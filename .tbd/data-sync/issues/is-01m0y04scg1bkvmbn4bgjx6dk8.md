---
type: is
id: is-01m0y04scg1bkvmbn4bgjx6dk8
title: Integrate Rust protected nodes, wrapping, and byte-safe CLI I/O
kind: task
status: open
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y0543cmz5ta9mnenqqq4c6
parent_id: is-01m0xn1krnmt64xkaw4dkzvc3k
created_at: 2026-08-26T02:59:45.167Z
updated_at: 2026-08-26T02:59:56.138Z
---
Connect the Rust preservation core to comrak and every process boundary.

Rust files and functions:
- src/formatter/filling.rs::fill_markdown(): normalize, scan/protect, parse/transform/render unprotected text, validate/restore, finalize; replace preservation-related ad hoc PUA/NUL workarounds rather than layering another mechanism.
- src/wrapping/text_wrapping.rs: retire extract_atomic_constructs()/restore_atomic_constructs() placeholder-width approximation for protected regions and introduce structured clusters/fragments with side-table widths.
- src/formatter/markdown.rs and formatter visitors: thin protected inline/block adapter and transform skipping.
- src/lib.rs::reformat_text()/reformat_file() and src/main.rs stdin/stdout paths: strict UTF-8 bytes, BOM/LF contract, no implicit document dedent, deterministic errors, atomic no-partial writes.
- tests/test_preservation.rs: only native comrak/token and failure-boundary diagnostics.

Keep old public/native behavior outside the shared change IDs unless an exact shared case approves a change. Acceptance: every core and math shared case passes the Rust binary, including multiline width accounting, parser collisions, invalid UTF-8, sentinel collisions, and in-place failure safety.
