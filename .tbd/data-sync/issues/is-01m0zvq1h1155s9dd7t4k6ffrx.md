---
type: is
id: is-01m0zvq1h1155s9dd7t4k6ffrx
title: Update the shared README feature summary and formatter comparison
kind: task
status: open
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - docs
  - readme
  - comparison
dependencies:
  - type: blocks
    target: is-01m0zvq8ym3ks2e5v80j8wbn5j
  - type: blocks
    target: is-01m0zvqgntxmpx9hsht3bb9a1p
  - type: blocks
    target: is-01m0zvr4pywnx84bq8n8zn6jew
  - type: blocks
    target: is-01m0zvr5089jta3pfz0328589y
parent_id: is-01m0zvnkyqktm79pza59a36k3b
created_at: 2026-08-26T20:20:49.312Z
updated_at: 2026-08-26T20:21:25.639Z
---
Edit the authored shared README body, not the generated Python or Rust README directly. Add a concise, high-visibility feature bucket for broad mixed-dialect preservation, with math first, followed by extended tables/blocks, frontmatter/HTML, roles/wikilinks/callouts, attributes/containers, code spans, and template syntax. Link to the official supported-syntax guide for the complete list and exact treatment.

Revise the existing comparison section from the research brief. Keep the narrative compact; do not add a cell-by-cell feature matrix. Explain Flowmark's differentiator as automatic mixed-dialect preservation with minimal configuration, semantic line breaking, shared Python/Rust behavior, and language-neutral conformance evidence. State competitors' capabilities and plugin requirements accurately and cite primary sources.

Do not say “all Markdown,” “universal,” or “fully source exact” while fm-js19 or fm-n0ww remains open. Regenerate both README artifacts through their existing scripts, confirm generation is idempotent, retain wrapper-specific content, run Flowmark on authored Markdown, and enforce the exact documentation footer rules.
