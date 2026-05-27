---
type: is
id: is-01kskcdj5jkydhmc0v9ye1pcvh
title: "Phase B: refactor _extract_atomic_constructs onto iter_atomic_tokens"
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-05-26-public-inline-api.md
labels: []
dependencies:
  - type: blocks
    target: is-01kskcdjgxdyx2rwyw8nkabwh7
parent_id: is-01kskcc95bk93gn9mz8x57c13z
created_at: 2026-05-27T00:12:44.081Z
updated_at: 2026-05-27T00:12:55.473Z
---
Spec Phase B: reimplement the wrapping word splitter (text_wrapping.py:39 placeholder dance) on iter_atomic_tokens to collapse flowmark's two atomic mechanisms into one. Wrapping golden corpus must stay byte-identical.
