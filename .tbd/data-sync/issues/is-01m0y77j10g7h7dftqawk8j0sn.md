---
type: is
id: is-01m0y77j10g7h7dftqawk8j0sn
title: Refresh the rust-porting-playbook submodule and audit the official update workflow
kind: task
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
delegate: codex@spud10.local
labels: []
dependencies:
  - type: blocks
    target: is-01m0y77jb7s7xmtm7hrb2z3aed
parent_id: is-01m0y77hm73p235cm8keb26w2m
hold: null
hold_until: null
created_at: 2026-08-26T05:03:35.968Z
updated_at: 2026-08-26T05:41:28.040Z
started_at: 2026-08-26T05:20:51.182Z
closed_at: 2026-08-26T05:41:28.039Z
close_reason: Latest playbook pointer is recorded and the official Flowmark-specific update workflow has been audited, adapted, documented, formatted, link-checked, and committed as da1e96c.
resolution: null
duplicate_of: null
---
Advance repos/rust-porting-playbook from the recorded parent pointer to the newest origin/main commit after verifying the submodule has no local work. Read the current canonical update checklist, sync/release workflow, test-coverage playbook, and relevant Rust rules. Audit Flowmark-rs files and commands against them; record justified Flowmark-specific adaptations, including why shared versioned upstream fixtures supersede copied generated fixtures and why normal Rust CI must not require Python.

## Notes

Updated flowmark-rs rust-porting-playbook gitlink df36b99 -> d24760a after verifying the submodule was clean. Read the current update checklist, sync/release workflow, coverage playbook, Python-to-Rust rules, and Rust testing rules. Replaced the stale operational playbook with a Flowmark adaptation based on direct versioned upstream conformance/tryscript assets, built-binary Rust gates, exact change IDs, and no Python dependency in normal Rust CI. Added the filled current checklist. Audit also found the branch is 88 commits behind Rust main (fm-mfvi), the target Python gitlink is local-only (fm-zah1), and the remaining released baseline audit is v0.7.2..v0.7.3 (fm-t81l). Rust commit: da1e96c.
