---
type: is
id: is-01m0y08yndjbv5a1832kbagpd6
title: "P0 vertical slice: colon containers and fenced divs"
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
created_at: 2026-08-26T03:02:01.644Z
updated_at: 2026-08-26T11:53:45.464Z
closed_at: 2026-08-26T11:53:45.463Z
close_reason: Colon containers and fenced divs are source-exact in both ports under one shared contract.
resolution: null
duplicate_of: null
---
Add colon-container/fenced-div preservation end to end through the shared manifest, Python scanner registry, Rust scanner registry, and integration layers.

A compatible logical line with at least three active colons opens; a compatible bare colon run closes. Maintain a nesting stack, preserve opener attributes/title and all raw container prefixes, and do not require the closer run to equal opener length unless a future dialect rule explicitly says so. Cover nested lengths, list/quote containers, blank lines, inline colons, code precedence, mismatched/missing closers, adjacent blocks, attributes, transforms, and idempotence.

Acceptance: exact shared outputs define the permissive union and the Rust port passes the same stable change ID without a copied fixture or divergence.

## Notes

Implemented Python in 1b684b5 and Rust in cb96b17 under FM-EXT-COLON-CONTAINER-001. Shared cases cover nested unequal fence lengths, attributes, list/quote containers, fenced-code precedence, unmatched outer fallback with a preserved closed inner, inline colons, and fixed points. Python also now permits containment-only overlap between an outer protected extension and existing opaque code ranges while still rejecting partial overlap.
