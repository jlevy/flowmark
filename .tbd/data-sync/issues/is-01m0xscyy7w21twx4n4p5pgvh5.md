---
type: is
id: is-01m0xscyy7w21twx4n4p5pgvh5
title: Add shared source-exact conformance cases for inline code spans
kind: task
status: closed
priority: 1
version: 7
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
delegate: codex@spud10.local
labels: []
dependencies:
  - type: blocks
    target: is-01m0xscdmzyb7m84p8mtscn2j5
  - type: blocks
    target: is-01m0xsc02hwk2b4xnmww9869yk
parent_id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
hold: null
hold_until: null
created_at: 2026-08-26T01:01:52.966Z
updated_at: 2026-08-26T11:05:44.772Z
started_at: 2026-08-26T11:02:50.920Z
closed_at: 2026-08-26T11:05:44.760Z
close_reason: Added six reviewed language-neutral FM-CODE-SPAN-001 cases for delimiter runs, whitespace/typography, multiline containers, math arbitration, Markdown contexts, and malformed fallback in b0caa64; coverage validation passes and the pre-fix CLI is red on exact delimiter preservation.
resolution: null
duplicate_of: null
---
Write FM-CODE-SPAN-001 as desired-output cases in the language-neutral manifest before changing Python code.

Files:
- tests/parity_corpus/manifest.toml
- tests/parity_corpus/cases/preservation/code-span/**
- tests/tryscript/fixtures/content/code-inline.md as the complementary integration document

Cover authored delimiter runs of arbitrary length, bodies containing shorter/equal/different runs, leading/trailing/all-space bodies, tabs, authored soft newlines, empty/malformed/unclosed spans, escapes, Unicode, adjacency, wrapping N-1/N/N+1, paragraphs/headings/lists/quotes/tables/links, every transform/mode, stdin/files/in-place, and idempotence. The formatter policy is source-exact: valid spans preserve authored delimiters and body after document-level normalization; do not canonicalize them through CommonMark renderer rules.

Small native scanner vectors may be added to tests/test_preservation_scanner.py only for run matching or arbitration diagnostics. Do not build a second Python-only output oracle or compare stripped whitespace. Acceptance: C1 and C2 fail against exact shared expected bytes before implementation and all already-correct contexts are pinned.
