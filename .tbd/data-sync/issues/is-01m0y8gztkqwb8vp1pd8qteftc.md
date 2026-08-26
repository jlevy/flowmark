---
type: is
id: is-01m0y8gztkqwb8vp1pd8qteftc
title: Publish the pinned Python conformance commit before Rust CI
kind: task
status: open
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0y77hm73p235cm8keb26w2m
created_at: 2026-08-26T05:26:13.585Z
updated_at: 2026-08-26T17:58:28.667Z
---
The Rust submodule now pins Python commit b027fde6f8174b9f20ca69fa459ac2a11e0ff483, which is currently available only from the local Flowmark worktree. Publish or merge that exact commit to an upstream ref before opening or validating the Rust PR remotely; then confirm a clean recursive clone can initialize repos/flowmark without a local alternate. Do not replace the exact gitlink with an older published commit merely to make initialization pass.

## Notes

The target advanced from 0d2bebb to b027fde as the preservation contract, corpus regressions, formatting, and shared integration goldens stabilized. The Rust branch pins b027fde exactly and passes every local gate. The earlier clean-clone failure proves unpublished submodule objects are not remotely reproducible; rerun the same proof only after b027fde is published.
