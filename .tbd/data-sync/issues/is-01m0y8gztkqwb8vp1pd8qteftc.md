---
type: is
id: is-01m0y8gztkqwb8vp1pd8qteftc
title: Publish the pinned Python conformance commit before Rust CI
kind: task
status: closed
priority: 1
version: 6
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0y77hm73p235cm8keb26w2m
created_at: 2026-08-26T05:26:13.585Z
updated_at: 2026-08-26T18:17:15.127Z
closed_at: 2026-08-26T18:17:15.114Z
close_reason: Published Python b027fde on the PR branch and verified a fresh shallow recursive clone of the published Rust branch resolved Python b027fde, playbook d24760a, and Homebrew 6567a9f from their configured remotes without local alternates.
resolution: null
duplicate_of: null
---
The Rust submodule now pins Python commit b027fde6f8174b9f20ca69fa459ac2a11e0ff483, which is currently available only from the local Flowmark worktree. Publish or merge that exact commit to an upstream ref before opening or validating the Rust PR remotely; then confirm a clean recursive clone can initialize repos/flowmark without a local alternate. Do not replace the exact gitlink with an older published commit merely to make initialization pass.

## Notes

The target advanced from 0d2bebb to b027fde as the preservation contract, corpus regressions, formatting, and shared integration goldens stabilized. The Rust branch pins b027fde exactly and passes every local gate. The earlier clean-clone failure proves unpublished submodule objects are not remotely reproducible; rerun the same proof only after b027fde is published.
