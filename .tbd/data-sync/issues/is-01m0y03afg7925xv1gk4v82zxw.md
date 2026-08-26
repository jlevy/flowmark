---
type: is
id: is-01m0y03afg7925xv1gk4v82zxw
title: Make Python wrapping and transforms protected-token aware
kind: task
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y03qynte7p5034zweegvjy
  - type: blocks
    target: is-01m0yfybntamn9fw3nefnr2fpt
parent_id: is-01m0xn1kf4s20aga85f298dzww
created_at: 2026-08-26T02:58:57.125Z
updated_at: 2026-08-26T09:15:13.036Z
closed_at: 2026-08-26T09:15:13.035Z
close_reason: Implemented structured token fragments/clusters, source-side scalar width accounting, authored-LF column resets, immutable built-in wrapper binding, and diagnostic wrapping tests in the current commit; 516 pytest tests and all lint/type gates pass.
resolution: null
duplicate_of: null
---
Teach existing formatting stages to preserve token boundaries and use side-table widths.

Files and functions:
- src/flowmark/linewrapping/text_wrapping.py: replace whitespace-only word reconstruction for protected content with structured fragments/clusters in _HtmlMdWordSplitter and wrap_paragraph_lines().
- src/flowmark/linewrapping/line_wrappers.py: both width and semantic no-wrap branches must preserve protected fragments.
- src/flowmark/formats/flowmark_markdown.py: render_paragraph(), render_heading(), render_table_cell(), render_line_break(), and inline accumulation must pass bridge metadata consistently.
- src/flowmark/transforms/doc_transforms.py, typography/smartquotes.py, and typography/ellipses.py: protected tokens are opaque.
- tests/test_wrapping.py plus tests/test_preservation_bridge.py: only native diagnostics for source adjacency, logical widths, and authored internal-LF column resets.

Do not approximate width with token text length and do not normalize by joining all fragments with one space. A no-whitespace token boundary forms one unbreakable cluster; a multiline inline token retains every authored internal LF and subsequent column. Existing public iter_atomic_spans/iter_atomic_words behavior remains unchanged.

Acceptance: N-1/N/N+1, intraword, transforms, width 0/1, semantic mode, and multiline cases match exact shared outputs with no token leakage.
