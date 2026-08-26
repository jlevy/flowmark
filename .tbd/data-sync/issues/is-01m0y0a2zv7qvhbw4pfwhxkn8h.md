---
type: is
id: is-01m0y0a2zv7qvhbw4pfwhxkn8h
title: "P2 vertical slice: MyST roles and wikilinks"
kind: feature
status: open
priority: 2
version: 1
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01kyss8fvgc7k0yb2xqjz8b0h2
created_at: 2026-08-26T03:02:38.842Z
updated_at: 2026-08-26T03:02:38.842Z
---
After P0 parity, extend inline preservation to general MyST role/backtick spans and double-bracket wikilinks.

Specify run-length closure, role-name and brace boundaries, escapes, nested-looking backticks/brackets, aliases/embeds/anchors, Unicode, adjacency, tables/links/headings/lists, math-role priority, code-span overlap, unmatched fallback, wrapping clusters, transforms, and idempotence in shared desired-output cases. Implement the same deterministic candidates and arbitration in both registries/scanners.

Acceptance: the stable change ID passes every shared layer in Python and Rust, while existing math/code priority remains unchanged and no public atomic-pattern API is silently altered.
