.PHONY: setup lint format test check clean manifest data text sections facts index eval

setup:  ## install dependencies and git hooks
	uv sync
	uv run pre-commit install

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest -m "not network and not llm"

check: lint test  ## what CI runs

clean:
	rm -rf .pytest_cache .ruff_cache **/__pycache__

manifest:  ## Stage 1.1: list 10-Ks on EDGAR, write data/manifest.csv
	uv run python -m finfilings.ingest.list_filings

# Pipeline targets are filled in by later stages.
data:  ## Stage 1.2: download filings listed in manifest, record hashes
	uv run python -m finfilings.ingest.download
text:  ## Stage 2.1: raw HTML -> clean text in data/processed/text/
	uv run python -m finfilings.ingest.parse

sections:  ## Stage 2.2: clean text -> data/processed/sections.jsonl
	uv run python -m finfilings.ingest.sections

facts:  ## Stage 2.3: XBRL numbers -> data/processed/facts.csv
	uv run python -m finfilings.ingest.xbrl

index:
	@echo "Stage 3: not implemented yet"
eval:
	@echo "Stage 6: not implemented yet"
