# Makefile for easy development workflows.
# See development.md for docs.
# Note GitHub Actions call uv directly, not this Makefile.

.DEFAULT_GOAL := default

.PHONY: default install lint lint-check test test-golden test-golden-coverage upgrade build clean \
        format format-docs generate generate-readme generate-skill validate-skill \
        check-release-pin benchmark profile reset-ref-docs

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
#   skills/flowmark/ (published skill bundle) <- generate-skill-discovery.py
#   .agents/.claude/AGENTS.md skill surfaces <- `flowmark --install-skill` (dogfood)
# The skill drift test (tests/test_skill_artifacts.py) fails if any pin is stale.
generate: generate-readme generate-skill generate-skill-install

generate-readme:
	uv run --python 3.14 scripts/generate-python-readme.py

generate-skill:
	uv run scripts/generate-skill-discovery.py

# Dogfood: install flowmark's own skill into this repo's three integration surfaces so the
# checked-in setup always reflects current output and the live DISCOVERY_VERSION pin.
# Idempotent (reports "unchanged" when current); AGENTS.md/.claude are in .flowmarkignore
# so the subsequent format pass leaves them alone.
generate-skill-install:
	uv run flowmark --install-skill

# Validate the published skill against the Agent Skills spec (needs network/npx).
validate-skill:
	npx --yes skills-ref@0.1.5 validate skills/flowmark

# Verify the skill's uvx bootstrap pin is consistent across all shipped artifacts.
# Pass VERSION=X.Y.Z to also assert it matches the release being cut; with no VERSION
# it checks internal consistency only. The publish workflow runs this with the tag.
check-release-pin:
	uv run python scripts/check-release-pin.py $(if $(VERSION),--expected $(VERSION),)

install:
	uv sync --all-extras

lint:
	uv run python devtools/lint.py

# Check-only lint, matching CI (does not modify files).
lint-check:
	uv run python devtools/lint.py --check

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
