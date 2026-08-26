---
type: is
id: is-01m0xn1krnmt64xkaw4dkzvc3k
title: "Phase 2: port the preservation core and math directly to Rust"
kind: feature
status: open
priority: 1
version: 7
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
child_order_hints:
  - is-01m0y04eekb6m93y6akzk6m15j
  - is-01m0y04scg1bkvmbn4bgjx6dk8
  - is-01m0y0543cmz5ta9mnenqqq4c6
  - is-01m0y77hm73p235cm8keb26w2m
created_at: 2026-08-25T23:45:46.773Z
updated_at: 2026-08-26T05:03:35.548Z
---
Parent for an idiomatic Rust implementation driven by the pinned upstream manifest and change IDs. Port the normalized byte model, registry, scanners, bridge, structured wrapping, comrak adapter, and CLI failure boundaries; then prove zero-new-divergence parity through shared conformance, tryscript, topic, reference, and CommonMark layers.

Do not mirror Python fixtures, regexes, unit-test names, or object layout. The Rust repository already has preservation-related PUA/NUL workarounds; replace them deliberately as shared cases become green rather than stacking a second mechanism. Completion is the submodule commit plus exact passing case IDs and updated port ledger.
