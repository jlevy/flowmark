---
type: is
id: is-01m0y77j10g7h7dftqawk8j0sn
title: Refresh the rust-porting-playbook submodule and audit the official update workflow
kind: task
status: open
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y77jb7s7xmtm7hrb2z3aed
parent_id: is-01m0y77hm73p235cm8keb26w2m
created_at: 2026-08-26T05:03:35.968Z
updated_at: 2026-08-26T05:03:36.294Z
---
Advance repos/rust-porting-playbook from the recorded parent pointer to the newest origin/main commit after verifying the submodule has no local work. Read the current canonical update checklist, sync/release workflow, test-coverage playbook, and relevant Rust rules. Audit Flowmark-rs files and commands against them; record justified Flowmark-specific adaptations, including why shared versioned upstream fixtures supersede copied generated fixtures and why normal Rust CI must not require Python.
