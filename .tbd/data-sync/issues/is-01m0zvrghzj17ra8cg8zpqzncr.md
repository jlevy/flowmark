---
type: is
id: is-01m0zvrghzj17ra8cg8zpqzncr
title: Integrate syntax support into project navigation and contributor workflow
kind: task
status: open
priority: 2
version: 4
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - docs
  - contributors
  - conformance
dependencies:
  - type: blocks
    target: is-01m0zvqgntxmpx9hsht3bb9a1p
  - type: blocks
    target: is-01m0zvr4pywnx84bq8n8zn6jew
  - type: blocks
    target: is-01m0zvr5089jta3pfz0328589y
parent_id: is-01m0zvnkyqktm79pza59a36k3b
created_at: 2026-08-26T20:21:37.470Z
updated_at: 2026-08-26T20:21:46.177Z
---
Update `docs/docs-overview.md`, the language-neutral conformance architecture document, and `tests/parity_corpus/README.md` so maintainers can discover the official syntax guide, understand the support catalog, and add or change a syntax without creating Python/Rust drift.

Document the vertical workflow: define treatment and status, add language-neutral desired-output cases, validate catalog references, implement Python, port from the same change and case IDs, run both native runners, update public claims, and record intentional normalization or an open gap. Keep runtime usage in the public guide and contributor mechanics in contributor docs; link instead of duplicating.

Update the corresponding flowmark-rs docs overview/port workflow during the Rust synchronization bead. Apply the exact footer policy, Flowmark formatting, and link validation to every edited authored document.
