---
type: is
id: is-01m0xn1k559xy7eg2a2zgpxqy5
title: "Phase 1A: define shared desired-output math behavior"
kind: feature
status: closed
priority: 1
version: 7
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
child_order_hints:
  - is-01m0y00nt855jn33j93519akpr
  - is-01m0y00zvn2e13edc2zyfx6jxn
created_at: 2026-08-25T23:45:46.149Z
updated_at: 2026-08-26T07:46:00.545Z
closed_at: 2026-08-26T07:46:00.545Z
close_reason: Committed reviewed language-neutral desired-output math contract and pre-fix classification in 9ee6444; full lint, type, conformance, pytest, and tryscript gates pass.
resolution: null
duplicate_of: null
---
Parent for the red shared tests that define FM-PRESERVE-CORE-001, FM-MATH-INLINE-001, and FM-MATH-BLOCK-001 before implementation. Use minimal exact cases for pinpoint behavior plus math.md and reference/CommonMark layers for interactions. Cover the full recognition, normalization, parser-collision, container, wrapping, transform, mode, I/O, malformed, idempotence, and adversarial matrices without building a Cartesian product.

Expected output is reviewed product intent, never a whitespace-stripped Python oracle or blindly captured known corruption. Small native tests belong with implementation children only when an internal invariant cannot be isolated at the shared CLI boundary.

## Notes

PR #71 expanded the seed around intraword and whitespace-padded math, soft newlines, container contexts, parser collisions, Unicode, escape parity, structural table-cell boundaries, empty dollar runs, unmatched-outer fallback, and malformed environments. Every observable promise belongs in the shared corpus; layered integration overlap is intentional.
