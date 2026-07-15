---
type: is
id: is-01kxhn6bcdrbdpqjqqjte7esne
title: "PR #78 review F78-1: include optional Markdown extensions in hook examples"
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01kxhn6b32q7kt5fahacwq37gx
created_at: 2026-07-15T01:10:23.372Z
updated_at: 2026-07-15T01:16:32.876Z
closed_at: 2026-07-15T01:16:32.875Z
close_reason: "Fixed in 331b298: both commit-hook selectors cover .md, .mdc, and .markdown, with a drift test."
---
Cursor Bugbot finding at src/skills/references/project-setup.md:67. Align the Lefthook and pre-commit examples with documented .mdc and .markdown support so --extend-include users do not silently skip those staged files.
