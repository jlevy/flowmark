---
type: is
id: is-01m0y8gztkqwb8vp1pd8qteftc
title: Publish the pinned Python conformance commit before Rust CI
kind: task
status: open
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0y77hm73p235cm8keb26w2m
created_at: 2026-08-26T05:26:13.585Z
updated_at: 2026-08-26T10:38:17.903Z
---
The Rust submodule pins Python commit 2363d8c512d05194a64b9bae92920efc1cfcc4ee, which is currently available only from the local Flowmark worktree. Push or merge that exact commit to an upstream ref before opening or validating the Rust PR remotely; then confirm a clean clone can initialize repos/flowmark without a local alternate. Do not replace the exact gitlink with an older published commit merely to make initialization pass.
