# FinFilings Agent

**Agentic RAG with evaluation over SEC 10-K filings of fintech companies.**

Cited, refusal-aware Q&A over annual reports, plus a hand-verified benchmark and an ablation study
from plain RAG to a LangGraph agent, measuring accuracy, faithfulness, latency and cost.

> **Not financial advice.** Research project on public SEC filings only. No PII, no market data.

![status](https://img.shields.io/badge/status-Stage%203%20in%20progress-blue)

## Research question

Does an agentic RAG pipeline beat plain RAG on financial-filing questions, by how much, on which
question types, and at what cost in latency and money?

## Status

| Stage | What | State |
|---|---|---|
| 0 | Scope, repo setup, decisions | done |
| 1 | Data acquisition (EDGAR) | done (6 filings, hashes in manifest) |
| 2 | Parsing and cleaning | done |
| 3 | Chunking and indexing | **in progress**: 3.1 chunking (done); 3.2 embeddings + dense index (this PR); 3.3 BM25 next |
| 4 | Baseline RAG | - |
| 5 | Evaluation dataset | - |
| 6 | Evaluation harness | - |
| 7 | Retrieval improvements | - |
| 8 | Agent (LangGraph) | - |
| 9 | Experiments and analysis | - |
| 10-13 | Hardening, demo, docs, packaging | - |

Full plan: Project brief kept outside the repo. Decisions: [DECISIONS.md](DECISIONS.md). Run log: [LOG.md](LOG.md).

## Quickstart

Prerequisites: Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/venkateshelangovan/finfilings-agent-app.git
cd finfilings-agent-app
cp .env.example .env     # fill in later stages; never commit .env
make setup               # install deps (incl. embedding stack, ~1 GB) + git hooks
make check               # ruff + pytest (what CI runs)
```

Stage 1.1: put your name and email in `.env` as `SEC_USER_AGENT`, then `make manifest` (or `uv run python -m finfilings.ingest.list_filings`).

Stage 1.2: `make data` downloads the filings into `data/raw/` (gitignored) and fills the hashes in `data/manifest.csv`.

Stage 2.1: `make text` converts raw HTML into clean text in `data/processed/text/` (gitignored).

Stage 2.2: `make sections` splits the text into Items 1, 1A, 7, 7A, 8, 15 and writes `data/processed/sections.jsonl`.

Stage 2.3: `make facts` pulls exact numbers (revenue, net income, provision, assets, ...) from SEC XBRL into `data/processed/facts.csv`.

Stage 2.4: `make qa` checks the parsed sections and fails if anything looks wrong; `uv run python -m finfilings.ingest.qa --sample` prints 5 sections to read by eye.

Stage 3.1: `make chunks` writes `data/processed/chunks.jsonl` (section-aware chunks, tables kept separate, char spans for citations).

Stage 3.2: `make index` embeds the chunks (downloads `bge-small-en-v1.5`, ~130 MB, first time only). Try it:
`uv run python -m finfilings.retrieval.dense "PayPal fraud losses" --ticker PYPL -k 5`

Later targets (`make index`, `make eval`) are stubs until their stages land.

## Scope

- **v1 companies (MVP):** PYPL, AFRM, COIN, two fiscal years each. Expansion to V, MA, HOOD, SOFI, UPST later.
- **In scope:** text sections plus an XBRL numbers tool, hybrid retrieval, reranking, LangGraph agent, evaluation harness, ablations.
- **Out of scope (v1):** market data, news, earnings calls, fine-tuning, auth/payments.

## Repo map

```
configs/        YAML settings (companies, chunking, retrieval, agent, eval)
data/           manifest.csv + eval set are committed; raw/processed are gitignored
src/finfilings/ ingest, index, retrieval, llm, baseline, agent, eval, serve
tests/          pytest (no network, no paid LLM calls in CI)
docs/           report, results, error analysis (later stages)
```

## Responsible use

Public data only (SEC EDGAR). Outputs may be wrong; always check the cited source passage.

## License

MIT, see [LICENSE](LICENSE).
