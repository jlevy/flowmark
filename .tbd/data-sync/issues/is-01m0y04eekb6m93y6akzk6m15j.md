---
type: is
id: is-01m0y04eekb6m93y6akzk6m15j
title: Port the preservation model, normalization, and scanners to Rust
kind: task
status: in_progress
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
delegate: codex@spud10.local
labels: []
dependencies:
  - type: blocks
    target: is-01m0y04scg1bkvmbn4bgjx6dk8
parent_id: is-01m0xn1krnmt64xkaw4dkzvc3k
hold: null
hold_until: null
created_at: 2026-08-26T02:59:33.970Z
updated_at: 2026-08-26T10:37:03.776Z
started_at: 2026-08-26T10:07:15.823Z
---
Port the accepted Python behavior by shared change IDs, not by translating Python tests or regexes.

Rust files and functions:
- src/preservation/mod.rs: private facade.
- src/preservation/model.rs: RegionKind, RegionForm, ContainerContext, NormalizedSource, ProtectedRegion, Candidate, validation.
- src/preservation/normalization.rs: normalize_source(), finalize_output(), byte/scalar width helpers.
- src/preservation/registry.rs: the same stable recognizer kinds and precedence.
- src/preservation/scanner.rs: inline/block state machines, container view, escape parity, environment stack, arbitration.
- src/preservation/bridge.rs: deterministic sentinel, token encoding/parsing, protection, validated restoration.
- tests/test_preservation.rs: only small native state/offset/invariant diagnostics.

Bump repos/flowmark to the exact reviewed Python math commit first and use failing shared case IDs/change_ids as the work queue. Rust scans UTF-8 bytes directly and must match the normative algorithm and outputs, not Python object layout. Do not extend wrapping/atomic_patterns.rs regexes or rely on comrak recognition.

Acceptance: core and scanner native diagnostics pass and the Rust implementation is ready for formatter integration with no new dependencies beyond existing toml/testing support unless separately reviewed.

## Notes

Senior review found that a Rust block scanner keyed only by quote depth and content column could pair unmatched delimiters across sibling list items. The implementation now ports Python's active container-frame identity and the upstream shared corpus adds preservation.math.block.sibling-boundaries, which proves the boundary through observable smart-quote transformation. Fixed-width collision-safe tokens replace the earlier provisional sentinel wording.
