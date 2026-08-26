---
type: is
id: is-01m0y94jg6wy9mh8jwwnt51ncm
title: Merge current flowmark-rs main before preservation implementation
kind: task
status: closed
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
delegate: codex@spud10.local
labels: []
dependencies:
  - type: blocks
    target: is-01m0y8gztfkha3mss2n1wn55f5
parent_id: is-01m0y77hm73p235cm8keb26w2m
created_at: 2026-08-26T05:36:55.300Z
updated_at: 2026-08-26T06:42:13.204Z
closed_at: 2026-08-26T06:42:13.203Z
close_reason: Merged Rust origin/main 015f239 at c6449a5, retained the direct pinned shared-conformance/tryscript design and latest playbook d24760a, repaired the Cargo-authoritative supplemental mapping, regenerated docs, and passed full Rust/admin/docs/package gates. Evidence recorded in flowmark-rs commit 6144051.
resolution: null
duplicate_of: null
---
The preservation-test foundation branch diverged at cb744eb and is 88 commits behind flowmark-rs origin/main 015f239 (v0.3.2, Python v0.7.2 parity). After committing the workflow audit, merge current main, resolve overlapping CI/skill/fixture/test changes in favor of the direct shared-corpus architecture, preserve all current release/security/dependency fixes, regenerate docs, and rerun the full Rust/admin/package gates. This synchronization precedes the remaining v0.7.2-to-v0.7.3 baseline audit.
