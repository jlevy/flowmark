---
type: is
id: is-01m0xscyy7w21twx4n4p5pgvh5
title: "Add tests/test_code_spans.py: delimiter and interior integrity properties"
kind: task
status: open
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0xscdmzyb7m84p8mtscn2j5
  - type: blocks
    target: is-01m0xsc02hwk2b4xnmww9869yk
parent_id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
created_at: 2026-08-26T01:01:52.966Z
updated_at: 2026-08-26T01:02:18.456Z
---
New file tests/test_code_spans.py, alongside the existing tests/test_escape_handling.py and tests/test_wrapping.py.

Assert properties rather than golden text, so the tests survive legitimate reflow and only fail on real corruption:

1. Delimiter integrity — for every code span in the input, the output span's CONTENT is byte-identical and its delimiter run is long enough that the content cannot close it early. Drives fm-fa8p.
2. Interior integrity — non-whitespace content unchanged, and runs of spaces and tabs inside a span preserved. Drives fm-9ey6.
3. The one permitted transform — a line ending inside a span becomes a space, per CommonMark 6.1.
4. Atomicity — a span crossing the wrap column moves whole, is never split, and is never escaped even when its content begins with a list marker. Passes today; regression cover.
5. Idempotence — a second pass is a no-op. This is what would have caught the `  a  ` -> ` a ` -> `a` progression.

A shared helper for "non-whitespace characters unchanged" is worth extracting; both this file and the math tests want it.

Parse spans with a backtick-run-aware regex, not a naive one, or the test cannot see the C1 failures it exists to catch.
