"""Step 2.4: quality checks on data/processed/sections.jsonl.

Fails loudly (exit code 1) if parsing broke, so bad data never reaches the index.
Run:  uv run python -m finfilings.ingest.qa            (checks)
      uv run python -m finfilings.ingest.qa --sample   (print 5 sections to read by eye)
"""

from __future__ import annotations

import json
import random
import statistics
import sys
from collections import defaultdict

from finfilings.ingest.sections import HEADING, SECTIONS_FILE

REQUIRED = ["1", "1A", "7"]
MIN_CHARS = {"1": 5_000, "1A": 10_000, "7": 10_000, "7A": 1_000}
MAX_RATIO_TO_MEDIAN = 10
RATIO_CHECKED = ["1", "1A", "7", "7A"]
# Some filers (PayPal) put the financial statements in Item 15, so either 8 or 15 must be big.
FINANCIALS_MIN_CHARS = 50_000


def check_sections(records: list[dict]) -> list[str]:
    problems = []
    by_filing: dict[tuple, dict[str, dict]] = defaultdict(dict)
    by_item: dict[str, list[int]] = defaultdict(list)
    for r in records:
        by_filing[(r["ticker"], r["year"])][r["section"]] = r
        by_item[r["section"]].append(r["n_chars"])

    medians = {item: statistics.median(v) for item, v in by_item.items()}
    for (ticker, year), secs in sorted(by_filing.items()):
        name = f"{ticker}_{year}"
        for item in REQUIRED:
            if item not in secs:
                problems.append(f"{name}: missing Item {item}")
        for item, r in secs.items():
            first_line = r["text"].splitlines()[0]
            m = HEADING.match(first_line)
            if not m or m.group(1).upper() != item:
                problems.append(f"{name}: Item {item} does not start with its heading")
            if r["n_chars"] < MIN_CHARS.get(item, 1):
                problems.append(f"{name}: Item {item} too short ({r['n_chars']} chars)")
            if item in RATIO_CHECKED and r["n_chars"] > MAX_RATIO_TO_MEDIAN * medians[item]:
                problems.append(f"{name}: Item {item} is >{MAX_RATIO_TO_MEDIAN}x its peers' median")
        financials = max(secs.get("8", {}).get("n_chars", 0), secs.get("15", {}).get("n_chars", 0))
        if financials < FINANCIALS_MIN_CHARS:
            problems.append(f"{name}: no large financial-statements section (Item 8 or 15)")
    return problems


def load() -> list[dict]:
    with open(SECTIONS_FILE, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def sample(records: list[dict], n: int = 5, seed: int = 42) -> None:
    keyed = [r for r in records if r["section"] in {"1", "1A", "7", "7A"}]
    for r in random.Random(seed).sample(keyed, n):
        print(f"\n===== {r['ticker']} {r['year']} Item {r['section']} ({r['n_chars']:,} chars)")
        print(r["text"][:600])
        print("   [...]")
        print(r["text"][-300:])


def main() -> None:
    records = load()
    if "--sample" in sys.argv:
        sample(records)
        return
    problems = check_sections(records)
    filings = len({(r["ticker"], r["year"]) for r in records})
    print(f"{len(records)} sections across {filings} filings")
    if problems:
        print("QA FAILED:")
        for p in problems:
            print(f"  - {p}")
        raise SystemExit(1)
    print("QA PASSED")


if __name__ == "__main__":
    main()
