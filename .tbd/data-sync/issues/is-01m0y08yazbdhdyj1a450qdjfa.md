---
type: is
id: is-01m0y08yazbdhdyj1a450qdjfa
title: "P0 vertical slice: Obsidian callouts"
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
created_at: 2026-08-26T03:02:01.309Z
updated_at: 2026-08-26T11:49:24.877Z
closed_at: 2026-08-26T11:49:24.877Z
close_reason: Obsidian callouts are source-exact in both ports under one shared contract.
resolution: null
duplicate_of: null
---
Add Obsidian callouts through shared cases, Python registry/scanner treatment, direct Rust port, and reviewed integration goldens.

Recognize a blockquote whose first logical content line begins with [!type], optional + or - fold marker, and optional title; preserve the contiguous compatible quote block exactly. Cover type spelling, empty/title forms, nesting, list containers, lazy quote continuations, blank quoted lines, adjacent ordinary quotes, malformed markers, inner Markdown/math/code, and termination when quote/container compatibility changes.

Implement only in the shared preservation registry/scanner files in both ports; parser-specific callout interpretation is not authoritative. Acceptance: one stable change ID maps every case and passes with zero new Rust divergence.

## Notes

Implemented Python in 4a222ea and Rust in 17f92c1 under FM-EXT-OBSIDIAN-CALLOUT-001. Four shared exact cases cover case-preserved types, +/- folds, titles, quoted blanks, nested callouts, lazy continuation, list containers, embedded math/code/wikilinks, and malformed fallback. Both focused selectors and native boundary tests pass with zero divergence.
