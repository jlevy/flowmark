---
type: is
id: is-01m0y03qynte7p5034zweegvjy
title: Integrate Python preservation into fill_markdown and byte-safe CLI I/O
kind: task
status: open
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y042abxn1c7w256z31w81j
parent_id: is-01m0xn1kf4s20aga85f298dzww
created_at: 2026-08-26T02:59:10.931Z
updated_at: 2026-08-26T02:59:21.545Z
---
Connect the complete protection pipeline at the actual formatting and process boundaries.

Files and functions:
- src/flowmark/linewrapping/markdown_filling.py::fill_markdown(): explicit optional dedent for direct helper use, normalize, scan/protect, preprocess only unprotected gaps, parse/transform/render, validate/restore, and finalize BOM/LF.
- src/flowmark/reformat_api.py::reformat_text(), reformat_file(), and reformat_files(): CLI/library Markdown formatting does not implicitly dedent; file/stdin paths read bytes, decode UTF-8 strictly, write UTF-8 bytes, and preserve the existing atomic output boundary.
- CLI exception handling: pin invalid UTF-8 and internal restoration errors to nonzero status, empty stdout, deterministic stderr, and unchanged in-place files.
- tests/test_filling.py and tests/test_reformat_api.py: a small number of direct-API/dedent and atomic-write failure tests only.

Remove global strip/dedent steps that can mutate a protected document before scanning, while preserving fill_markdown(dedent_input=True) as an explicit docstring convenience applied before normalization. Plaintext behavior stays outside the protection scanner unless a shared case deliberately changes it.

Acceptance: all FM-PRESERVE-CORE-001 and math cases pass against the installed CLI, direct API semantics are documented, and no failure can emit or commit a partial document.
