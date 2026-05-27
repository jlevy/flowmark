# Makefile for easy development workflows.
# See development.md for docs.
# Note GitHub Actions call uv directly, not this Makefile.

.DEFAULT_GOAL := default

.PHONY: default install lint test test-golden test-golden-coverage upgrade build clean format format-docs gen-skill validate-skill benchmark profile

default: format install lint test

format: format-docs gen-skill

# Regenerate the committed repo-root skill discovery copy from the authored SKILL.md.
# The drift test (tests/test_skill_artifacts.py) fails if this is out of date.
gen-skill:
	uv run python -c "from pathlib import Path; from flowmark.skill import discovery_skill_text; Path('skills/flowmark/SKILL.md').write_text(discovery_skill_text(), encoding='utf-8')"

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
