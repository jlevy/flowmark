---
type: is
id: is-01m0xpsyq253tk2p90pq8vsz7c
title: "C1: authored code-span delimiters can be structurally corrupted"
kind: bug
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
created_at: 2026-08-26T00:16:32.994Z
updated_at: 2026-08-26T03:01:09.732Z
---
The current Marko renderer reconstructs every inline code span, often shortening a multi-backtick delimiter to one backtick. If the body contains a backtick run, the emitted delimiter can close early and change the Markdown structure. Even when narrowing renders equivalently, it violates the approved source-formatter policy.

Required behavior is FM-CODE-SPAN-001 source fidelity: after document-level BOM/newline normalization, preserve the complete valid authored span—opening run, body, and closing run—through the pre-parse side table. Recognition matches an opener to the next run of exactly the same length and participates in deterministic math/code arbitration. Unmatched runs remain ordinary text.

Primary evidence is the shared code-span corpus plus code-inline.md across tryscript and both ports. Close only after fm-fa8p and the integration/acceptance beads prove exact output in Python; Rust parity is tracked separately.
