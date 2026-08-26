---
type: is
id: is-01m0zvnkyqktm79pza59a36k3b
title: "Documentation: publish Flowmark's cross-dialect Markdown and math support"
kind: epic
status: open
priority: 1
version: 10
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - docs
  - preservation
  - parity
dependencies: []
child_order_hints:
  - is-01m0zvpft5b6ft59jdxv76yc7b
  - is-01m0zvpg8vydyae76y3wg9x5gr
  - is-01m0zvprs0epg1czezn9ak2pnq
  - is-01m0zvq1h1155s9dd7t4k6ffrx
  - is-01m0zvq8ym3ks2e5v80j8wbn5j
  - is-01m0zvqgntxmpx9hsht3bb9a1p
  - is-01m0zvr4pywnx84bq8n8zn6jew
  - is-01m0zvr5089jta3pfz0328589y
  - is-01m0zvrghzj17ra8cg8zpqzncr
created_at: 2026-08-26T20:20:02.645Z
updated_at: 2026-08-26T20:21:37.470Z
---
Turn the preservation work in Python PR #71 and Rust PR #81 into one accurate, maintainable public documentation system.

The public contract must explain that Flowmark handles mixed Markdown dialects with little or no configuration, give math the highest visibility, list every supported syntax in an official guide, and summarize the differentiator in the README without a giant feature matrix. Claims must distinguish source-exact opaque preservation, intentional normalization, formatter-owned Markdown, safe fallback, and known gaps.

Use the upstream shared corpus and a language-neutral support catalog as evidence. The Python and Rust builds must consume the same authored support content, and installed `flowmark --docs` output must remain useful outside a source checkout. All authored Markdown must follow the tbd common documentation guidelines, end with exactly one required footer unless it is a justified generated artifact, and be formatted with Flowmark. Code comments touched by the work must follow the tbd general comment rules.
