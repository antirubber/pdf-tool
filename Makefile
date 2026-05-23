.PHONY: reinstall test lint

reinstall:
	uv cache clean pdf-tool
	uv tool install --force --reinstall .

test:
	uv run pytest

lint:
	ruff check pdf_tool tests
