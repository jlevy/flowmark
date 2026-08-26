---
type: is
id: is-01m0zvn8jpssxjwtqqq058sxdz
title: Prove bounded-work preservation scanning in Python and Rust
kind: bug
status: open
priority: 1
version: 1
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - performance
  - preservation
  - parity
dependencies: []
parent_id: is-01m0zvmjwn7hmgcxs7vs5d4py0
created_at: 2026-08-26T20:19:50.997Z
updated_at: 2026-08-26T20:19:50.997Z
---
The preservation spec promises linear scanning, but repeated unmatched candidates in wikilinks, angle-bracket spans, and Pandoc multiline-table detection currently trigger forward rescans consistent with quadratic work in both implementations.

Refactor the recognition strategy so failed candidates do not repeatedly traverse the same suffix. Use shared adversarial fixtures with geometrically increasing inputs for behavior and fixed-point parity. Add small native instrumentation tests that count scanner work or state transitions with deterministic bounds; do not rely only on wall-clock thresholds. Retain fail-closed behavior, precedence, exact restoration, and malformed-input handling.

Acceptance requires the spec's complexity statement to match the implementation, bounded-work evidence in both ports, exact shared outputs, and no regression in the complete preservation and CommonMark corpora.
