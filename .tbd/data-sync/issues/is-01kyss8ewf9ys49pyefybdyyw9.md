---
type: is
id: is-01kyss8ewf9ys49pyefybdyyw9
title: "Phase 4A: P0 opaque-extension vertical slices"
kind: feature
status: open
priority: 2
version: 9
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01kyss8gskyz68yaky5j8vrnpx
parent_id: is-01m0xn12jj483njnx12sm0sjs1
child_order_hints:
  - is-01m0y08y0hrt3jw0wmxpb0yzm3
  - is-01m0y08yazbdhdyj1a450qdjfa
  - is-01m0y08yndjbv5a1832kbagpd6
  - is-01m0y08z09p26pakg08h937pfd
  - is-01m0y08zeydjc34a7dyd0feamy
created_at: 2026-07-30T15:11:04.078Z
updated_at: 2026-08-26T03:03:47.855Z
---
Parent for the highest-risk extension registry families after math and code parity: Pandoc multiline tables, Obsidian callouts, colon containers/fenced divs, TOML frontmatter, and definition lists.

Each child is an end-to-end vertical slice: specify a case matrix and stable change ID, add reviewed shared desired-output cases, implement the Python registry/scanner rule, port it directly to Rust, run all shared layers, and require zero new divergence. This keeps recognition rules explicit and prevents a Python-only backlog from accumulating.
