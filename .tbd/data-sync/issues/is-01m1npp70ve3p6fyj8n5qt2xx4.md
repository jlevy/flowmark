---
type: is
id: is-01m1npp70ve3p6fyj8n5qt2xx4
title: Prepare flowmark 0.8.0 release metadata and PR
kind: task
status: open
priority: 1
version: 2
labels:
  - release
dependencies:
  - type: blocks
    target: is-01m1npp7a9x2vf2ch09tm1542k
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T07:56:16.794Z
updated_at: 2026-09-04T07:56:33.312Z
---
Bump the Python discovery version and synchronized Rust discovery pin to the next minor versions, generate exact release notes from v0.7.3..HEAD, update required documentation, run release-pin checks, commit, push, open the release-prep PR, and land only after all required checks pass.
