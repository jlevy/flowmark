# Makefile for easy development workflows.
# See development.md for docs.
# Note GitHub Actions call uv directly, not this Makefile.

.DEFAULT_GOAL := default

.PHONY: default install lint test test-golden test-golden-coverage upgrade build clean format format-docs benchmark profile

default: format install lint test

format: format-docs

install:
	uv sync --all-extras

lint:
	uv run python devtools/lint.py

test:
	uv run pytest
	$(MAKE) test-golden

test-golden:
	npx tryscript@latest run tests/tryscript/*.tryscript.md

test-golden-coverage:
	bash scripts/check-golden-coverage.sh

upgrade:
	uv sync --upgrade --all-extras --dev

build:
	uv build

clean:
	-rm -rf dist/
	-rm -rf *.egg-info/
	-rm -rf .pytest_cache/
	-rm -rf .mypy_cache/
	-rm -rf .venv/
	-find . -type d -name "__pycache__" -exec rm -rf {} +

format-docs:
	uv run flowmark --auto .

benchmark:
	uv run devtools/benchmark.py --compare 0.6.0

profile:
	uv run devtools/benchmark.py --profile

# Reset the expected reference docs to the actual ones currently produced.
reset-ref-docs:
	cp tests/testdocs/testdoc.actual.auto.md tests/testdocs/testdoc.expected.auto.md
	cp tests/testdocs/testdoc.actual.cleaned.md tests/testdocs/testdoc.expected.cleaned.md
	cp tests/testdocs/testdoc.actual.plain.md tests/testdocs/testdoc.expected.plain.md
	cp tests/testdocs/testdoc.actual.semantic.md tests/testdocs/testdoc.expected.semantic.md
