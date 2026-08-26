# Makefile for easy development workflows.
# See docs/development.md for docs.
# Note GitHub Actions call uv directly, not this Makefile.

.DEFAULT_GOAL := default

# Use only the checked-in project configuration. Otherwise uv merges user- and
# system-level settings into uv.lock, which can make it fail on another machine.
UV_CONFIG_FILE := $(CURDIR)/uv.toml
export UV_CONFIG_FILE

# Safe default for every dependency resolution invoked through this Makefile.
UV_EXCLUDE_NEWER ?= 14 days
export UV_EXCLUDE_NEWER

# Tryscript resolves the implementation under test through this injected directory.
# Rust supplies its Cargo binary directory when it consumes the same upstream scripts.
FLOWMARK_BIN_DIR ?= $(CURDIR)/.venv/bin
FLOWMARK_BIN ?= $(FLOWMARK_BIN_DIR)/flowmark

.PHONY: default install lint lint-check test test-conformance accept-conformance test-golden \
        test-golden-coverage upgrade build clean format format-docs generate generate-readme \
        generate-skill validate-skill check-release-pin benchmark profile reset-ref-docs

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
	uv sync --all-extras --all-groups

lint:
	uv run python devtools/lint.py

# Check-only lint, matching CI (does not modify files).
lint-check:
	uv run python devtools/lint.py --check

test: test-conformance
	uv run pytest
	$(MAKE) test-golden

test-conformance:
	uv run python scripts/import-commonmark-spec.py check
	uv run python -m devtools.conformance coverage
	uv run python -m devtools.conformance run --executable "$(FLOWMARK_BIN)"

accept-conformance:
	@test -n "$(strip $(CASES))" || \
		(echo "ERROR: pass exact case IDs with CASES=id.one,id.two" >&2; exit 2)
	uv run python -m devtools.conformance accept --executable "$(FLOWMARK_BIN)" \
		--case-ids "$(CASES)" --write

test-golden:
	FLOWMARK_BIN_DIR="$(FLOWMARK_BIN_DIR)" npx tryscript@0.1.7 run tests/tryscript/*.tryscript.md

test-golden-coverage:
	bash scripts/check-golden-coverage.sh

upgrade:
	uv sync --upgrade --all-extras --all-groups

build: install
	uv build --no-build-isolation

clean:
	-rm -rf dist/
	-rm -rf *.egg-info/
	-rm -rf .pytest_cache/
	-rm -rf .ruff_cache/
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
