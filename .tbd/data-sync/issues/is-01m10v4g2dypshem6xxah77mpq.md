---
type: is
id: is-01m10v4g2dypshem6xxah77mpq
title: Document the shared Flowmark CLI exit-status contract
kind: task
status: closed
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - docs
  - cli
dependencies: []
parent_id: is-01m0zvnkyqktm79pza59a36k3b
created_at: 2026-08-27T05:29:56.044Z
updated_at: 2026-08-27T05:30:16.184Z
closed_at: 2026-08-27T05:30:16.174Z
close_reason: Added the 0/1/2 parity contract to the canonical shared README source, Flowmark-formatted it to a fixed point, and regenerated the Python README.
resolution: null
duplicate_of: null
---
Document exit statuses 0, 1, and 2 in the canonical shared README source so Python and Rust publish the same operational contract. Regenerate the Python README; the Rust port will consume the exact upstream source and regenerate its README and bundled docs.
