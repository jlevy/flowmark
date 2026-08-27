---
type: is
id: is-01m0zvn8jpssxjwtqqq058sxdz
title: Prove bounded-work preservation scanning in Python and Rust
kind: bug
status: in_progress
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - performance
  - preservation
  - parity
dependencies: []
parent_id: is-01m0zvmjwn7hmgcxs7vs5d4py0
created_at: 2026-08-26T20:19:50.997Z
updated_at: 2026-08-27T08:13:53.284Z
---
The preservation spec promises linear scanning, but repeated unmatched candidates in wikilinks, angle-bracket spans, and Pandoc multiline-table detection currently trigger forward rescans consistent with quadratic work in both implementations.

Refactor the recognition strategy so failed candidates do not repeatedly traverse the same suffix. Use shared adversarial fixtures with geometrically increasing inputs for behavior and fixed-point parity. Add small native instrumentation tests that count scanner work or state transitions with deterministic bounds; do not rely only on wall-clock thresholds. Retain fail-closed behavior, precedence, exact restoration, and malformed-input handling.

Acceptance requires the spec's complexity statement to match the implementation, bounded-work evidence in both ports, exact shared outputs, and no regression in the complete preservation and CommonMark corpora.

## Notes

PY4 angle and wikilink quadratics are fixed in 970eba6 with bounded reverse and suffix-state scans. Direct exact differentials covered 335,922 exhaustive plus 200,000 random angle inputs and 2,015,538 exhaustive plus 200,000 random wikilink inputs; 9e9fd7c covers the processing-instruction overlap discovered by the differential. Full Python lint, 540 pytest cases, 143 tryscript cases, CommonMark and shared corpora, and build passed; hosted PR CI is green. Keep open for the remaining Pandoc audit and deterministic operation-count evidence required by this broader bead.
