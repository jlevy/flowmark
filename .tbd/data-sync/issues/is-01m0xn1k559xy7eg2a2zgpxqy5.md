---
type: is
id: is-01m0xn1k559xy7eg2a2zgpxqy5
title: "Track A Phase 1: math corpus and red tests"
kind: task
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
created_at: 2026-08-25T23:45:46.149Z
updated_at: 2026-08-26T02:41:48.633Z
---
Build the math coverage from shared tests first. Expand the upstream math.md integration fixture, add minimal desired-output cases for the complete math matrix under stable change IDs, run the same cases in Python and Rust, and wire the same upstream fixture into the shared tryscript and whole-document layers. Add only a small number of Python-native scanner/property tests for byte-index, state-machine, adapter, and fail-closed invariants that cannot be isolated cleanly at the shared CLI boundary.

## Notes

PR #71 expanded the seed around intraword and whitespace-padded math, soft newlines, container contexts, parser collisions, Unicode, escape parity, structural table-cell boundaries, empty dollar runs, unmatched-outer fallback, and malformed environments. Every observable promise belongs in the shared corpus; layered integration overlap is intentional.
