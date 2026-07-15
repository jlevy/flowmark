---
type: is
id: is-01kxhzp7wpw4gr21zca69yeqfm
title: Align Flowmark skill ownership across Python and Rust PRs
kind: task
status: closed
priority: 1
version: 3
labels: []
dependencies: []
created_at: 2026-07-15T04:13:49.844Z
updated_at: 2026-07-15T04:30:17.079Z
closed_at: 2026-07-15T04:30:17.078Z
close_reason: Aligned jlevy/flowmark#64 and jlevy/flowmark-rs#78 around one public Flowmark skill, added tested Rust runtime-mirror sync and CI checks, pushed both branches, and confirmed all checks pass.
---
Make jlevy/flowmark#64 the canonical skill installation and documentation source while keeping jlevy/flowmark-rs#78 sensibly aligned as the recommended Rust implementation. Audit duplicated artifacts, update both PRs, test, push, and verify CI.
