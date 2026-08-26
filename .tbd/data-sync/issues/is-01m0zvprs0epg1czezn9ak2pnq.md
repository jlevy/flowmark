---
type: is
id: is-01m0zvprs0epg1czezn9ak2pnq
title: Write the official supported Markdown and math syntax guide
kind: feature
status: open
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - docs
  - math
  - preservation
dependencies:
  - type: blocks
    target: is-01m0zvq1h1155s9dd7t4k6ffrx
  - type: blocks
    target: is-01m0zvq8ym3ks2e5v80j8wbn5j
  - type: blocks
    target: is-01m0zvr4pywnx84bq8n8zn6jew
  - type: blocks
    target: is-01m0zvrghzj17ra8cg8zpqzncr
parent_id: is-01m0zvnkyqktm79pza59a36k3b
created_at: 2026-08-26T20:20:40.351Z
updated_at: 2026-08-26T20:21:37.470Z
---
Add a durable public guide at a self-evident path such as `docs/supported-markdown.md`. The guide is the detailed human-facing view of the language-neutral support catalog; do not duplicate low-level scanner design or the full test manifest.

Lead with Flowmark's mixed-dialect, little-configuration preservation promise and give math the first detailed section. Show concise valid examples for every math form and explain delimiter matching, code precedence, wrapping as an atomic unit, container behavior, malformed fallback, line-ending/final-newline normalization, and what “source exact” does and does not include.

Organize other syntax by useful buckets: CommonMark and GFM, source-exact inline code, YAML and TOML frontmatter, raw HTML, Pandoc multiline and grid tables, definition and line blocks, fenced divs/colon containers, attribute groups, Obsidian/GitHub-style callouts, MyST roles, wikilinks/embeds, template tags, and related opaque regions. Clearly list known gaps and intentional canonicalizations generated from or checked against the catalog.

Link to the language-neutral conformance documentation for contributors. Follow the common documentation guidelines, use precise present-state prose, include exactly one required footer, run Flowmark, and verify every internal and external link.
