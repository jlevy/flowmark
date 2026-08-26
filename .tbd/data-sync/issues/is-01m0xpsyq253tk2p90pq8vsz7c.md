---
type: is
id: is-01m0xpsyq253tk2p90pq8vsz7c
title: "C1: code span delimiter runs are collapsed regardless of content"
kind: bug
status: open
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
created_at: 2026-08-26T00:16:32.994Z
updated_at: 2026-08-26T00:17:27.390Z
---
flowmark shortens a multi-backtick code span delimiter to a single backtick unconditionally, without checking whether the content contains a backtick run that would then close the span early.

Harmless when the content has no backticks (``simple`` -> `simple` renders the same). Structurally corrupting when it does:

  ``has ` tick``              ->  `has ` tick`
  ``code with `backtick` in`` ->  `code with `backtick` in`
  ```outer with `` inner```   ->  `outer with `` inner`

In each broken case the shortened delimiter is closed by a backtick inside the content, so one span becomes a truncated span plus loose text plus a stray backtick. The rendered output changes completely. Silent and idempotent (stable after one pass), so one-time structural corruption rather than runaway. Fires in every context including table cells.

This is what mangled the preservation spec's own table cells while it was being written, and is almost certainly the same root cause as issue #58.

Fix: choose the delimiter run from the content — the shortest backtick run strictly longer than the longest run inside — rather than collapsing to one. Narrowing a wider delimiter is fine only when the content holds no backticks.

Reproduced by tests/tryscript/fixtures/content/code-inline.md sections A3, A4, A5, A7, A8, D6.
