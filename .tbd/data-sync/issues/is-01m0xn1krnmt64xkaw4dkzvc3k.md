---
type: is
id: is-01m0xn1krnmt64xkaw4dkzvc3k
title: "Phase 2: port the preservation core and math directly to Rust"
kind: feature
status: closed
priority: 1
version: 10
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
child_order_hints:
  - is-01m0y04eekb6m93y6akzk6m15j
  - is-01m0y04scg1bkvmbn4bgjx6dk8
  - is-01m0y0543cmz5ta9mnenqqq4c6
  - is-01m0y77hm73p235cm8keb26w2m
  - is-01m0y8gztfkha3mss2n1wn55f5
created_at: 2026-08-25T23:45:46.773Z
updated_at: 2026-08-26T19:18:45.260Z
closed_at: 2026-08-26T19:18:45.258Z
close_reason: "The idiomatic Rust preservation port is complete at 90d24c1 against Python 783b445: 476 exact shared passes, only 34 inherited ledgered CommonMark divergences, all shared tryscript/reference/CommonMark layers, 679-test inventory, 670-file zero-diff audit, package smokes, and cross-platform CI pass."
resolution: null
duplicate_of: null
---
Parent for an idiomatic Rust implementation driven by the pinned upstream manifest and change IDs. Port the normalized byte model, registry, scanners, bridge, structured wrapping, comrak adapter, and CLI failure boundaries; then prove zero-new-divergence parity through shared conformance, tryscript, topic, reference, and CommonMark layers.

Do not mirror Python fixtures, regexes, unit-test names, or object layout. The Rust repository already has preservation-related PUA/NUL workarounds; replace them deliberately as shared cases become green rather than stacking a second mechanism. Completion is the submodule commit plus exact passing case IDs and updated port ledger.

## Notes

The idiomatic Rust preservation port is locally complete through Python b027fde and Rust 90203d2. Shared conformance reports 476 exact passes with only the 34 inherited CommonMark ledger entries; all-feature/no-default tests, clippy, rustdoc, packaging, tryscript, reference documents, CommonMark, and the 670-file audit pass. This parent remains open only because Phase 2A retains the remote publication and clean-clone child fm-zah1.
