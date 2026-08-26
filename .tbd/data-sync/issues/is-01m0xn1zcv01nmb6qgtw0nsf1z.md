---
type: is
id: is-01m0xn1zcv01nmb6qgtw0nsf1z
title: "C2: whitespace and line structure inside code spans are normalized"
kind: bug
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
created_at: 2026-08-25T23:45:58.683Z
updated_at: 2026-08-26T11:30:17.826Z
closed_at: 2026-08-26T11:30:17.825Z
close_reason: C2 is proven closed by shared whitespace, tab, multiline-container, topic, and second-pass exact tests; full Python suite is green.
resolution: null
duplicate_of: null
---
The current paragraph path collapses whitespace before atomic tokenization, so spaces and tabs inside code spans are changed and some inputs drift again on a second pass. Contexts taking different renderer paths expose inconsistent behavior.

The approved Flowmark policy is stricter than CommonMark renderer canonicalization: a recognized valid code span preserves its complete authored normalized-source slice, including delimiter width, spaces, tabs, and authored soft line endings. It is protected before Marko and restored after structured wrapping. Global re.sub/string split-join and public iter_atomic_spans are not the new mechanism.

Primary evidence is exact FM-CODE-SPAN-001 shared cases plus code-inline.md, reference documents, and idempotence in both ports. Close the Python defect only after fm-9ey6 and fm-ocpw pass; Rust parity is tracked separately.
