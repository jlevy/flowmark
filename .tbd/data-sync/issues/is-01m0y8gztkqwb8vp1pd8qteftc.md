---
type: is
id: is-01m0y8gztkqwb8vp1pd8qteftc
title: Publish the pinned Python conformance commit before Rust CI
kind: task
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0y77hm73p235cm8keb26w2m
created_at: 2026-08-26T05:26:13.585Z
updated_at: 2026-08-26T10:48:27.480Z
---
The Rust submodule pins Python commit 0d2bebb0fabb9ad8705ac797687f96335ca7cfe7, which is currently available only from the local Flowmark worktree. Push or merge that exact commit to an upstream ref before opening or validating the Rust PR remotely; then confirm a clean clone can initialize repos/flowmark without a local alternate. Do not replace the exact gitlink with an older published commit merely to make initialization pass.
