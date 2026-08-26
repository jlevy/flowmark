---
type: is
id: is-01m0y0a0hssvaatcwxcydjya23
title: "P1 vertical slice: Pandoc grid tables"
kind: feature
status: open
priority: 2
version: 1
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01kyss8fvgc7k0yb2xqjz8b0h2
created_at: 2026-08-26T03:02:36.328Z
updated_at: 2026-08-26T03:02:36.328Z
---
After every P0 family has Python/Rust parity, add Pandoc grid tables through shared desired-output cases and both preservation registries/scanners.

Recognize compatible top/bottom borders and row/separator lines as one container-bound opaque block. Cover simple/multiline cells, header separators, alignment widths, Unicode, nested Markdown-like content, list/quote containers, adjacency, broken borders, false-positive ASCII art, missing bottom borders, transforms, width modes, and idempotence.

Acceptance: a stable change ID passes all upstream layers in both ports with exact source preservation and no new divergence.
