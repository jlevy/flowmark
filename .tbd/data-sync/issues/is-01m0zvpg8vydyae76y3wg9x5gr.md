---
type: is
id: is-01m0zvpg8vydyae76y3wg9x5gr
title: Research competing formatter support for Markdown dialects and math
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - docs
  - research
  - comparison
dependencies:
  - type: blocks
    target: is-01m0zvq1h1155s9dd7t4k6ffrx
parent_id: is-01m0zvnkyqktm79pza59a36k3b
created_at: 2026-08-26T20:20:31.642Z
updated_at: 2026-08-26T20:20:49.312Z
---
Write a dated research brief using current primary sources and pinned tool versions for the formatters already discussed in Flowmark's README: dprint's Markdown plugin, markdownfmt, mdformat, Prettier, markdownlint-cli2, and the remark ecosystem. Add another directly relevant formatter only if it changes the positioning.

Compare at feature-bucket level rather than building a giant marketing matrix: default CommonMark/GFM/MDX scope, math forms, extension/dialect breadth, whether plugins or configuration are required, preservation of unknown syntax, formatting versus linting, and source-exact versus AST reserialization behavior. Where public docs are insufficient, run a small reproducible fixture battery containing Flowmark's representative syntax families and record exact versions and commands.

Use calibrated language and cite every external capability claim. Current primary-source starting points include Prettier's CommonMark/GFM/MDX documentation and 3.9 parser notes, mdformat's CommonMark-by-default and extension-plugin docs, dprint's pulldown-cmark-based plugin docs/source, and remark's explicit GFM/frontmatter/math/directive plugin model.
