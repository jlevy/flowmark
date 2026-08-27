---
type: is
id: is-01m10zjnf3330k28yp1m5tvjev
title: "PR #81 review PY1: record Python scanner cost profile"
kind: task
status: closed
priority: 3
version: 3
labels:
  - pr-review
  - performance
dependencies: []
parent_id: is-01m10zj8yq0hnkj9mcx57xsq0v
created_at: 2026-08-27T06:47:34.615Z
updated_at: 2026-08-27T08:13:58.996Z
closed_at: 2026-08-27T08:13:58.996Z
close_reason: The requested PY1 profile evidence is recorded and dispositioned; no standalone Python optimization was required.
resolution: null
duplicate_of: null
---
PY1 reports scan_protected_regions at about 42% of Python runtime on testdoc and 8.45 s of 17.1 s on a block-heavy document. Treat as accepted baseline evidence; no standalone optimization is required beyond the concrete PY2-PY4 work because Python speed is not the release-critical target.

## Notes

PY1 accepted as baseline evidence and explicitly dispositioned at flowmark-rs PR comment 5436273177. Python speed remains secondary; the concrete superlinear PY4 paths were fixed, while PY2 and PY3 remain bounded follow-ups.
