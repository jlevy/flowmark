---
type: is
id: is-01m1npp7kv19ezn34qwcyf3s98
title: Coordinate synchronized release ordering and rollback
kind: task
status: closed
priority: 1
version: 5
labels:
  - release
dependencies:
  - type: blocks
    target: is-01m1npp70ve3p6fyj8n5qt2xx4
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T07:56:17.402Z
updated_at: 2026-09-04T16:03:38.577Z
closed_at: 2026-09-04T11:41:46.542Z
close_reason: "Completed safe synchronized ordering: Python prep merged, Rust prep merged, Rust dry-run green, crate/PyPI/GitHub/Homebrew 0.4.0 published and verified first, then Python 0.8.0 published and verified. All collision checks were clear immediately before mutation; both sibling pins now resolve; no rollback was required."
resolution: null
duplicate_of: null
---
Keep Python 0.8.0 and Rust 0.4.0 pins mutually resolvable, record the immutable Python commit used by Rust, verify no tag or registry collision, sequence publication safely, and retain a stop/rollback decision for every external step.

## Notes

Final order: Python source prep merged first at 7dfd042 so Rust can pin an immutable public commit; publish flowmark-rs 0.4.0 first after its PR/dry-run, then flowmark 0.8.0 immediately afterward. This minimizes the interval in which a published package's skill points at an unavailable sibling version. Cross-channel reruns are idempotent per both runbooks.
