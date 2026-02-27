# Plan Spec: Python Flowmark Full Tryscript Migration and Golden Harness Hardening

## Purpose

Complete a full migration of Python Flowmark CLI golden coverage to a comprehensive,
fixture-first tryscript harness and establish quality gates so the suite remains
systematic and maintainable.

## Background

Current Python Flowmark test state (2026-02-27):

1. `pytest` test suite is extensive (`~304` collected tests).
2. Tryscript coverage exists but is narrow:
- `tests/golden/cli-golden.tryscript.md`
- `25` scenarios in a single monolithic file
3. CI already runs tryscript (`npx tryscript@latest run`), but there is no dedicated
   tryscript config file and no automated command coverage gate.
4. The Rust case study repo (`../flowmark-rs`) now has a richer, split tryscript layout:
- `12` `.tryscript.md` files
- `61` fixture files under `tests/tryscript/fixtures`

Current state after this migration tranche:

1. Python Flowmark now has `12` tryscript files under `tests/tryscript/`.
2. Imported fixture tree includes `61` fixture files.
3. `npx tryscript@latest run tests/tryscript/*.tryscript.md` passes (`119` scenarios).
4. Legacy monolithic `tests/golden/cli-golden.tryscript.md` has been removed.

Third-party reference reviewed via `tbd shortcut checkout`:
- `attic/blobsy` ([jlevy/blobsy](https://github.com/jlevy/blobsy))

Blobsy patterns worth adopting:

1. central `tryscript.config.ts` with normalized env/path/patterns
2. taxonomy split by concern (`commands`, `errors`, `workflows`, `json`)
3. golden quality gate script enforcing command coverage and anti-pattern checks
4. deterministic placeholder patterns for volatile fields

Applied from blobsy in this migration:

1. root `tryscript.config.ts` with global env/path/patterns
2. modular scenario layout replacing single-file monolith
3. `scripts/check-golden-coverage.sh` gate with anti-pattern enforcement

## Summary of Task

Create and stabilize a Python-first tryscript golden harness that is:

1. comprehensive (all major CLI surfaces)
2. fixture-first (not mostly inline shell snippets)
3. deterministic (scrubbed and patternized)
4. enforceable in CI (coverage gate + tryscript run)

This migration should make tryscript the primary golden harness for CLI behavior.

## Backward Compatibility

### Compatibility mode

- Strict CLI behavior compatibility for Python Flowmark users.

### Protected surfaces

1. CLI output and exit-code behavior
2. file discovery behavior (`--list-files`, include/exclude, ignore semantics)
3. formatting behavior for `--auto` and core formatting flags

### Allowed migration changes

1. test harness structure and file organization
2. deterministic normalization patterns in golden files
3. replacement of monolithic golden files with split tryscript modules

## Stage 1: Planning Stage

### Scope

In scope:

1. migrate from single-file golden tryscript to full multi-file fixture-first suite
2. add tryscript config and coverage gate scripts
3. wire CI and make targets for maintainable execution

Out of scope:

1. changing documented CLI behavior intentionally
2. broad feature additions unrelated to testability

### Acceptance criteria

1. Python repo has split tryscript suite under `tests/tryscript/` covering all major CLI
   feature families.
2. Existing single-file `tests/golden/cli-golden.tryscript.md` is either retired or
   clearly marked legacy and superseded.
3. CI runs tryscript suite and golden coverage gate script.
4. Command coverage matrix exists and is enforced by script.
5. Full Python test suite passes after migration.

## Stage 2: Architecture Stage

### Target test architecture

1. `tests/tryscript/` for scenario files
2. `tests/tryscript/fixtures/` for reusable content/project/config fixtures
3. root `tryscript.config.ts` for deterministic settings
4. `scripts/check-golden-coverage.sh` for quality/coverage enforcement

### Suite organization

Use the flowmark-rs case-study structure and naming where possible:

1. `help.tryscript.md`
2. `errors-version.tryscript.md`
3. `formatting.tryscript.md`
4. `typography-tests.tryscript.md`
5. `list-spacing.tryscript.md`
6. `auto-mode.tryscript.md`
7. `file-ops.tryscript.md`
8. `stdin.tryscript.md`
9. `file-discovery.tryscript.md`
10. `config-interaction.tryscript.md`
11. `verbose-docs.tryscript.md`
12. `cli-golden.tryscript.md` (transition/legacy compatibility only if needed)

### Determinism strategy

1. global env via config: `NO_COLOR=1`, `LC_ALL=C`
2. stable path resolution for `flowmark` binary (`.venv/bin`)
3. explicit regex placeholders for volatile values
4. ban broad `...` output-elision anti-pattern in committed tests

## Stage 3: Refine Architecture

### Reuse opportunities

1. Import fixtures and scenario split from `../flowmark-rs/tests/tryscript`.
2. Reuse existing Python fixture docs and content files where equivalent.
3. Borrow quality-gate concepts from `attic/blobsy/packages/blobsy/scripts/check-golden-coverage.sh`.

### Key improvements over current Python setup

1. move from one monolithic tryscript file to modular scenario files
2. introduce explicit command coverage checks
3. add dedicated migration/parity backlog capture for failing scenarios

## Stage 4: Implementation Plan

### Phase F1: Spec and baseline inventory

- [x] quantify current python tryscript coverage and limits
- [x] review flowmark-rs tryscript structure for reusable assets
- [x] review blobsy tryscript quality-gate patterns
- [x] publish this migration spec

### Phase F2: Import and adapt tryscript suite

- [x] copy `tests/tryscript/` fixtures + scenario files from `../flowmark-rs`
- [x] adapt binary path for Python runtime (`$TRYSCRIPT_GIT_ROOT/.venv/bin`)
- [x] normalize scenario metadata and ensure deterministic behavior
- [x] run tryscript and record failures by category

### Phase F3: Add quality gates

- [x] add root `tryscript.config.ts`
- [x] add `scripts/check-golden-coverage.sh` with:
  - command coverage checks
  - anti-pattern checks (`...` elisions)
- [x] add `make test-golden` target for tryscript
- [x] update CI to run coverage check before/with tryscript

### Phase F4: Validate and reconcile

- [x] run `uv run pytest`
- [x] run `npx tryscript@latest run`
- [x] run coverage gate script
- [x] triage failures into parity/migration backlog items
- [x] deprecate or remove legacy monolithic golden file when superseded

## Validation Plan

Primary commands:

```bash
uv run pytest
npx tryscript@latest run tests/tryscript/*.tryscript.md
bash scripts/check-golden-coverage.sh
```

Secondary checks:

1. verify all major CLI commands are represented in at least one tryscript scenario
2. verify no unstable output fields leak into goldens without patternization
3. verify CI green on all required jobs

## Deliverables

1. comprehensive tryscript scenario set under `tests/tryscript/`
2. reusable fixture tree for content/project/config discovery behaviors
3. `tryscript.config.ts`
4. command coverage + anti-pattern gate script
5. migration report with failure triage and follow-up backlog

## Tracking

`tbd` epic and tasks:

- Epic: `fm-o1o9`
- F1 spec: `fm-aqn6`
- F2 suite import/adaptation: `fm-kulj`
- F3 config/gates: `fm-l04j`
- F4 validation/reconciliation: `fm-nj3v`
