---
type: is
id: is-01m0y0a1jtnwfh4akan7197358
title: "P1 vertical slice: raw multiline HTML blocks"
kind: feature
status: open
priority: 2
version: 1
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01kyss8fvgc7k0yb2xqjz8b0h2
created_at: 2026-08-26T03:02:37.401Z
updated_at: 2026-08-26T03:02:37.401Z
---
After P0 parity, preserve raw multiline HTML using CommonMark 0.31.2 HTML-block boundaries and one shared change ID.

Implement boundary recognition in the preservation scanner registries, then retain the exact raw block rather than relying on Marko/comrak re-rendering. Cover all CommonMark HTML block types, comments/declarations/processing instructions/CDATA, blank-line termination, raw tags, custom tags, embedded Markdown/math, list/quote context where legal, unmatched-looking text, adjacency, CRLF/BOM, transforms, and idempotence.

Use the pinned CommonMark examples as standards coverage plus minimal Flowmark cases for exact treatment. Acceptance: Python and Rust pass the same bytes without parser-specific boundary drift.
