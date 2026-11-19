import numpy as np
import pytest

from finfilings.retrieval.dense import DenseIndex


def make_index():
    chunks = [
        {"chunk_id": "A-2024-1-0000", "ticker": "AAA", "year": 2024, "section": "1"},
        {"chunk_id": "A-2025-1A-0000", "ticker": "AAA", "year": 2025, "section": "1A"},
        {"chunk_id": "B-2025-1A-0000", "ticker": "BBB", "year": 2025, "section": "1A"},
    ]
    vecs = np.array([[1, 0], [0.8, 0.6], [0, 1]], dtype=np.float32)  # already unit length
    return DenseIndex(vecs, chunks, "fake")


def test_ranks_by_cosine():
    hits = make_index().search_vector(np.array([1, 0], dtype=np.float32), k=3)
    assert [c["chunk_id"] for _, c in hits] == ["A-2024-1-0000", "A-2025-1A-0000", "B-2025-1A-0000"]
    assert hits[0][0] == pytest.approx(1.0)


def test_metadata_filters_apply_before_ranking():
    q = np.array([1, 0], dtype=np.float32)
    hits = make_index().search_vector(q, k=3, ticker="BBB")
    assert [c["chunk_id"] for _, c in hits] == ["B-2025-1A-0000"]
    hits = make_index().search_vector(q, k=3, ticker="AAA", year=2025)
    assert [c["chunk_id"] for _, c in hits] == ["A-2025-1A-0000"]
    assert make_index().search_vector(q, ticker="ZZZ") == []


def test_length_mismatch_rejected():
    with pytest.raises(ValueError):
        DenseIndex(np.zeros((2, 2), dtype=np.float32), [{}], "fake")
