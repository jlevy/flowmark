---
type: is
id: is-01m0y77jb7s7xmtm7hrb2z3aed
title: Rebuild Flowmark-rs port status and sync records around shared change IDs
kind: task
status: closed
priority: 1
version: 7
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
delegate: codex@spud10.local
labels: []
dependencies:
  - type: blocks
    target: is-01m0y8gztfkha3mss2n1wn55f5
  - type: blocks
    target: is-01m0y8gztkqwb8vp1pd8qteftc
  - type: blocks
    target: is-01m0y94jg6wy9mh8jwwnt51ncm
parent_id: is-01m0y77hm73p235cm8keb26w2m
created_at: 2026-08-26T05:03:36.294Z
updated_at: 2026-08-26T05:42:07.080Z
closed_at: 2026-08-26T05:42:07.079Z
close_reason: Current status, sync artifact, QA workflow, historical records, and shared change-ID evidence are systematic, formatted, link-checked, and committed as 4cdeb64.
resolution: null
duplicate_of: null
---
Replace stale version/test-count parity claims with a living record keyed by the pinned Python submodule commit, shared schema version, change IDs, Rust beads, exact known-divergence entries, and validation commands. Revise docs/port-sync-playbook.md, docs/port-status.md, the active sync plan, QA guidance, and administrative mapping outputs so future math and Markdown-extension changes can be ported directly and audited without copying fixtures or treating test counts as proof.

## Notes

Replaced stale full-parity/test-count claims with a living status keyed by released baseline v0.7.2, exact in-progress commit 093c924, schema, change IDs, beads, and exact divergence ledger. Rewrote the QA runbook around clean submodules, Cargo-built binary, direct upstream shared cases/tryscript, package smoke tests, and optional Python only for baseline-transition audits. Added dated sync artifact, corrected historical plan/archive links, and updated the parity lesson. Detected/recorded the 88-commit Rust-main gap as fm-mfvi. Rust commit: 4cdeb64.
