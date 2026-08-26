---
type: is
id: is-01m0xsczjbncpddwkvxsehvmsz
title: Survey and regenerate the goldens the Track C fixes change
kind: task
status: open
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
created_at: 2026-08-26T01:01:53.611Z
updated_at: 2026-08-26T01:02:17.779Z
---
The Track C fixes change output for any document with multiple spaces inside a code span, or a wide delimiter around content containing backticks. Survey before assuming the blast radius is small.

Known in advance:
- tests/tryscript/fixtures/content/code-inline.md — the corpus itself.
- tests/testdocs/testdoc.orig.md and its four expected files — check for code spans with internal runs.
- tests/tryscript/fixtures/content/comprehensive.md — already the one fixture that differs between the Python and Rust repos, so re-check both after regenerating.

Method: run the formatter over each fixture before and after the fixes, diff, and classify every change as either "the fix working" or "a regression". Do not regenerate goldens wholesale without reading the diff; the point of the survey is that a golden refresh hides exactly the class of bug this phase exists to fix.

Also re-check the flowmark repo's own Markdown, since `make format` runs flowmark over the tree and any doc quoting backticks inside a wide delimiter will shift once.
