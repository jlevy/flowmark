---
type: is
id: is-01m10nx6xr86enx1x2h5mkcqs8
title: Resolve or document low-impact CommonMark source-form differences
kind: task
status: open
priority: 3
version: 1
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - commonmark
  - conformance
dependencies: []
parent_id: is-01m0zvmjwn7hmgcxs7vs5d4py0
created_at: 2026-08-27T03:58:34.423Z
updated_at: 2026-08-27T03:58:34.423Z
---
After high-impact CommonMark behavior is clean, classify the remaining uncommon examples and semantically equivalent spellings. Prefer source-form fidelity where it is stable and useful, but permit reviewed formatter canonicalization of markers, indentation, blank lines, or equivalent delimiters when parsed structure, fixed-point behavior, and cross-port bytes remain correct. Activate exact expectations for resolved cases and list every retained intentional normalization or unsupported edge case in the language-neutral support catalog and public known-gaps documentation. Acceptance: all 652 CommonMark 0.31.2 examples have a reviewed disposition; no case is deferred without an open owner; source-exact, semantically equivalent normalization, and known-gap outcomes are distinguishable; Python and Rust agree exactly on the shared contract.
