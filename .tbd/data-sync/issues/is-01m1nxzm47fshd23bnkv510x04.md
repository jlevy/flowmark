---
type: is
id: is-01m1nxzm47fshd23bnkv510x04
title: Add shared code-span setext boundary contract
kind: task
status: closed
priority: 1
version: 3
labels:
  - release
  - parity
dependencies: []
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T10:03:45.158Z
updated_at: 2026-09-04T10:03:51.071Z
closed_at: 2026-09-04T10:03:51.068Z
close_reason: Shared Python source contract and cross-port provenance are complete in the synchronized release prep.
resolution: null
duplicate_of: null
---
Record the Python reference output for a code span adjacent to a setext-heading boundary as FM-CODE-SPAN-002. The case was discovered by the synchronized release differential review: Python and Rust v0.3.2 end the inline scope at the block boundary, while the pre-release Rust scanner regressed. Prove the Python case reaches a fixed point and connect it to the Rust fmr-4phz fix in the shared traceability map.

## Notes

FM-CODE-SPAN-002 is committed in Python PR #76. Current Python passes the exact case twice; Rust failed before fmr-4phz and passes after the setext-aware scanner fix. The Rust shared change-ID map now records both owners.
