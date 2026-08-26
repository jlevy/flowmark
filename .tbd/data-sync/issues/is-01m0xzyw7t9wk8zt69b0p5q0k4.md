---
type: is
id: is-01m0xzyw7t9wk8zt69b0p5q0k4
title: Add selective golden acceptance, reachability, and CI gates
kind: task
status: open
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y00nt855jn33j93519akpr
  - type: blocks
    target: is-01m0y00zvn2e13edc2zyfx6jxn
  - type: blocks
    target: is-01m0y0056wzdgx731m97mrka76
parent_id: is-01m0xn2b9tnj99k484920ysv9z
created_at: 2026-08-26T02:56:31.481Z
updated_at: 2026-08-26T03:06:11.904Z
---
Make the shared corpus load-bearing and safe to maintain.

Files:
- devtools/conformance.py: accept_cases() must require one or more exact case IDs, show the complete proposed diff, and refuse an unbounded update.
- Makefile: add test-conformance, accept-conformance CASES=..., and include conformance in make test.
- scripts/check-golden-coverage.sh: validate the manifest, require each parity payload to be reachable exactly once, and require each topical fixture to be referenced by tryscript or the manifest.
- .github/workflows/ci.yml: run schema/reachability and built-binary conformance checks explicitly.

No ordinary test, CI step, or no-argument command may rewrite a golden. Do not use total test counts as a coverage proxy. Acceptance: dangling entries, dangling files, dead topic fixtures, broad acceptance, malformed schemas, and runner failures all fail CI with bounded actionable output.
