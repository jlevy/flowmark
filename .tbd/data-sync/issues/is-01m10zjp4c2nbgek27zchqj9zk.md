---
type: is
id: is-01m10zjp4c2nbgek27zchqj9zk
title: "PR #81 review PY2: reduce byte-to-scalar conversion overhead"
kind: bug
status: open
priority: 3
version: 2
labels:
  - pr-review
  - performance
dependencies: []
parent_id: is-01m10zj8yq0hnkj9mcx57xsq0v
created_at: 2026-08-27T06:47:35.306Z
updated_at: 2026-08-27T08:13:53.782Z
---
PY2 reports model.py scalar_index called about 2.0 million times and consuming 4.05 s on a 135 KB block-heavy document, plus high scalar_byte_offsets memory cost. Defer a representation/cursor optimization until Rust parity is stable; retain UTF-8 byte offsets at the language-neutral contract boundary.

## Notes

Explicitly deferred in PR comment 5436273177. Preserve UTF-8 byte offsets at the portable contract boundary; revisit scalar-internal coordinates only as a separately validated Python optimization.
