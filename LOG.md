# LOG

What was done, numbers obtained, what failed. Newest first.

## 2026-11-19: Stage 3.1 (chunking)
- Added `index/chunk.py` + `make chunks`, settings in `configs/chunking.yaml` (600 tokens target, 800 cap, 12% overlap). Each chunk keeps ticker, year, section, kind (text/table), char_span inside its section, an id like `PYPL-2025-1A-0007` and an `embed_text` with a `[PYPL 10-K 2025 | Item 1A]` header. 6 tests (29 total).
- **Your run:** `make chunks`, paste the printed stats. I am looking at chunk count, token spread, and the share of tiny chunks.

## 2026-11-19: Stage 2.4 (QA checks)
- Added `ingest/qa.py` + `make qa`: required Items present (1, 1A, 7), each section starts with its own heading, minimum sizes, no section >10x its peers' median, and Item 8 or 15 is large (PayPal keeps financials in 15). 6 tests (23 total).
- **Your run:** `make qa`, then `uv run python -m finfilings.ingest.qa --sample` and read the 5 sections. Paste the QA result and tell me if any sample looks wrong.

## 2026-11-19: Stage 2.3b (provision metric)
- Tag finder showed all candidate tags are standard us-gaap, not extensions. `show` returned **no entries for our accession numbers** for PYPL (ProvisionForLoanLeaseAndOtherLosses) and COIN (ProvisionForDoubtfulAccounts), so those companies' provision line is not available via companyfacts (D-013). Affirm tag `ProvisionForLoanLossesExpensed` added.
- **Your run:** `make facts`; expect AFRM 7/7, PYPL and COIN 6/7.

## 2026-11-19: Stage 2.3 (XBRL facts)
- **Real results:** `make sections` found all 6 Items in all 6 filings (PYPL Item 8 = 260-301 chars, a pointer; its statements are in Item 15 at ~216k chars). `make facts`: 6/7 metrics for every filing; `provision_for_credit_losses` missing everywhere, probably because it is tagged in a company extension namespace (my code only read us-gaap). Added `find` helper: `uv run python -m finfilings.ingest.xbrl find provision`.
- Added `ingest/xbrl.py`: calls SEC `companyfacts`, keeps only values from each manifest filing (matched by accession number), at that filing's fiscal year end, full-year duration for flow items. Tries several tags per metric and records which one matched (`source_tag`).
- 2 tests with a fake companyfacts JSON (15 pass total). **Not run on real SEC data.**
- **Your run:** `make facts`, paste the output. Any `missing:` metric means that company uses a tag I did not list; we add it from the real data.

## 2026-11-19: Stage 2.2 (sections)
- Real output of `make text`: PYPL 465-475k chars (209-213 tables), AFRM 549-558k (113), COIN 652-683k (95).
- Findings from the Item-heading grep: ToC rows contain ' | ' and page numbers; body headings are ALL CAPS (`ITEM 1A. RISK FACTORS`) except AFRM Item 1A (`Item 1A. Risk Factors`). **PayPal's Item 8 is a 8-line pointer; its financial statements are under Item 15**, so Item 15 is kept too.
- Found bug: table cells split words across inline spans (`Disagreements w ith`). Fixed by joining cell text without a separator; test added.
- `ingest/sections.py`: skips ' | ' lines, first body heading per Item, section ends at next heading. 12 tests pass. Terminal `ΓÇÖ` seen in cmd is only console display of UTF-8 (not a file bug).
- **Your run:** `make text` (re-run for the fix) then `make sections`, paste output.

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
