# FinFilings Agent

**Agentic RAG with evaluation over SEC 10-K filings of fintech companies.**

Cited, refusal-aware Q&A over annual reports, plus a hand-verified benchmark and an ablation study
from plain RAG to a LangGraph agent, measuring accuracy, faithfulness, latency and cost.

> **Not financial advice.** Research project on public SEC filings only. No PII, no market data.

![status](https://img.shields.io/badge/status-Stage%200%20done-blue)

## Research question

Does an agentic RAG pipeline beat plain RAG on financial-filing questions, by how much, on which
question types, and at what cost in latency and money?

## Status

| Stage | What | State |
|---|---|---|
| 0 | Scope, repo setup, decisions | **done (pending your local check)** |
| 1 | Data acquisition (EDGAR) | next |
| 2 | Parsing and cleaning | - |
| 3 | Chunking and indexing | - |
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
make setup               # install deps + git hooks
make check               # ruff + pytest (what CI runs)
```

Later targets (`make data`, `make index`, `make eval`) are stubs until their stages land.

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
