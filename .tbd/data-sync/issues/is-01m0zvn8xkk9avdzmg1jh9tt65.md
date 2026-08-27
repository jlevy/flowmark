---
type: is
id: is-01m0zvn8xkk9avdzmg1jh9tt65
title: Map original preservation issues to exact shared regression cases
kind: task
status: closed
priority: 1
version: 6
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - traceability
  - testing
  - parity
dependencies:
  - type: blocks
    target: is-01m0zvpft5b6ft59jdxv76yc7b
parent_id: is-01m0zvmjwn7hmgcxs7vs5d4py0
created_at: 2026-08-26T20:19:51.346Z
updated_at: 2026-08-27T05:14:51.596Z
closed_at: 2026-08-27T05:14:51.595Z
close_reason: "Mapped issues #58, #62, #67, and #70 from each promised behavior to exact stable shared case IDs, exact fixtures, fixed-point behavior, and both-port evidence in the active preservation spec."
resolution: null
duplicate_of: null
---
Make GitHub issues #58, #62, #67, and #70 auditable from the language-neutral conformance corpus. Each original minimal reproduction and each distinct promised behavior must map to a stable shared case ID and change ID rather than only to a broader topic document or a language-specific unit test.

Add any missing exact reproductions, including issue #58's escaped-backtick spacing example and the unresolved issue #67 forms. Record issue links in corpus metadata or the preservation traceability ledger, validate that every referenced case exists and is active or explicitly gap-tracked, and run the same cases through both native runners.

Acceptance requires a reviewer to move from each issue claim to exact input, exact output, status, and both-port evidence without reading Python implementation details.

## Notes

Reviewed final issue ledger. #58 maps to preservation.code-span.issue-58-escaped-backtick; #70 to preservation.math.inline.issue-70-wrap-corruption; #67 to wikilink, definition-list, and all five GitLab cases; #62 maps each reported extension family to an exact representative shared case. Every referenced case is active, idempotent, and consumed unchanged by both native runners at Python 644be24 / Rust 8e65557.
