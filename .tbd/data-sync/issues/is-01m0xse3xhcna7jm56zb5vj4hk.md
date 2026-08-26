---
type: is
id: is-01m0xse3xhcna7jm56zb5vj4hk
title: Implement the Python container-aware block scanner and math blocks
kind: task
status: in_progress
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y02vbss1rhf6xgcwtf8qef
parent_id: is-01m0xn1kf4s20aga85f298dzww
created_at: 2026-08-26T01:02:30.833Z
updated_at: 2026-08-26T08:15:06.194Z
---
Implement FM-MATH-BLOCK-001 as a pre-parse source scanner, not in block_heuristics.py and not as a parser-specific workaround.

Files and functions:
- src/flowmark/preservation/scanner.py: build_container_view(), scan_existing_opaque_blocks(), scan_display_math(), scan_environment_blocks(), compatible_container(), and resolve_candidate_tree().
- src/flowmark/preservation/registry.py: block precedence for frontmatter, fenced/indented code, display math, and future extension rules.
- tests/test_preservation_scanner.py: only container-column, nesting-stack, mismatch, fallback, and byte-range diagnostics that are not clearer as shared cases.

Parse blockquote markers and list content columns while retaining raw byte ranges. Existing fenced/indented code and leading frontmatter win before math. Commit only legally closed dollar/bracket/environment blocks; an unmatched outer opener cannot swallow the suffix, and completed nested candidates survive where specified. Preserve raw prefixes, labels, attributes, tabs, blank lines, and line structure.

Acceptance: FM-MATH-BLOCK-001 shared cases pass once integrated, malformed and deeply nested inputs terminate linearly, and no rule in linewrapping/block_heuristics.py becomes the authoritative preservation scanner.
