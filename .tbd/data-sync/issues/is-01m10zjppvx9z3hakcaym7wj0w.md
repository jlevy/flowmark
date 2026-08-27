---
type: is
id: is-01m10zjppvx9z3hakcaym7wj0w
title: "PR #81 review PY3: fast-path rendered token parsing"
kind: task
status: open
priority: 3
version: 2
labels:
  - pr-review
  - performance
dependencies: []
parent_id: is-01m10zj8yq0hnkj9mcx57xsq0v
created_at: 2026-08-27T06:47:35.898Z
updated_at: 2026-08-27T08:13:54.033Z
---
PY3 reports bridge.py _parse_rendered_stream as a per-character interpreter loop even for token-free documents. Add marker absence fast paths and bulk str.find/slice processing when Python optimization work resumes, preserving exact restoration and collision behavior.

## Notes

Explicitly deferred in PR comment 5436273177 because Rust runtime speed is release-critical and Python bridge optimization is secondary. Retain as a bounded marker-find and slicing optimization follow-up.
