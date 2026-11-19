# LOG

What was done, numbers obtained, what failed. Newest first.

## 2026-11-19: Stage 0 (scope, setup, decisions)
- Created repo layout, `pyproject.toml` (uv), Makefile, ruff, pytest, pre-commit (incl. gitleaks), CI workflow, `.env.example`, MIT license.
- Added typed config loader (`src/finfilings/config.py`) with tests; `configs/*.yaml` with first values.
- Verified in sandbox: `ruff check`, `ruff format --check`, `pytest` pass.
- **Not yet verified on your machine:** `make setup`, pre-commit hooks, GitHub Actions run. Report results here.
- Known gaps: `uv.lock` is generated on your first `make setup`; please commit it. CIKs and fiscal years unverified (Stage 1).
