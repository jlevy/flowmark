---
type: is
id: is-01kskcdey3v9me5h4f60dxwjh8
title: "Phase A: scope PR explicitly + update stale metadata"
kind: task
status: open
priority: 1
version: 1
spec_path: docs/project/specs/active/plan-2026-05-26-public-inline-api.md
labels: []
dependencies: []
parent_id: is-01kskcc95bk93gn9mz8x57c13z
created_at: 2026-05-27T00:12:40.770Z
updated_at: 2026-05-27T00:12:40.770Z
---
Review #1/#5: PR #47 body still says 'docs-only/Planning spec only' and spec status says 'Planning. Not started.' though Phase A code (atomic.py, ast.py, tests) is now pushed. Update PR body, spec Stage-4 status, and phase checklist so reviewers know they're reviewing Phase A code. Decide+state that this PR is Phase A only (iter_atomic_tokens/split_sentences_with_spans are Phase B, not in this PR).
