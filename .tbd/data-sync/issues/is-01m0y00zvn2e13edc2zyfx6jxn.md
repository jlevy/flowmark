---
type: is
id: is-01m0y00zvn2e13edc2zyfx6jxn
title: Add shared desired-output cases for math blocks and container boundaries
kind: task
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y01fj6agpjn5srgykswtbh
  - type: blocks
    target: is-01m0xse3xhcna7jm56zb5vj4hk
parent_id: is-01m0xn1k559xy7eg2a2zgpxqy5
created_at: 2026-08-26T02:57:40.724Z
updated_at: 2026-08-26T07:46:00.506Z
closed_at: 2026-08-26T07:46:00.506Z
close_reason: Committed reviewed language-neutral desired-output math contract and pre-fix classification in 9ee6444; full lint, type, conformance, pytest, and tryscript gates pass.
resolution: null
duplicate_of: null
---
Write red, language-neutral cases before implementation for FM-MATH-BLOCK-001.

Files:
- tests/parity_corpus/manifest.toml
- tests/parity_corpus/cases/preservation/math-block/**
- tests/tryscript/fixtures/content/math.md for the full-document interaction
- tests/testdocs expected files only when reviewed behavior intentionally changes

Cover $$ and bracket display blocks, exact compatible closers, MyST labels/attributes, nested and custom LaTeX environments, mismatch and unmatched fallback, blank lines, container changes, blockquotes, list content columns, lazy continuation, tabs, fenced/indented code precedence, frontmatter adjacency, table boundaries, raw-block adjacency, CRLF/BOM/missing final newline, file/in-place/check/config modes, deep nesting, long bodies, and linear-time watchdog cases.

The expected block slice includes authored prefixes, indentation, whitespace, line structure, labels, and attributes after documented normalization. Do not accept a collapsed block as current truth. Acceptance: every block-state transition and fail-safe is pinned by exact/idempotent shared output, with focused cases plus the topic document rather than exhaustive duplication.
