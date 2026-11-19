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

## D-010: tables kept as [TABLE] row blocks, one line per row (provisional, Stage 2)
- **Why:** flattening a table into prose scrambles numbers from different columns. Keeping rows with ' | ' separators preserves which number belongs to which label, and the markers let Stage 3 chunk tables on their own.
- **Known limit:** column headers (years) can sit in separate rows; judged on real output before changing.

## D-011: keep Items 1, 1A, 7, 7A, 8 and 15 (accepted, Stage 2)
- **Why:** the real PayPal filing puts the financial statements and notes under Item 15 (Item 8 only points to it). Keeping 15 for every company is simpler than per-company rules; for AFRM and COIN it is mostly exhibits and is small. Items 2-6, 9-14 and 16 are not needed for our question types.
- **Boundary rule:** a section ends at the next Item heading of any kind, so Item 1A ends at 1B even though 1B is not kept.

## D-012: facts stored as CSV, not parquet; match by accession number (provisional, Stage 2)
- **Why CSV:** the table is tiny (about 40 rows). Parquet would add pandas and pyarrow for no benefit. Can switch later without changing callers.
- **Why accession:** a 10-K also contains prior-year numbers and later filings restate them. Taking only values tagged with the filing's own accession, at its own period end, makes each number traceable to one document, which is what citations need.
- **Why several tags per metric:** companies tag the same concept differently (e.g. revenue). The tag used is stored in `source_tag`.

## D-013: provision for credit losses is not in XBRL companyfacts for PYPL and COIN; answer from text (accepted, Stage 2)
- **Evidence:** `xbrl show` for the tags PayPal and Coinbase could use returned nothing for our filings' accession numbers. The tags exist only in other filings. Companyfacts exposes standard taxonomies only, and a company's own extension tags (e.g. PayPal's "transaction and credit losses" line) are not included.
- **Decision:** keep `provision_for_credit_losses` as an optional metric. Affirm has it (`ProvisionForLoanLossesExpensed`). For PYPL and COIN the facts tool must return "not available" and the agent falls back to the MD&A text, which is a real case for the agentic fallback in Stage 8.
- **Not done:** parsing the numbers out of income-statement tables to fill the gap. Revisit only if numeric questions on these two fail.

## D-014: chunk size measured by estimated tokens (chars / 4), cut at line or sentence ends (provisional, Stage 3)
- **Why estimate:** a real tokenizer needs a model download and makes tests and CI depend on the network. chars/4 is the usual rule of thumb for English; errors only blur the size by a few percent, which is far below the effect of the 400-800 token range we ablate in Stage 7.
- **Why cut at natural boundaries:** a chunk that ends mid-sentence is harder to retrieve and to quote. Cuts prefer a line break, then a sentence end, then a space.
- **Why overlap = 12% of the chunk:** text near a cut would otherwise lose context from its neighbour. Overlapping chunks are also verbatim substrings of the section, so `char_span` always points at the exact source passage.
- **Tables:** one chunk per table; a table over the 800-token cap is split by rows, each piece re-wrapped in [TABLE] markers.
- **Known weakness:** column headers (years) may be in a different row or chunk than the numbers; judged on retrieval results in Stage 7.

## D-015: merge chunks under 100 estimated tokens into a neighbour (provisional, Stage 3)
- **Evidence:** first real run gave 2,558 chunks, median 388 tokens (target 600) and **23% of chunks under 100 tokens**, mostly from short prose lines next to tables, one-row tables and the leftover tail after an overlap.
- **Decision:** merge a tiny chunk with its neighbour when the result stays under the 800-token cap and both are verbatim text (so `char_span` still equals the exact source text). Setting `min_chunk_tokens: 0` turns it off, so Stage 7 can ablate it.
- **Why it matters:** a 40-token chunk matches many queries weakly and competes with real content in top-k.
