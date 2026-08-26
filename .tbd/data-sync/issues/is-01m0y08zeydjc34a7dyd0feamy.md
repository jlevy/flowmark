---
type: is
id: is-01m0y08zeydjc34a7dyd0feamy
title: "P0 vertical slice: definition lists"
kind: feature
status: closed
priority: 2
version: 8
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y0a0hssvaatcwxcydjya23
  - type: blocks
    target: is-01m0y0a1jtnwfh4akan7197358
  - type: blocks
    target: is-01m0y0a1zxz367b842m3kx96xp
  - type: blocks
    target: is-01m0y0a2fn4je9ddv5s4h8aa5b
  - type: blocks
    target: is-01m0y0a2zv7qvhbw4pfwhxkn8h
parent_id: is-01kyss8ewf9ys49pyefybdyyw9
created_at: 2026-08-26T03:02:02.459Z
updated_at: 2026-08-26T12:23:17.839Z
closed_at: 2026-08-26T12:23:17.838Z
close_reason: Pandoc definition lists are specified and source-exact in Python 30de4c0 and Rust 14cb570 under FM-EXT-DEFINITION-LIST-001. Four shared cases cover term/marker/continuation/container/opaque/fallback boundaries; native scanner tests, both selectors, full shared conformance, and both tryscript layers pass.
resolution: null
duplicate_of: null
---
Add definition-list preservation as one shared-to-Rust vertical slice.

Recognize one or more term lines followed by compatible definition markers in the same container and preserve the contiguous definition-list block. Specify marker spacing, continuation indentation, multiple terms/definitions, blank lines, nested lists/quotes, lazy continuation, inline math/code, colon-container ambiguity, ordinary colon prose, malformed/incomplete forms, boundaries, transforms, and idempotence before implementation.

Implement in the Python and Rust preservation registries/scanners, not in parser-specific cleanup heuristics. Acceptance: reviewed shared cases and topic/reference documents pass under one stable change ID with zero new Rust divergence.
