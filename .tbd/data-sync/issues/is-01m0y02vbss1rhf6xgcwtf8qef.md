---
type: is
id: is-01m0y02vbss1rhf6xgcwtf8qef
title: Implement the Python collision-safe bridge and parser adapter
kind: task
status: in_progress
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y03afg7925xv1gk4v82zxw
parent_id: is-01m0xn1kf4s20aga85f298dzww
created_at: 2026-08-26T02:58:41.654Z
updated_at: 2026-08-26T08:48:11.631Z
---
Carry typed source regions through Marko without asking Marko to recognize their syntax.

Files and functions:
- src/flowmark/preservation/bridge.py: choose_sentinel(), encode_token(), protect_source(), parse_token(), and restore_source().
- src/flowmark/formats/flowmark_markdown.py: add thin protected-inline and opaque-block element/renderer hooks to CustomParser/MarkdownNormalizer; render_raw_text(), render_paragraph(), render_heading(), and table-cell paths must carry tokens intact.
- src/flowmark/transforms/doc_transforms.py and doc_cleanups walkers: skip protected nodes/tokens.
- tests/test_preservation_bridge.py: collision selection, parser round-trip, missing/duplicate/reordered/malformed token failures, and no-sentinel-remains invariants only.

Use the deterministic supplementary-PUA sentinel and base-36 token contract in the spec. Restoration validates the entire token stream before returning any output and fails closed. Protected source remains in a side table; it is not escaped into Markdown or reconstructed from the AST.

Acceptance: Marko cannot reinterpret parser-collision bodies, every shared sentinel case passes, and injected invariant failures produce no partial output.
