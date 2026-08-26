---
type: is
id: is-01m0xscdmzyb7m84p8mtscn2j5
title: Route Python code spans through exact restoration and token-aware wrapping
kind: task
status: open
priority: 1
version: 6
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0xsczjbncpddwkvxsehvmsz
  - type: blocks
    target: is-01m0xse38rtqj4zy9m2k5f1awj
  - type: blocks
    target: is-01m0xn1zcv01nmb6qgtw0nsf1z
parent_id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
created_at: 2026-08-26T01:01:35.262Z
updated_at: 2026-08-26T03:00:29.932Z
---
Complete the Python side of FM-CODE-SPAN-001 using the existing protection pipeline.

Files and functions:
- src/flowmark/linewrapping/markdown_filling.py::fill_markdown(): include code_span regions in protection before Marko.
- src/flowmark/formats/flowmark_markdown.py::render_code_span(): becomes a fallback for unprotected/parser-created spans; it is not authoritative for recognized source spans.
- src/flowmark/linewrapping/text_wrapping.py and line_wrappers.py: preserve code token gaps, adjacency, tabs, spaces, and authored internal line endings exactly.
- src/flowmark/transforms/doc_transforms.py and typography: skip code tokens through the same typed mechanism.
- tests/test_preservation_bridge.py/test_wrapping.py: only native failure or width diagnostics not expressed by shared cases.

Do not use pre-token re.sub whitespace collapse, iter_atomic_spans as the new scanner, or CommonMark's rendered-content normalization as the formatter policy. Acceptance: C2 and second-pass drift are eliminated in every context and all FM-CODE-SPAN-001 cases pass exact bytes.
