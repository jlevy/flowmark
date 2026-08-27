---
type: is
id: is-01m0zvprs0epg1czezn9ak2pnq
title: Write the official supported Markdown and math syntax guide
kind: feature
status: open
priority: 1
version: 7
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
updated_at: 2026-08-27T04:02:07.076Z
---
Add a durable public guide such as docs/supported-markdown.md as the human-facing view of the language-neutral support catalog. Lead with Flowmark's mixed-dialect, little-configuration practical support contract and give math the first detailed section. Explain that baseline support means preserved meaning/content, fixed-point output, and Python/Rust parity; strict CommonMark fidelity separately pursues source-exact spelling or documents intentional normalization. Show concise examples for every math form and explain matching, code precedence, atomic wrapping, containers, malformed fallback, and normalization boundaries. Organize other syntax by common CommonMark, GFM, and GLFM buckets first, then frontmatter, raw HTML, Pandoc tables, definitions/line blocks, containers/attributes, callouts, MyST, wikilinks/embeds, templates, and other opaque regions. List high-impact/common gaps before rare equivalent-spelling differences and generate or check them against the catalog. Link contributor conformance docs, follow common documentation/footer rules, run Flowmark, and verify links.
