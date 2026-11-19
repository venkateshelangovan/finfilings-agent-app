"""Step 1.2: download every filing listed in data/manifest.csv and record its SHA-256.

Idempotent: a file that already exists and matches its manifest hash is skipped.
Run:  uv run python -m finfilings.ingest.download
"""

from __future__ import annotations

import csv
import hashlib
import time
from pathlib import Path

import requests

from finfilings.config import REPO_ROOT
from finfilings.ingest.edgar import MIN_SECONDS_BETWEEN_REQUESTS, get_user_agent

MANIFEST = REPO_ROOT / "data" / "manifest.csv"
RAW_DIR = REPO_ROOT / "data" / "raw"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def raw_path(row: dict, raw_dir: Path = RAW_DIR) -> Path:
    return raw_dir / row["ticker"] / f"{row['ticker']}_{row['fiscal_year']}_10-K.htm"


def read_manifest(path: Path = MANIFEST) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def write_manifest(rows: list[dict], path: Path = MANIFEST) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def verify(rows: list[dict], raw_dir: Path = RAW_DIR) -> list[str]:
    """Return a list of problems; empty means every row has a file with a matching hash."""
    problems = []
    for row in rows:
        p = raw_path(row, raw_dir)
        if not p.exists():
            problems.append(f"missing file: {p.name}")
        elif sha256_file(p) != row["sha256"]:
            problems.append(f"hash mismatch: {p.name}")
    return problems


def main() -> None:
    rows = read_manifest()
    if not rows:
        raise SystemExit("manifest.csv is empty. Run `make manifest` first.")
    ua = get_user_agent()
    for row in rows:
        p = raw_path(row)
        if p.exists() and row["sha256"] and sha256_file(p) == row["sha256"]:
            print(f"skip   {p.name}")
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        time.sleep(MIN_SECONDS_BETWEEN_REQUESTS)
        resp = requests.get(row["url"], headers={"User-Agent": ua}, timeout=60)
        resp.raise_for_status()
        p.write_bytes(resp.content)
        row["sha256"] = sha256_file(p)
        print(f"saved  {p.name}  {len(resp.content) / 1e6:.1f} MB")
    write_manifest(rows)
    problems = verify(rows)
    print("OK: all files present and hashes match" if not problems else f"PROBLEMS: {problems}")


if __name__ == "__main__":
    main()
