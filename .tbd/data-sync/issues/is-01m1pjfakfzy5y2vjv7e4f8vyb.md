---
type: is
id: is-01m1pjfakfzy5y2vjv7e4f8vyb
title: Upgrade local Flowmark CLI to flowmark-rs 0.4.0
kind: task
status: closed
priority: 2
version: 6
labels: []
dependencies: []
created_at: 2026-09-04T16:01:51.208Z
updated_at: 2026-09-04T19:02:32.227Z
closed_at: 2026-09-04T19:02:32.210Z
close_reason: "Completed replacement after correcting the initially missed Cargo shadow: uninstalled Cargo flowmark v0.3.2 and both stale binaries, force-installed exact prebuilt flowmark-rs 0.4.0 as a uv global tool, confirmed uv symlink ownership and PATH precedence, and passed version and formatting smoke checks. No repository files changed."
resolution: null
duplicate_of: null
---
Replace the shell-visible local Flowmark executable with the exact flowmark-rs 0.4.0 release and verify version, provenance path, and formatting behavior. The user explicitly authorized this newly published maintained release as a narrow cool-off exception after its release artifacts and checksums were validated.

## Notes

Reopened: The initial close was premature: the user's interactive Finterm shell resolves the stale Cargo-installed 0.3.2-dev executable ahead of uv's global tool directory. Reopening to remove old Cargo binaries and complete uv-global PATH verification.
