---
type: is
id: is-01m0xsc02hwk2b4xnmww9869yk
title: Recognize source-exact inline code spans in the Python pre-parse scanner
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
    target: is-01m0xpsyq253tk2p90pq8vsz7c
  - type: blocks
    target: is-01m0xscdmzyb7m84p8mtscn2j5
parent_id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
created_at: 2026-08-26T01:01:21.349Z
updated_at: 2026-08-26T03:00:30.393Z
---
Extend the established Python preservation scanner for FM-CODE-SPAN-001 after its shared cases are red.

Files and functions:
- src/flowmark/preservation/scanner.py::scan_backtick_runs() and arbitrate_candidates(): match an opener with the next run of exactly the same length within the inline scope and apply the specified same-start priority with GitLab/MyST math.
- src/flowmark/preservation/registry.py: register code_span without changing public MARKDOWN_INLINE_PATTERNS or ATOMIC_PATTERNS.
- tests/test_preservation_scanner.py: only focused run-length, overlap, and unmatched diagnostics.

The recognized region owns the exact authored opening run, body, and closing run. Do not shorten a safe wide delimiter, reconstruct padding, or delegate source fidelity to MarkdownNormalizer.render_code_span(). Unmatched runs remain ordinary source.

Acceptance: delimiter corruption C1 is eliminated in all shared contexts, composite-math arbitration is unchanged, and scanner work remains linear.
