---
type: is
id: is-01kskcdg67dmmypqwkjkh71064
title: "Phase A: fix extract_links Url/AutoLink branch + span-recovery docs"
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-05-26-public-inline-api.md
labels: []
dependencies:
  - type: blocks
    target: is-01kskcdgm1nhs4p39s366cnc85
parent_id: is-01kskcc95bk93gn9mz8x57c13z
created_at: 2026-05-27T00:12:42.054Z
updated_at: 2026-05-27T00:12:53.801Z
---
Review #6 + design note: gfm Url subclasses inline.AutoLink, so the Url branch is effectively dead under current ordering - fix branch order and docstring to reflect marko's model. Also soften ast.py docstring: span recovery is a chopdiff-level source-mapping problem (duplicate link text, reference links, escaped text, nested inline markup), NOT just 'locate the link text'.
