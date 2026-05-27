---
type: is
id: is-01kskcdh0dyar758qn8hehdgwe
title: "Phase A: keep top-level flowmark.__all__ conservative"
kind: task
status: open
priority: 3
version: 1
spec_path: docs/project/specs/active/plan-2026-05-26-public-inline-api.md
labels: []
dependencies: []
parent_id: is-01kskcc95bk93gn9mz8x57c13z
created_at: 2026-05-27T00:12:42.893Z
updated_at: 2026-05-27T00:12:42.893Z
---
Review suggestion: submodules (flowmark.atomic, flowmark.ast) are the canonical boundary. Trim top-level re-exports to only the names most callers use directly; avoid flattening the whole surface into __init__.
