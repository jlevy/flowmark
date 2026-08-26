---
type: is
id: is-01m0yqefdexrdhzxa7hqg2cqj6
title: Bound parser-token expansion under adversarial marker collisions
kind: bug
status: closed
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
delegate: codex@spud10.local
labels: []
dependencies:
  - type: blocks
    target: is-01m0y042abxn1c7w256z31w81j
parent_id: is-01m0xn1kf4s20aga85f298dzww
hold: null
hold_until: null
created_at: 2026-08-26T09:46:59.873Z
updated_at: 2026-08-26T09:53:17.977Z
started_at: 2026-08-26T09:47:06.810Z
closed_at: 2026-08-26T09:53:17.976Z
close_reason: Replaced the variable-length absent sentinel with reversible authored-marker escaping and fixed ten-scalar unsigned-64-bit tokens. Added a constant-factor expansion invariant over 4,096 marker collisions and 2,048 regions; focused native, shared core/math, full-topic tryscript, and lint/type gates pass in commit 0a0532e.
resolution: null
duplicate_of: null
---
The variable-length absent sentinel makes every token proportional to the longest authored U+F0000 run before U+F0001. Combining an O(n) collision run with O(n) protected regions expands parser-facing text to O(n^2), contradicting the normative complexity contract and creating a memory/DoS risk that would otherwise be copied into Rust. Replace it with a portable fixed-width token encoding plus reversible escaping of authored marker scalars; validate malformed escapes/tokens fail closed; add a native expansion-bound invariant and shared collision coverage; update the spec and Rust mapping.
