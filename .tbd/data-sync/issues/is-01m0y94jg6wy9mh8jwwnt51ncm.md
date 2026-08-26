---
type: is
id: is-01m0y94jg6wy9mh8jwwnt51ncm
title: Merge current flowmark-rs main before preservation implementation
kind: task
status: in_progress
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
delegate: codex@spud10.local
labels: []
dependencies: []
parent_id: is-01m0y77hm73p235cm8keb26w2m
created_at: 2026-08-26T05:36:55.300Z
updated_at: 2026-08-26T05:42:07.311Z
---
The preservation-test foundation branch diverged at cb744eb and is 88 commits behind flowmark-rs origin/main 015f239 (v0.3.2, Python v0.7.2 parity). After committing the workflow audit, merge current main, resolve overlapping CI/skill/fixture/test changes in favor of the direct shared-corpus architecture, preserve all current release/security/dependency fixes, regenerate docs, and rerun the full Rust/admin/package gates. This synchronization precedes the remaining v0.7.2-to-v0.7.3 baseline audit.
