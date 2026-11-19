"""Step 3.3: keyword (BM25) search over the same chunks as the dense index.

Dense vectors find chunks that mean the same thing; BM25 finds chunks that contain the same
words. Exact terms (a ticker, 'CECL', '0.93', a product name) are where BM25 beats embeddings,
so Stage 7 will fuse the two. The index is built in memory at load time (about a second for
~2,000 chunks), so it can never be stale.

CLI check:  uv run python -m finfilings.index.bm25 "transaction expense rate" --ticker PYPL -k 5
"""

from __future__ import annotations

import argparse
import json
import re

import numpy as np
from rank_bm25 import BM25Okapi

from finfilings.index.chunk import CHUNKS_FILE

# Keeps numbers like 1,234.5 or 0.93 and words like company's as single tokens.
TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.,'][a-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class BM25Index:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        # embed_text starts with '[PYPL 10-K 2025 | Item 1A]', so ticker and year are searchable.
        self.bm25 = BM25Okapi([tokenize(c["embed_text"]) for c in chunks])

    @classmethod
    def load(cls) -> BM25Index:
        with open(CHUNKS_FILE, encoding="utf-8") as f:
            return cls([json.loads(line) for line in f])

    def search(
        self,
        query: str,
        k: int = 8,
        ticker: str | None = None,
        year: int | None = None,
        section: str | None = None,
    ) -> list[tuple[float, dict]]:
        scores = np.asarray(self.bm25.get_scores(tokenize(query)), dtype=float)
        mask = np.ones(len(self.chunks), dtype=bool)
        for field, value in (("ticker", ticker), ("year", year), ("section", section)):
            if value is not None:
                mask &= np.array([c[field] == value for c in self.chunks])
        scores = np.where(mask & (scores > 0), scores, -np.inf)  # score 0 = no query word matched
        top = np.argsort(-scores)[:k]
        return [(float(scores[i]), self.chunks[i]) for i in top if np.isfinite(scores[i])]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--ticker")
    ap.add_argument("--year", type=int)
    ap.add_argument("--section")
    a = ap.parse_args()
    hits = BM25Index.load().search(
        a.query,
        k=a.k,
        ticker=a.ticker.upper() if a.ticker else None,
        year=a.year,
        section=a.section,
    )
    for score, c in hits:
        preview = c["text"][:110].replace("\n", " ")
        print(f"{score:.2f}  {c['chunk_id']} [{c['kind']}]  {preview}")


if __name__ == "__main__":
    main()
