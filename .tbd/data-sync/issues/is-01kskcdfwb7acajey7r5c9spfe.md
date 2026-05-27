---
type: is
id: is-01kskcdfwb7acajey7r5c9spfe
title: "Phase A: fix iter_inline contract (inline-only vs generic walk)"
kind: task
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-05-26-public-inline-api.md
labels: []
dependencies:
  - type: blocks
    target: is-01kskcdg67dmmypqwkjkh71064
  - type: blocks
    target: is-01kskcdgm1nhs4p39s366cnc85
parent_id: is-01kskcc95bk93gn9mz8x57c13z
created_at: 2026-05-27T00:12:41.739Z
updated_at: 2026-05-27T00:12:53.513Z
---
Review #4: iter_inline yields EVERY descendant with list children, incl. block elements, blank lines, and RawText inside fenced code blocks - surprising for a helper named iter_inline and risks treating code-block content as inline. Either rename to a generic tree iterator or constrain to inline scopes and skip code-block bodies. Update extract_links to match the chosen contract.
