"""Step 2.2: split each clean text file into 10-K Items and write data/processed/sections.jsonl.

How headings are found (from the real filings we inspected):
- The table of contents lists every Item as a table row, so those lines contain ' | '. Skip them.
- Body headings are short lines such as 'ITEM 1A. RISK FACTORS' or 'Item 1A. Risk Factors'.
- A section runs from its heading to the next Item heading of any kind.
Run:  uv run python -m finfilings.ingest.sections
"""

from __future__ import annotations

import json
import re

from finfilings.config import REPO_ROOT
from finfilings.ingest.download import read_manifest
from finfilings.ingest.parse import TEXT_DIR

SECTIONS_FILE = REPO_ROOT / "data" / "processed" / "sections.jsonl"
# Items we keep. 15 is kept because some filers (PayPal) put the financial statements there.
KEEP = ["1", "1A", "7", "7A", "8", "15"]
HEADING = re.compile(r"^item\s+(\d{1,2}[A-C]?)\s*\.?(\s.*)?$", re.I)
MAX_HEADING_LEN = 200


def find_headings(lines: list[str]) -> list[tuple[int, str]]:
    """(line_index, item) for each body heading, in document order."""
    found = []
    for i, line in enumerate(lines):
        if " | " in line or len(line) > MAX_HEADING_LEN:
            continue
        m = HEADING.match(line.strip())
        if m:
            found.append((i, m.group(1).upper()))
    return found


def split_sections(text: str) -> dict[str, dict]:
    """Return {item: {start_line, end_line, text}} for the Items in KEEP."""
    lines = text.splitlines()
    headings = find_headings(lines)
    out = {}
    for n, (start, item) in enumerate(headings):
        if item not in KEEP or item in out:
            continue  # keep the first body heading per item
        end = headings[n + 1][0] if n + 1 < len(headings) else len(lines)
        out[item] = {
            "start_line": start + 1,
            "end_line": end,
            "text": "\n".join(lines[start:end]).strip(),
        }
    return out


def main() -> None:
    n = 0
    with open(SECTIONS_FILE, "w", encoding="utf-8") as f:
        for row in read_manifest():
            path = TEXT_DIR / f"{row['ticker']}_{row['fiscal_year']}.txt"
            sections = split_sections(path.read_text(encoding="utf-8"))
            summary = []
            for item in KEEP:
                s = sections.get(item)
                if s is None:
                    summary.append(f"{item}: MISSING")
                    continue
                rec = {
                    "ticker": row["ticker"],
                    "year": int(row["fiscal_year"]),
                    "section": item,
                    "start_line": s["start_line"],
                    "end_line": s["end_line"],
                    "n_chars": len(s["text"]),
                    "text": s["text"],
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                summary.append(f"{item}: {len(s['text']):,}")
                n += 1
            print(f"{row['ticker']}_{row['fiscal_year']}  " + "  ".join(summary))
    print(f"Wrote {n} sections to {SECTIONS_FILE}")


if __name__ == "__main__":
    main()
