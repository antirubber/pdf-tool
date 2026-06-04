.PHONY: reinstall test lint release

reinstall:
	uv cache clean pdf-tool
	uv tool install --force --reinstall .

test:
	uv run pytest

lint:
	ruff check pdf_tool tests

release:
	@test -n "$(VERSION)" || { echo "usage: make release VERSION=X.Y.Z"; exit 1; }
	./scripts/release.sh $(VERSION)
