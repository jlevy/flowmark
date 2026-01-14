# Makefile for easy development workflows.
# See development.md for docs.
# Note GitHub Actions call uv directly, not this Makefile.

.DEFAULT_GOAL := default

<<<<<<< before updating
.PHONY: default install lint test upgrade build clean agent-rules format-docs

default: agent-rules format-docs install lint test 
=======
.PHONY: default install lint test upgrade build clean

default: install lint test 
>>>>>>> after updating

install:
	uv sync --all-extras

lint:
	uv run python devtools/lint.py

test:
	uv run pytest

upgrade:
	uv sync --upgrade --all-extras --dev

build:
	uv build

<<<<<<< before updating
agent-rules: CLAUDE.md GEMINI.md AGENTS.md

# Use .cursor/rules for sources of rules.
# Create Claude and Codex rules from these.
CLAUDE.md: .cursor/rules/general.mdc .cursor/rules/python.mdc
	cat .cursor/rules/general.mdc .cursor/rules/python.mdc .cursor/rules/flowmark.mdc > CLAUDE.md

GEMINI.md: .cursor/rules/general.mdc .cursor/rules/python.mdc
	cat .cursor/rules/general.mdc .cursor/rules/python.mdc .cursor/rules/flowmark.mdc > GEMINI.md

AGENTS.md: .cursor/rules/general.mdc .cursor/rules/python.mdc
	cat .cursor/rules/general.mdc .cursor/rules/python.mdc .cursor/rules/flowmark.mdc > AGENTS.md

=======
>>>>>>> after updating
clean:
	-rm -rf dist/
	-rm -rf *.egg-info/
	-rm -rf .pytest_cache/
	-rm -rf .mypy_cache/
	-rm -rf .venv/
	-find . -type d -name "__pycache__" -exec rm -rf {} +

format-docs:
	uv run flowmark --auto README.md

# Reset the expected reference docs to the actual ones currently produced.
reset-ref-docs:
	cp tests/testdocs/testdoc.actual.auto.md tests/testdocs/testdoc.expected.auto.md
	cp tests/testdocs/testdoc.actual.cleaned.md tests/testdocs/testdoc.expected.cleaned.md
	cp tests/testdocs/testdoc.actual.plain.md tests/testdocs/testdoc.expected.plain.md
	cp tests/testdocs/testdoc.actual.semantic.md tests/testdocs/testdoc.expected.semantic.md

