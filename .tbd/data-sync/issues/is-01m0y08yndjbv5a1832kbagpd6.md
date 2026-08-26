---
type: is
id: is-01m0y08yndjbv5a1832kbagpd6
title: "P0 vertical slice: colon containers and fenced divs"
kind: feature
status: open
priority: 2
version: 6
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
updated_at: 2026-08-26T03:02:38.842Z
---
Add colon-container/fenced-div preservation end to end through the shared manifest, Python scanner registry, Rust scanner registry, and integration layers.

A compatible logical line with at least three active colons opens; a compatible bare colon run closes. Maintain a nesting stack, preserve opener attributes/title and all raw container prefixes, and do not require the closer run to equal opener length unless a future dialect rule explicitly says so. Cover nested lengths, list/quote containers, blank lines, inline colons, code precedence, mismatched/missing closers, adjacent blocks, attributes, transforms, and idempotence.

Acceptance: exact shared outputs define the permissive union and the Rust port passes the same stable change ID without a copied fixture or divergence.
