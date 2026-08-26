---
type: is
id: is-01m0zvr4pywnx84bq8n8zn6jew
title: Audit all durable Markdown for tbd documentation and comment compliance
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - docs
  - cleanup
  - guidelines
dependencies:
  - type: blocks
    target: is-01m0zvr5089jta3pfz0328589y
parent_id: is-01m0zvnkyqktm79pza59a36k3b
created_at: 2026-08-26T20:21:25.341Z
updated_at: 2026-08-26T20:21:37.999Z
---
Inventory Markdown in both repositories and classify each file as authored durable documentation, generated output, vendored/submodule content, test fixture/golden, or historical evidence. Apply the tbd common documentation guidelines to every governed authored document, not only files changed for this feature.

Require one exact footer at the physical end of each governed Markdown file, no duplicate footer, navigable links from obvious root docs, specific headings, present-state prose, calibrated claims, and no avoidable duplication. Format authored files with Flowmark. Do not rewrite byte-exact fixtures, vendored material, generated artifacts, or preservation inputs; record explicit justified exclusions instead.

Add a deterministic repository check for the footer/inventory policy so compliance does not drift. Apply the tbd general comment rules to source comments touched by documentation generation or validation changes. If the mechanical repository-wide diff is large, keep it in a dedicated commit or PR so the preservation implementation remains reviewable.
