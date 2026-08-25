---
type: is
id: is-01m0xn1zcv01nmb6qgtw0nsf1z
title: Code span interiors lose whitespace, progressively and non-idempotently
kind: bug
status: open
priority: 1
version: 1
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
created_at: 2026-08-25T23:45:58.683Z
updated_at: 2026-08-25T23:45:58.683Z
---
Backtick a-four-spaces-b becomes a-one-space-b: 6 bytes of interior become 3. Backtick two-spaces-a-two-spaces is worse and not idempotent: it loses one space per pass for two passes before settling, and the rendered content changes too, not just the source. Per CommonMark 0.31.2 section 6.1 a code span converts line endings to spaces and strips one leading and trailing space if both present, but internal runs are significant. Cause is ordering, not intent: the paragraph-level whitespace normalisation in wrap_paragraph_lines runs before atomic protection. No test pins current behaviour. This is M5 in the spec and a precondition for math spans being byte-exact by the same code path rather than a special stricter one. Adjacent to but distinct from issue 58.
