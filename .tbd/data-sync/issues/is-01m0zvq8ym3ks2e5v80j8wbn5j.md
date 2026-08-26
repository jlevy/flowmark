---
type: is
id: is-01m0zvq8ym3ks2e5v80j8wbn5j
title: Make supported-syntax documentation part of installed flowmark --docs
kind: feature
status: open
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - docs
  - cli
  - packaging
dependencies:
  - type: blocks
    target: is-01m0zvqgntxmpx9hsht3bb9a1p
  - type: blocks
    target: is-01m0zvr4pywnx84bq8n8zn6jew
  - type: blocks
    target: is-01m0zvr5089jta3pfz0328589y
parent_id: is-01m0zvnkyqktm79pza59a36k3b
created_at: 2026-08-26T20:20:56.915Z
updated_at: 2026-08-26T20:21:25.639Z
---
Make the official syntax guide available through Flowmark itself in source checkouts and installed distributions. Today Python `get_docs_content()` reads a repository README and falls back to a short link when that file is absent, while Rust embeds a generated `src/flowmark-docs.md`. Replace this asymmetry with one upstream-authored documentation composition that both ports can generate and package.

Keep the README concise and the syntax guide detailed, but ensure `flowmark --docs` contains or cleanly composes both. The generation design must preserve port-specific installation/API prefaces without copying the support list into two manually maintained files. Generated artifacts need clear ownership markers; authored sources need the required footer.

Add golden tests for source-tree and installed wheel/sdist behavior, generation idempotence, section presence and ordering, and failure on stale generated output. Define the corresponding Rust generation input so the port can embed the same support content without a Python runtime.
