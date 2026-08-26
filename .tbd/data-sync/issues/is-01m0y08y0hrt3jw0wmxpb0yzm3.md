---
type: is
id: is-01m0y08y0hrt3jw0wmxpb0yzm3
title: "P0 vertical slice: Pandoc multiline tables"
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
created_at: 2026-08-26T03:02:00.976Z
updated_at: 2026-08-26T11:45:18.524Z
closed_at: 2026-08-26T11:45:18.524Z
close_reason: Pandoc multiline tables are source-exact in both ports under one shared contract.
resolution: null
duplicate_of: null
---
Add one extension-registry vertical slice after math and code parity: shared FM-OPAQUE-P0 cases, Python recognition/treatment, direct Rust port, tryscript/topic integration where useful, and reviewed goldens.

Implement the rule in src/flowmark/preservation/registry.py and scanner.py, then mirror it in Rust src/preservation/registry.rs and scanner.rs. Recognize Pandoc multiline-table caption/header/rule/body structure within one compatible container and preserve the complete block. Cover caption placement, headerless forms, column rules, blank lines, list/quote nesting, false-positive thematic breaks, delimiter-like cell text, unmatched structure, transforms, widths, I/O, and idempotence.

Do not parse cell semantics or copy fixtures between repositories. Acceptance: the stable change ID has zero Rust divergence and all shared layers pass from the pinned upstream commit.

## Notes

Implemented Python in 56274b8 and Rust in 5b0df60 under FM-EXT-MULTILINE-TABLE-001. Four shared exact cases cover headered/headerless forms, following captions, quote containers, transforms, idempotence, and thematic-break fallback. Full Python shared corpus and focused Rust selector pass; no divergence was added.
