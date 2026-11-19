.PHONY: setup lint format test check clean data index eval

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

# Pipeline targets are filled in by later stages.
data:
	@echo "Stage 1: not implemented yet"
index:
	@echo "Stage 3: not implemented yet"
eval:
	@echo "Stage 6: not implemented yet"
