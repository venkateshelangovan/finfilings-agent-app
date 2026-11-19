from finfilings.ingest.download import raw_path, sha256_file, verify

ROW = {"ticker": "PYPL", "fiscal_year": "2024", "sha256": ""}


def test_sha256_known_value(tmp_path):
    f = tmp_path / "a.txt"
    f.write_bytes(b"abc")
    assert sha256_file(f) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_verify_detects_missing_mismatch_and_ok(tmp_path):
    assert verify([dict(ROW)], tmp_path) == ["missing file: PYPL_2024_10-K.htm"]
    p = raw_path(ROW, tmp_path)
    p.parent.mkdir(parents=True)
    p.write_bytes(b"abc")
    assert verify([dict(ROW)], tmp_path) == ["hash mismatch: PYPL_2024_10-K.htm"]
    ok = dict(ROW, sha256=sha256_file(p))
    assert verify([ok], tmp_path) == []
