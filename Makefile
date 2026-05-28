# Makefile for easy development workflows.
# See development.md for docs.
# Note GitHub Actions call uv directly, not this Makefile.

.DEFAULT_GOAL := default

.PHONY: default install lint test test-golden test-golden-coverage upgrade build clean \
        format format-docs generate generate-readme generate-skill validate-skill \
        benchmark profile reset-ref-docs

default: format install lint test

## ─────────────── Format and Generate ───────────────

# Auto-format the project: regenerate the checked-in generated docs from their sources,
# then run flowmark over the tree. Generation runs first so the format pass leaves the
# generated output canonical too.
format: generate format-docs

# Run flowmark --auto over the tree (respects .gitignore and .flowmarkignore).
format-docs:
	uv run flowmark --auto .

# Regenerate checked-in generated docs from their sources:
#   README.md            <- docs/shared + docs/templates (generate-python-readme.py)
#   skills/flowmark/SKILL.md (published discovery copy) <- generate-skill-discovery.py
# The skill drift test (tests/test_skill_artifacts.py) fails if the discovery copy is stale.
generate: generate-readme generate-skill

generate-readme:
	uv run --python 3.14 scripts/generate-python-readme.py

generate-skill:
	uv run scripts/generate-skill-discovery.py

# Validate the published skill against the Agent Skills spec (needs network/npx).
validate-skill:
	npx skills-ref validate skills/flowmark

install:
	uv sync --all-extras

lint:
	uv run python devtools/lint.py

test:
	uv run pytest
	$(MAKE) test-golden

test-golden:
	npx tryscript@0.1.7 run tests/tryscript/*.tryscript.md

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
