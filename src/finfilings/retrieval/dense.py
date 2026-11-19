"""Dense retrieval: cosine similarity between a query vector and every chunk vector.

CLI check:  uv run python -m finfilings.retrieval.dense "PayPal fraud losses" --ticker PYPL -k 5
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from finfilings.index.chunk import CHUNKS_FILE
from finfilings.index.embed import EMBEDDINGS_FILE, META_FILE, embed_texts, file_sha256


class DenseIndex:
    def __init__(self, vectors: np.ndarray, chunks: list[dict], model_name: str):
        if len(vectors) != len(chunks):
            raise ValueError("vectors and chunks must have the same length")
        self.vectors, self.chunks, self.model_name = vectors, chunks, model_name

    @classmethod
    def load(cls) -> DenseIndex:
        meta = json.loads(META_FILE.read_text(encoding="utf-8"))
        if meta["chunks_sha256"] != file_sha256(CHUNKS_FILE):
            raise RuntimeError("chunks.jsonl changed since the index was built: run `make index`")
        with open(CHUNKS_FILE, encoding="utf-8") as f:
            chunks = [json.loads(line) for line in f]
        return cls(np.load(EMBEDDINGS_FILE), chunks, meta["model"])

    def search_vector(
        self,
        query_vec: np.ndarray,
        k: int = 8,
        ticker: str | None = None,
        year: int | None = None,
        section: str | None = None,
    ) -> list[tuple[float, dict]]:
        scores = self.vectors @ query_vec  # both normalised, so dot product = cosine
        mask = np.ones(len(self.chunks), dtype=bool)
        for field, value in (("ticker", ticker), ("year", year), ("section", section)):
            if value is not None:
                mask &= np.array([c[field] == value for c in self.chunks])
        scores = np.where(mask, scores, -np.inf)
        top = np.argsort(-scores)[:k]
        return [(float(scores[i]), self.chunks[i]) for i in top if np.isfinite(scores[i])]

    def search(self, query: str, **kwargs) -> list[tuple[float, dict]]:
        vec = embed_texts([query], self.model_name, is_query=True)[0]
        return self.search_vector(vec, **kwargs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--ticker")
    ap.add_argument("--year", type=int)
    ap.add_argument("--section")
    a = ap.parse_args()
    for score, c in DenseIndex.load().search(
        a.query,
        k=a.k,
        ticker=a.ticker.upper() if a.ticker else None,
        year=a.year,
        section=a.section,
    ):
        preview = c["text"][:110].replace("\n", " ")
        print(f"{score:.3f}  {c['chunk_id']} [{c['kind']}]  {preview}")


if __name__ == "__main__":
    main()
