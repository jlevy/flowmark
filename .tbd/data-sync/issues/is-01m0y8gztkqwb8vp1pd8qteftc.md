---
type: is
id: is-01m0y8gztkqwb8vp1pd8qteftc
title: Publish the pinned Python conformance commit before Rust CI
kind: task
status: open
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0y77hm73p235cm8keb26w2m
created_at: 2026-08-26T05:26:13.585Z
updated_at: 2026-08-26T11:01:21.070Z
---
The Rust submodule pins Python commit 0d2bebb0fabb9ad8705ac797687f96335ca7cfe7, which is currently available only from the local Flowmark worktree. Push or merge that exact commit to an upstream ref before opening or validating the Rust PR remotely; then confirm a clean clone can initialize repos/flowmark without a local alternate. Do not replace the exact gitlink with an older published commit merely to make initialization pass.

## Notes

A fresh recursive clone of flowmark-rs c8ec803 used the configured GitHub submodule URL and failed with upload-pack: not our ref 0d2bebb0fabb9ad8705ac797687f96335ca7cfe7. An exact-SHA fetch in the existing checkout was a false positive because the object was already local. Publish or merge that exact Python commit, then rerun a fresh recursive clone; do not substitute an older gitlink.
