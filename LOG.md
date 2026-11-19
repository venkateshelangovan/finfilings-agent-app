# LOG

What was done, numbers obtained, what failed. Newest first.

## 2026-11-19: Stage 2.1 (HTML to clean text)
- Stage 1 done: 6 filings downloaded, hashes in manifest, `companies.yaml` marked `verified: true`.
- Added `ingest/parse.py`: drops scripts, hidden XBRL header and display:none blocks; keeps tables as `[TABLE]` row blocks; removes page numbers and repeated "Table of Contents" lines.
- 3 tests on a synthetic HTML fixture (10 total pass). **Not run on real filings** (no EDGAR access here). Your run: `make text`, paste the output lines.

## 2026-11-19: Stage 1.2 (download + hashes)
- Added `ingest/download.py`: reads manifest, downloads missing files to `data/raw/<TICKER>/`, writes SHA-256 back, re-verifies. Skips files that already match (idempotent).
- 2 new tests (hash, verify). **Not run against real EDGAR**; your run: `make manifest` then `make data`.

## 2026-11-19: Stage 1.1 (list filings, no download yet)
- Added `ingest/edgar.py` (submissions API client, 10-K picker, fair-access sleep + User-Agent) and `ingest/list_filings.py` (writes `data/manifest.csv` with blank sha256).
- Unit tests use a fake submissions JSON; no network in CI. 5 tests pass in sandbox.
- **Not run against real EDGAR** (sandbox has no access). Your run: `make manifest`, then paste the output here.

## 2026-11-19: Stage 0 (scope, setup, decisions)
- Created repo layout, `pyproject.toml` (uv), Makefile, ruff, pytest, pre-commit (incl. gitleaks), CI workflow, `.env.example`, MIT license.
- Added typed config loader (`src/finfilings/config.py`) with tests; `configs/*.yaml` with first values.
- Verified in sandbox: `ruff check`, `ruff format --check`, `pytest` pass.
- **Not yet verified on your machine:** `make setup`, pre-commit hooks, GitHub Actions run. Report results here.
- Known gaps: `uv.lock` is generated on your first `make setup`; please commit it. CIKs and fiscal years unverified (Stage 1).
