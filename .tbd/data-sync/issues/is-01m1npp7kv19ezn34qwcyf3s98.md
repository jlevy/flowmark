---
type: is
id: is-01m1npp7kv19ezn34qwcyf3s98
title: Coordinate synchronized release ordering and rollback
kind: task
status: in_progress
priority: 1
version: 3
labels:
  - release
dependencies:
  - type: blocks
    target: is-01m1npp70ve3p6fyj8n5qt2xx4
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T07:56:17.402Z
updated_at: 2026-09-04T07:56:40.893Z
---
Keep Python 0.8.0 and Rust 0.4.0 pins mutually resolvable, record the immutable Python commit used by Rust, verify no tag or registry collision, sequence publication safely, and retain a stop/rollback decision for every external step.
