"""Step 3.1: split each section into chunks and write data/processed/chunks.jsonl.

Rules (all values come from configs/chunking.yaml so they can be ablated later):
- Never cross a section boundary: each section is chunked on its own.
- Prose: ~chunk_tokens per chunk, cut at a line break or sentence end, with overlap_ratio overlap.
- Tables ([TABLE]...[/TABLE]) are separate chunks; very large tables are split by rows.
- Every chunk records its character span inside the section text, so a citation can be
  traced back to the exact source passage.
Run:  uv run python -m finfilings.index.chunk
"""

from __future__ import annotations

import json
import math
import re
import statistics

from finfilings.config import REPO_ROOT, ChunkingConfig, load_chunking
from finfilings.ingest.sections import SECTIONS_FILE

CHUNKS_FILE = REPO_ROOT / "data" / "processed" / "chunks.jsonl"
TABLE_RE = re.compile(r"\[TABLE\]\n.*?\n\[/TABLE\]", re.S)
SENTENCE_END = re.compile(r"[.!?]\s")


def _tighten(text: str, start: int, end: int) -> tuple[int, int]:
    """Shrink [start, end) so it has no leading/trailing whitespace."""
    raw = text[start:end]
    lead = len(raw) - len(raw.lstrip())
    return start + lead, start + lead + len(raw.strip())


def _prose_spans(text: str, a: int, b: int, target: int, overlap: int) -> list[tuple[int, int]]:
    spans = []
    start, min_len = a, target // 2
    while start < b:
        end = min(start + target, b)
        if end < b:
            lo = start + min_len
            cut = text.rfind("\n", lo, end)
            if cut != -1:
                end = cut
            else:
                ends = [m.end() for m in SENTENCE_END.finditer(text, lo, end)]
                if ends:
                    end = ends[-1]
                else:
                    sp = text.rfind(" ", lo, end)
                    end = sp if sp != -1 else end
        s, e = _tighten(text, start, end)
        if e > s:
            spans.append((s, e))
        if end >= b:
            break
        nxt = max(end - overlap, start + 1)
        while nxt < end and not text[nxt].isspace():  # do not start mid-word
            nxt += 1
        while nxt < end and text[nxt].isspace():
            nxt += 1
        start = nxt if nxt < end else end
    return spans


def _table_pieces(text: str, a: int, b: int, max_chars: int) -> list[tuple[int, int, str]]:
    """(start, end, chunk_text) for a table; split by rows only if it is too large."""
    whole = text[a:b]
    if len(whole) <= max_chars:
        return [(a, b, whole)]
    pieces, rows, pos = [], [], a + len("[TABLE]\n")
    for line in text[pos : b - len("\n[/TABLE]")].split("\n"):
        rows.append((pos, line))
        pos += len(line) + 1
    group: list[tuple[int, str]] = []
    size = 0
    for row in [*rows, None]:
        if row is None or (group and size + len(row[1]) + 1 > max_chars - 20):
            body = "\n".join(line for _, line in group)
            pieces.append(
                (group[0][0], group[-1][0] + len(group[-1][1]), f"[TABLE]\n{body}\n[/TABLE]")
            )
            group, size = [], 0
        if row is not None:
            group.append(row)
            size += len(row[1]) + 1
    return pieces


def _merge_small(text, raw, min_chars, max_chars):
    """Merge a chunk smaller than min_chars with its neighbour when the result still fits.

    Tiny chunks (a heading line, a one-row table, the tail left after an overlap) carry
    almost no meaning on their own and clutter the index. Only verbatim chunks are merged,
    so the merged chunk is still exactly text[start:end] and its char_span stays honest.
    """
    out: list[tuple[int, int, str, str, bool]] = []
    for item in raw:
        if out:
            ps, pe, pt, pk, pv = out[-1]
            s, e, t, k, v = item
            small = len(pt) < min_chars or len(t) < min_chars
            if small and pv and v and max(e, pe) - ps <= max_chars:
                kind = "table" if "table" in (pk, k) else "text"
                out[-1] = (ps, max(e, pe), text[ps : max(e, pe)], kind, True)
                continue
        out.append(item)
    return out


def chunk_section(
    text: str, ticker: str, year: int, section: str, cfg: ChunkingConfig
) -> list[dict]:
    target = int(cfg.chunk_tokens * cfg.chars_per_token)
    overlap = int(target * cfg.overlap_ratio)
    max_chars = int(cfg.max_chunk_tokens * cfg.chars_per_token)

    raw: list[tuple[int, int, str, str, bool]] = []  # start, end, text, kind, verbatim
    cursor = 0
    for m in [*TABLE_RE.finditer(text), None]:
        prose_end = m.start() if m else len(text)
        for s, e in _prose_spans(text, cursor, prose_end, target, overlap):
            raw.append((s, e, text[s:e], "text", True))
        if m:
            for s, e, t in _table_pieces(text, m.start(), m.end(), max_chars):
                raw.append((s, e, t, "table", t == text[s:e]))
            cursor = m.end()
    raw.sort(key=lambda r: r[0])
    raw = _merge_small(text, raw, int(cfg.min_chunk_tokens * cfg.chars_per_token), max_chars)

    chunks = []
    for i, (s, e, t, kind, _) in enumerate(raw):
        chunks.append(
            {
                "chunk_id": f"{ticker}-{year}-{section}-{i:04d}",
                "ticker": ticker,
                "year": year,
                "section": section,
                "kind": kind,
                "char_span": [s, e],
                "n_tokens_est": math.ceil(len(t) / cfg.chars_per_token),
                "text": t,
                "embed_text": f"[{ticker} 10-K {year} | Item {section}] {t}",
            }
        )
    return chunks


def main() -> None:
    cfg = load_chunking()
    all_chunks: list[dict] = []
    with open(SECTIONS_FILE, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            all_chunks.extend(chunk_section(r["text"], r["ticker"], r["year"], r["section"], cfg))
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    toks = sorted(c["n_tokens_est"] for c in all_chunks)
    q = lambda p: toks[min(len(toks) - 1, int(p * len(toks)))]  # noqa: E731
    tables = sum(c["kind"] == "table" for c in all_chunks)
    print(f"{len(all_chunks):,} chunks ({tables:,} table chunks) -> {CHUNKS_FILE}")
    print(
        f"est. tokens: min {toks[0]}, p10 {q(0.1)}, median {int(statistics.median(toks))}, "
        f"p90 {q(0.9)}, max {toks[-1]}"
    )
    tiny = [c for c in all_chunks if c["n_tokens_est"] < 100]
    print(f"chunks under 100 est. tokens: {len(tiny):,} ({len(tiny) / len(toks):.1%})")
    for kind in ("text", "table"):
        print(f"  tiny {kind}: {sum(c['kind'] == kind for c in tiny):,}")
    for c in tiny[:6]:
        print(f"  e.g. {c['chunk_id']} ({c['kind']}): {c['text'][:70]!r}")
    per_filing: dict[str, int] = {}
    for c in all_chunks:
        key = f"{c['ticker']}_{c['year']}"
        per_filing[key] = per_filing.get(key, 0) + 1
    print("per filing:", per_filing)


if __name__ == "__main__":
    main()
