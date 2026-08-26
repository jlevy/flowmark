---
type: is
id: is-01m0xsczjbncpddwkvxsehvmsz
title: Review Python code-span goldens and close C1/C2 by shared evidence
kind: task
status: open
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y06s6yse0c28j4fa8mz1vs
parent_id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
created_at: 2026-08-26T01:01:53.611Z
updated_at: 2026-08-26T03:37:06.204Z
---
Close the Python FM-CODE-SPAN-001 phase by reviewing every affected layer.

Run the exact shared code-span cases, upstream code-inline.md tryscript workflow and second pass, all four reference-document modes, CommonMark documents, repository Markdown, and full lint/test/build. Use selective case-ID acceptance and classify each changed byte as intended source preservation or regression. Pay special attention to spec tables and documentation containing backticks, table cells versus paragraphs/headings, tabs, authored soft line endings, semantic wrapping, and inputs with no protected spans.

Update fm-dq8n and fm-bj2c only when the shared cases prove C1/C2 closed. No broad golden regeneration and no corrupt current output may be accepted as truth. Acceptance: Python is green, idempotent, has no unexplained blast-radius churn, and the exact upstream commit/change IDs are ready for Rust.

## Notes

Owns activation of the exact upstream code-inline.md full-output tryscript workflow and its second-pass check; do not accept a pre-fix corrupt baseline.
