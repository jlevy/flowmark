---
type: is
id: is-01kyss8fvgc7k0yb2xqjz8b0h2
title: "Phase 4B: P1/P2 extension-registry vertical slices"
kind: feature
status: closed
priority: 2
version: 10
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01kyss8gskyz68yaky5j8vrnpx
parent_id: is-01m0xn12jj483njnx12sm0sjs1
child_order_hints:
  - is-01m0y0a0hssvaatcwxcydjya23
  - is-01m0y0a1jtnwfh4akan7197358
  - is-01m0y0a1zxz367b842m3kx96xp
  - is-01m0y0a2fn4je9ddv5s4h8aa5b
  - is-01m0y0a2zv7qvhbw4pfwhxkn8h
created_at: 2026-07-30T15:11:05.072Z
updated_at: 2026-08-26T13:15:00.639Z
closed_at: 2026-08-26T13:15:00.638Z
close_reason: null
resolution: null
duplicate_of: null
---
Parent for lower-severity extension families after all P0 slices have Python/Rust parity: Pandoc grid tables, raw multiline HTML, attribute groups, line blocks, and general MyST roles/wikilinks.

Each child owns shared cases, Python treatment, direct Rust port, and integration review under one stable change ID. Delimiter and marker fidelity not covered by an explicit preservation policy remains out of scope until specified; parser-specific behavior never substitutes for the shared source contract.
