# DECISIONS

Every choice and why. Add an entry whenever you pick between options. Status: `accepted`, `provisional`, `reversed`.

## D-001: Python 3.11+, `uv`, ruff, pytest, pre-commit (accepted, Stage 0)
- **Why:** `uv` gives fast, lockfile-based installs (`uv.lock`), which is what makes "a stranger can reproduce" true.
  ruff replaces black+flake8+isort with one tool. pytest is the standard.
- **Alternatives:** poetry, conda+pip.
- **Note:** `requires-python` is `>=3.11,<3.14` so ML libraries have wheels.

## D-002: Minimal dependencies per stage (accepted, Stage 0)
- **Why:** each stage adds only what it uses, so every dependency has a reason in git history and CI stays fast.

## D-003: LLM provider = Anthropic by default, provider-agnostic client (provisional, Stage 0)
- **Why:** chosen as a default on your behalf; the client wrapper in Stage 4 hides the provider so you can switch via `LLM_PROVIDER`.
- **Open:** confirm provider and set a monthly spend limit on the account before Stage 4.
- **Rule:** cheap model for development, strong model for final runs; a *different* model for judging than for answering.

## D-004: MVP = 3 companies (PYPL, AFRM, COIN), 2 fiscal years each (provisional, Stage 0)
- **Why:** parsing varies per company and is the biggest time risk. Three companies cover payments, lending and crypto, which gives varied filing structure for the parser without 8x the work. Expand after the MVP checkpoint.
- **Provisional because:** CIKs and fiscal years in `configs/companies.yaml` are unverified. Stage 1 verifies them against EDGAR (`verified: true`) before any download. AFRM's fiscal year ends June 30.

## D-005: Workflow = one branch and PR per stage; first scaffold direct to `main` (accepted, Stage 0)
- **Why:** `main` always holds code you have run locally. PR descriptions double as stage summaries.

## D-006: Repo is public from the start (provisional, Stage 0)
- **Why:** all data is public SEC data and secrets are excluded (`.env` ignored, gitleaks hook). Public from day one also shows commit history as proof of work.
- **Rule:** never commit keys; `SEC_USER_AGENT` (your email) lives only in `.env`.

## D-007: Tests and CI never call the network or a paid LLM (accepted, Stage 0)
- **Why:** deterministic, free, safe. Tests needing either are marked `network` / `llm` and excluded in CI.

## D-008: fiscal_year = year of the fiscal period end date (accepted, Stage 1)
- **Why:** EDGAR gives `reportDate` (period end). PayPal and Coinbase end Dec 31, so FY2024 = period ending 2024-12-31. Affirm ends June 30, so FY2025 = period ending 2025-06-30. One simple rule, no company-specific exceptions.
- **Risk:** companies with 52/53-week years ending in early January would shift a year. None in scope.

## D-009: original 10-K only, skip 10-K/A amendments (accepted, Stage 1)
- **Why:** amendments are often partial (e.g. only Part III) and would create duplicate or incomplete documents. Revisit if a company's original is missing.
