---
type: is
id: is-01m10zj8yq0hnkj9mcx57xsq0v
title: "Address PR #81 follow-up: upstream Python performance observations"
kind: task
status: closed
priority: 2
version: 6
labels:
  - pr-review
  - performance
  - preservation
dependencies: []
child_order_hints:
  - is-01m10zjnf3330k28yp1m5tvjev
  - is-01m10zjp4c2nbgek27zchqj9zk
  - is-01m10zjppvx9z3hakcaym7wj0w
created_at: 2026-08-27T06:47:21.813Z
updated_at: 2026-08-27T08:13:59.255Z
closed_at: 2026-08-27T08:13:59.254Z
close_reason: All PY1-PY4 observations have a published disposition; PY2 and PY3 remain named follow-ups and PY4 is fixed.
resolution: null
duplicate_of: null
---
Track PY1-PY4 from flowmark-rs PR #81 issue comment 5435358838 against Python PR #71. Rust speed is release-critical; Python optimization is secondary by explicit maintainer policy, but superlinear recognizers remain a shared-contract concern. Deduplicate PY4 against fm-svww.

## Notes

PY1-PY4 dispositions were published at flowmark-rs PR comment 5436273177. PY4 is fixed in Python commits 970eba6 and 9e9fd7c; PY1 is recorded; PY2 and PY3 remain explicit non-blocking follow-up beads.
