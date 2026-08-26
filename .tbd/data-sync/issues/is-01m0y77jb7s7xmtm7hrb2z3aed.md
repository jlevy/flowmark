---
type: is
id: is-01m0y77jb7s7xmtm7hrb2z3aed
title: Rebuild Flowmark-rs port status and sync records around shared change IDs
kind: task
status: open
priority: 1
version: 1
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0y77hm73p235cm8keb26w2m
created_at: 2026-08-26T05:03:36.294Z
updated_at: 2026-08-26T05:03:36.294Z
---
Replace stale version/test-count parity claims with a living record keyed by the pinned Python submodule commit, shared schema version, change IDs, Rust beads, exact known-divergence entries, and validation commands. Revise docs/port-sync-playbook.md, docs/port-status.md, the active sync plan, QA guidance, and administrative mapping outputs so future math and Markdown-extension changes can be ported directly and audited without copying fixtures or treating test counts as proof.
