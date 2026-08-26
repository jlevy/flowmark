---
type: is
id: is-01m0y0a2fn4je9ddv5s4h8aa5b
title: "P2 vertical slice: Pandoc line blocks"
kind: feature
status: closed
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01kyss8fvgc7k0yb2xqjz8b0h2
created_at: 2026-08-26T03:02:38.324Z
updated_at: 2026-08-26T13:08:40.319Z
closed_at: 2026-08-26T13:08:40.317Z
close_reason: null
resolution: null
duplicate_of: null
---
After P0 parity, add Pandoc line-block preservation from shared cases through Python and Rust.

Recognize contiguous compatible container-content lines beginning with an active vertical bar and required following space; preserve every authored line, indentation, and inline body. Cover blank line-block lines, escaped bars, table ambiguity, blockquotes/lists, Unicode, hard breaks, math/code inside, adjacency, malformed starters, termination, transforms, widths, and idempotence.

Acceptance: exact outputs under a stable change ID pass in both ports with no copied assets or divergence.
