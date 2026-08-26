---
type: is
id: is-01m0xzyjzy4xf6vn0g5nsa5zdw
title: Build the Python native conformance runner against the installed CLI
kind: task
status: closed
priority: 1
version: 6
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0xzyw7t9wk8zt69b0p5q0k4
  - type: blocks
    target: is-01m0xzz7sn1zkyekpady04eh38
  - type: blocks
    target: is-01m0y0056wzdgx731m97mrka76
parent_id: is-01m0xn2b9tnj99k484920ysv9z
created_at: 2026-08-26T02:56:22.012Z
updated_at: 2026-08-26T03:32:38.118Z
closed_at: 2026-08-26T03:32:38.117Z
close_reason: Implemented the strict Python schema validator and native installed-binary runner with exact byte and file-tree comparison, idempotent fresh-sandbox passes, exact selectors, minimal environment, timeouts, bounded diagnostics, shared malformed/failure fixtures, and invalid-UTF-8 transport coverage. Full lint, 471 pytest tests, 133 tryscript checks, and build pass.
resolution: null
duplicate_of: null
---
Implement the Python adapter for FM-CONFORMANCE-001 after the shared schema exists.

Files and functions:
- devtools/conformance.py: load_manifest(), validate_manifest(), select_cases(), materialize_case(), run_case(), compare_result(), and accept_cases().
- tests/test_conformance.py: collect the manifest and invoke the installed flowmark executable, never fill_markdown().
- Shared runner-fixtures under tests/parity_corpus/ validate unknown fields, duplicates, bad paths, symlinks, missing payloads, kind-specific fields, exact bytes, file-tree completeness, idempotence, timeouts, and bounded diagnostics.

The runner must use a minimal allowlisted environment, fresh sandbox per run, byte-oriented stdin/stdout/stderr and file comparisons, explicit executable injection, exact ID/change_id/tag filters, and a generous per-case hang watchdog. Reuse tomllib/tomli already shipped by the project. Keep native tests about runner mechanics; product behavior lives in manifest cases.

Acceptance: all seed cases run against the built/installed Python CLI, every shared malformed fixture has its specified result, invalid UTF-8 can be passed as bytes, and no expected output is synthesized in a normal test.
