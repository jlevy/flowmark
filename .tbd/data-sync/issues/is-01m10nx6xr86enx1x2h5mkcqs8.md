---
type: is
id: is-01m10nx6xr86enx1x2h5mkcqs8
title: Review low-impact CommonMark source-form choices
kind: task
status: open
priority: 3
version: 3
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - commonmark
  - conformance
dependencies: []
parent_id: is-01m0zvmjwn7hmgcxs7vs5d4py0
created_at: 2026-08-27T03:58:34.423Z
updated_at: 2026-08-27T04:08:54.321Z
---
After high-impact CommonMark behavior is clean, review the remaining uncommon examples and semantically equivalent source-form choices. Prefer the stable line wrapping, marker style, indentation, blank-line policy, and delimiters that make Flowmark output easiest to read and edit. Preserve input spelling exactly only when re-rendering is unsafe or source fidelity clearly improves the editing experience. Activate exact shared expectations for each chosen output and list every unsupported edge case in the language-neutral catalog and public known-gaps documentation. Acceptance: all 652 CommonMark 0.31.2 examples have a reviewed disposition; no case is deferred without an open owner; compatible Flowmark normalization, selective source-exact treatment, and real known gaps are distinguishable; output reaches a fixed point and Python/Rust agree exactly.
