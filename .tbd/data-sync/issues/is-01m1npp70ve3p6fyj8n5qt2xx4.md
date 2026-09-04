---
type: is
id: is-01m1npp70ve3p6fyj8n5qt2xx4
title: Prepare flowmark 0.8.0 release metadata and PR
kind: task
status: closed
priority: 1
version: 4
labels:
  - release
dependencies:
  - type: blocks
    target: is-01m1npp7a9x2vf2ch09tm1542k
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T07:56:16.794Z
updated_at: 2026-09-04T10:13:17.254Z
closed_at: 2026-09-04T10:13:17.253Z
close_reason: "The reviewed and fully green flowmark 0.8.0 release-prep change is merged to main in PR #76."
resolution: null
duplicate_of: null
---
Bump the Python discovery version and synchronized Rust discovery pin to the next minor versions, generate exact release notes from v0.7.3..HEAD, update required documentation, run release-pin checks, commit, push, open the release-prep PR, and land only after all required checks pass.

## Notes

Prepared flowmark 0.8.0 metadata and synchronized discovery pins, committed c8ac85a, pushed codex/release-0.8.0-prep, opened PR #76, and passed all five hosted CI jobs on Python 3.10-3.14. Squash-merged to main as 7dfd0421d483a42dee29edef999f866b04294720. The main branch is clean; the original user workspace remains preserved in stash@{0}.
