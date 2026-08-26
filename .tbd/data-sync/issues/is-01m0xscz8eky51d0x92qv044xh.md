---
type: is
id: is-01m0xscz8eky51d0x92qv044xh
title: Make upstream tryscript and topic fixtures executable-neutral and shared
kind: task
status: closed
priority: 1
version: 8
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y0056wzdgx731m97mrka76
  - type: blocks
    target: is-01m0y042abxn1c7w256z31w81j
parent_id: is-01m0xn2b9tnj99k484920ysv9z
created_at: 2026-08-26T01:01:53.294Z
updated_at: 2026-08-26T03:43:07.448Z
closed_at: 2026-08-26T03:43:07.446Z
close_reason: Replaced every embedded Python executable directory with FLOWMARK_BIN_DIR injection, wired Makefile and CI, proved the unchanged suite against an alternate binary directory, activated six previously dead safe topic fixtures with full readable output, and added a tracked defer ledger for math, inline code, and known-corrupt raw HTML. Golden coverage now rejects implementation paths and dead unowned topic fixtures. Full lint, 471 pytest tests, 139 tryscript checks, and build pass.
resolution: null
duplicate_of: null
---
Make the existing upstream tryscript suite and topic documents one shared test layer for both implementations.

Python repository files:
- tests/tryscript/*.tryscript.md: replace .venv/bin path entries with FLOWMARK_BIN_DIR supplied by the runner.
- tests/tryscript/formatting.tryscript.md: run math.md and code-inline.md as readable full-output workflows.
- tests/tryscript/auto-mode.tryscript.md: include second-pass checks for both topic fixtures.
- tests/tryscript/fixtures/content/math.md and code-inline.md: remain the one canonical integration inputs; never copy or Flowmark-format these exact-syntax fixtures.
- Makefile and .github/workflows/ci.yml: set FLOWMARK_BIN_DIR to the installed Python script directory.
- scripts/check-golden-coverage.sh: reject .venv/bin, target/debug, or other implementation paths and enforce fixture reachability.

Do not commit corrupt expected output as a characterization of known defects. Add desired output with the corresponding fix, and retain deliberate overlap with minimal conformance cases because tryscript validates a different workflow boundary. Acceptance: the suite runs unchanged when only FLOWMARK_BIN_DIR changes.

## Notes

Dependency correction during implementation: this bead makes the complete upstream tryscript harness executable-neutral and validates injected-binary portability. Activating full-output math.md and code-inline.md workflows here would require committing known corruption or leaving normal CI red. Their canonical inputs remain upstream; fm-ucy8 activates and reviews math.md with the Python math fix, and fm-ocpw activates and reviews code-inline.md with the Python code-span fix. This staging is recorded in the linked spec.
