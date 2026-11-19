"""Step 3.2: embed every chunk and save the dense index to data/processed/dense/.

The index is just a matrix (one normalised vector per chunk) plus a small metadata file.
With ~2,000 chunks, exact search with a dot product is instant, so no vector database is needed
(D-016). The metadata stores a hash of chunks.jsonl so a stale index is detected, not trusted.
Run:  uv run python -m finfilings.index.embed      (needs the 'ml' dependency group)
"""

from __future__ import annotations

import hashlib
import json
import time

import numpy as np

from finfilings.config import REPO_ROOT, load_chunking
from finfilings.index.chunk import CHUNKS_FILE

DENSE_DIR = REPO_ROOT / "data" / "processed" / "dense"
EMBEDDINGS_FILE = DENSE_DIR / "embeddings.npy"
META_FILE = DENSE_DIR / "meta.json"
# BGE models were trained to see this prefix on SEARCH QUERIES (not on documents).
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

_model_cache: dict[str, object] = {}


def file_sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def embed_texts(
    texts: list[str], model_name: str, is_query: bool = False, batch_size: int = 32
) -> np.ndarray:
    """Return an (n, dim) float32 matrix of L2-normalised embeddings."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("Embedding needs the 'ml' group: run `uv sync --all-groups`") from exc
    if model_name not in _model_cache:
        _model_cache[model_name] = SentenceTransformer(model_name)
    model = _model_cache[model_name]
    if is_query and "bge" in model_name.lower():
        texts = [BGE_QUERY_PREFIX + t for t in texts]
    vecs = model.encode(  # type: ignore[attr-defined]
        texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=len(texts) > 100
    )
    return np.asarray(vecs, dtype=np.float32)


def build() -> None:
    model_name = load_chunking().embedding_model
    with open(CHUNKS_FILE, encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]
    t0 = time.time()
    vecs = embed_texts([c["embed_text"] for c in chunks], model_name)
    DENSE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_FILE, vecs)
    META_FILE.write_text(
        json.dumps(
            {
                "model": model_name,
                "n_chunks": len(chunks),
                "dim": int(vecs.shape[1]),
                "chunk_ids": [c["chunk_id"] for c in chunks],
                "chunks_sha256": file_sha256(CHUNKS_FILE),
            }
        ),
        encoding="utf-8",
    )
    secs = time.time() - t0
    print(f"embedded {len(chunks):,} chunks with {model_name}, shape {vecs.shape}, {secs:.0f}s")


if __name__ == "__main__":
    build()
