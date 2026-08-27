---
type: is
id: is-01m0zvpft5b6ft59jdxv76yc7b
title: Define a language-neutral Markdown syntax support catalog
kind: feature
status: open
priority: 1
version: 8
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
updated_at: 2026-08-27T04:08:52.992Z
---
Create a versioned, language-neutral source of truth for public support claims alongside the shared corpus, not in Python code. Give every syntax a stable ID, name, dialect/spec provenance, treatment class, support status, priority, and active conformance case IDs or an open gap bead. Model both contract levels: practical support requires semantic safety, fixed point, and Python/Rust parity; CommonMark review additionally records compatible Flowmark formatting, selective source-exact treatment, or an open gap. Cover ordinary CommonMark, GFM, and GLFM buckets first, then every preserved extension family. Enumerate math forms individually: dollar forms, paren/bracket forms, GitLab dollar-backtick, MyST roles/fences, and nested/starred/custom environments. Use explicit statuses for formatter-owned, source-exact protected, intentionally normalized, safe fallback, and unsupported/known gap. Add language-neutral schema and referential-integrity checks that reject duplicate IDs, dangling evidence, claims backed only by deferred cases, and gap statuses without open beads. Reports must distinguish semantic, fixed-point, parity, and source-fidelity evidence and prioritize common/high-impact gaps.
