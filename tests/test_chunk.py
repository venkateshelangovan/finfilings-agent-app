import re

from finfilings.config import ChunkingConfig
from finfilings.index.chunk import chunk_section

CFG = ChunkingConfig(chunk_tokens=60, max_chunk_tokens=80, chars_per_token=4, overlap_ratio=0.15)
# target = 240 chars, overlap = 36 chars, max table chunk = 320 chars

SENT = "Fraud losses are a growing risk for our business. "
PROSE = "ITEM 1A. RISK FACTORS\n" + (SENT * 6 + "\n") * 8
TABLE = "[TABLE]\n" + "\n".join(f"Row {i} | {i * 100}" for i in range(60)) + "\n[/TABLE]"


def run(text):
    return chunk_section(text, "PYPL", 2025, "1A", CFG)


def test_prose_chunks_respect_size_and_cover_everything():
    chunks = run(PROSE)
    assert len(chunks) > 3
    assert all(len(c["text"]) <= 240 for c in chunks)
    covered = set()
    for c in chunks:
        covered.update(range(*c["char_span"]))
    missing = [i for i, ch in enumerate(PROSE) if not ch.isspace() and i not in covered]
    assert missing == []


def test_span_matches_text_and_chunks_overlap():
    chunks = run(PROSE)
    for c in chunks:
        s, e = c["char_span"]
        assert PROSE[s:e] == c["text"]
    assert any(
        a["char_span"][1] > b["char_span"][0] for a, b in zip(chunks, chunks[1:], strict=False)
    )


def test_no_chunk_starts_mid_word():
    for c in run(PROSE):
        s = c["char_span"][0]
        assert s == 0 or PROSE[s - 1].isspace()


def test_table_is_its_own_chunk_and_large_table_is_split():
    chunks = run(PROSE + TABLE + "\nAfter the table we continue.\n")
    tables = [c for c in chunks if c["kind"] == "table"]
    assert len(tables) >= 2
    assert all(
        c["text"].startswith("[TABLE]\n") and c["text"].endswith("\n[/TABLE]") for c in tables
    )
    assert all(len(c["text"]) <= 320 for c in tables)
    all_rows = "\n".join(c["text"] for c in tables)
    assert all(f"Row {i} |" in all_rows for i in range(60))
    assert not any("[TABLE]" in c["text"] for c in chunks if c["kind"] == "text")


def test_ids_unique_and_header_added():
    chunks = run(PROSE)
    ids = [c["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids))
    assert re.fullmatch(r"PYPL-2025-1A-\d{4}", ids[0])
    assert chunks[0]["embed_text"].startswith("[PYPL 10-K 2025 | Item 1A] ")


def test_text_without_spaces_still_terminates():
    chunks = run("x" * 2000)
    assert len(chunks) >= 8
    assert all(len(c["text"]) <= 240 for c in chunks)
