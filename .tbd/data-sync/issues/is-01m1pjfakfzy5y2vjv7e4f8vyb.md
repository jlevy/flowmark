---
type: is
id: is-01m1pjfakfzy5y2vjv7e4f8vyb
title: Upgrade local Flowmark CLI to flowmark-rs 0.4.0
kind: task
status: closed
priority: 2
version: 3
labels: []
dependencies: []
created_at: 2026-09-04T16:01:51.208Z
updated_at: 2026-09-04T16:03:32.540Z
closed_at: 2026-09-04T16:03:32.521Z
close_reason: Replaced the PATH-leading uv tool installation with exact prebuilt flowmark-rs 0.4.0; both entry points report the synchronized 0.4.0/0.8.0 identity and a formatter smoke test passed.
resolution: null
duplicate_of: null
---
Replace the shell-visible local Flowmark executable with the exact flowmark-rs 0.4.0 release and verify version, provenance path, and formatting behavior. The user explicitly authorized this newly published maintained release as a narrow cool-off exception after its release artifacts and checksums were validated.
