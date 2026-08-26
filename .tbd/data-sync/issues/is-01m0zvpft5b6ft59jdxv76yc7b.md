---
type: is
id: is-01m0zvpft5b6ft59jdxv76yc7b
title: Define a language-neutral Markdown syntax support catalog
kind: feature
status: open
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - docs
  - conformance
  - parity
dependencies:
  - type: blocks
    target: is-01m0zvprs0epg1czezn9ak2pnq
  - type: blocks
    target: is-01m0zvq1h1155s9dd7t4k6ffrx
  - type: blocks
    target: is-01m0zvr5089jta3pfz0328589y
  - type: blocks
    target: is-01m0zvrghzj17ra8cg8zpqzncr
parent_id: is-01m0zvnkyqktm79pza59a36k3b
created_at: 2026-08-26T20:20:31.165Z
updated_at: 2026-08-26T20:21:37.470Z
---
Create a versioned, language-neutral source of truth for public support claims, preferably alongside the shared parity corpus rather than in Python code. Give every syntax a stable identifier, display name, dialect or specification provenance, treatment class, support status, and one or more active conformance case IDs or an open gap bead.

Use a small explicit vocabulary: formatter-owned, source-exact protected region, intentionally normalized boundary, safe fallback, and unsupported/known gap. Include all standard Markdown/GFM buckets and every preserved extension family. Enumerate math forms individually: single- and double-dollar inline forms, multiline double-dollar display, `\(...\)`, `\[...\]`, GitLab dollar-backtick forms with arbitrary matching backtick runs, MyST `{math}` roles, fenced math, and nested/starred/custom LaTeX environments.

Add executable schema and referential-integrity checks that reject duplicate syntax IDs, dangling case/change IDs, claims backed only by deferred cases, and statuses that lack evidence or an open bead. The checker must be runnable without importing Flowmark and consumable by both Python and Rust workflows.
