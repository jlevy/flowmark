---
type: is
id: is-01m0xsczjbncpddwkvxsehvmsz
title: Review Python code-span goldens and close C1/C2 by shared evidence
kind: task
status: closed
priority: 1
version: 7
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y06s6yse0c28j4fa8mz1vs
parent_id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
created_at: 2026-08-26T01:01:53.611Z
updated_at: 2026-08-26T11:30:17.116Z
closed_at: 2026-08-26T11:30:17.115Z
close_reason: Python code-span goldens reviewed selectively; exact corpus, full tests, and fixed-point workflow pass.
resolution: null
duplicate_of: null
---
Close the Python FM-CODE-SPAN-001 phase by reviewing every affected layer.

Run the exact shared code-span cases, upstream code-inline.md tryscript workflow and second pass, all four reference-document modes, CommonMark documents, repository Markdown, and full lint/test/build. Use selective case-ID acceptance and classify each changed byte as intended source preservation or regression. Pay special attention to spec tables and documentation containing backticks, table cells versus paragraphs/headings, tabs, authored soft line endings, semantic wrapping, and inputs with no protected spans.

Update fm-dq8n and fm-bj2c only when the shared cases prove C1/C2 closed. No broad golden regeneration and no corrupt current output may be accepted as truth. Acceptance: Python is green, idempotent, has no unexplained blast-radius churn, and the exact upstream commit/change IDs are ready for Rust.

## Notes

Reviewed and committed in 921a47e: 29 exact FM-CODE-SPAN-001 cases (7 custom/topic plus CommonMark 328-349). Only CommonMark example 334 changed, deliberately joining the soft line break between two exact code spans. Corrected importer ownership so non-Code-spans backticks remain FM-COMMONMARK and raw HTML remains FM-EXT-RAW-HTML. Full make test passed: 518 pytest and 143 tryscript checks.
