---
type: is
id: is-01m0zvnkyqktm79pza59a36k3b
title: "Documentation: publish Flowmark's cross-dialect Markdown and math support"
kind: epic
status: open
priority: 1
version: 15
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
  - is-01m10ntxm4570ja5wmb0zk7t7q
  - is-01m10v4g2dypshem6xxah77mpq
created_at: 2026-08-26T20:20:02.645Z
updated_at: 2026-08-27T05:29:56.044Z
---
Turn the preservation work in Python PR #71 and Rust PR #81 into one accurate, maintainable public documentation system. State two levels of support. The baseline practical contract says common CommonMark, GFM, and GLFM forms and registered extensions are safe in mixed documents with little configuration: meaning and content survive, output reaches a fixed point, and Python/Rust agree. CommonMark compatibility is mandatory across all 652 examples. Reviewed Flowmark line wrapping and canonicalization are expected; source-exact treatment is selective for opaque or fragile syntax, and every actual gap remains explicit. Public docs must give math highest visibility, list supported syntax in an official guide, summarize the differentiator in the README without a giant matrix, and lead with common/high-impact gaps before rare spelling differences. Claims distinguish source-exact protection, intentional normalization, formatter-owned Markdown, safe fallback, and known gaps. Use the shared corpus and language-neutral catalog as evidence. Python and Rust consume the same authored content, installed docs remain useful, and all governed Markdown follows common documentation/footer rules and Flowmark formatting.
