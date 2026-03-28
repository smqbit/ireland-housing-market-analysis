setup:
	uv sync

run:
	uv run python main.py

lint:
	uv run ruff check .

format:
	uv run ruff format .

fix:
	uv run ruff check . --fix

typecheck:
	uv run mypy .

clean:
	rm -rf .venv __pycache__ .mypy_cache .ruff_cache