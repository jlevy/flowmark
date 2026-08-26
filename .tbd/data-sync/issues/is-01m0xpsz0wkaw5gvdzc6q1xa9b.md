---
type: is
id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
title: "Track C Phase 2: inline code corpus, red tests, and the C1/C2 fixes"
kind: task
status: open
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
created_at: 2026-08-26T00:16:33.308Z
updated_at: 2026-08-26T00:17:27.972Z
---
Phase 2 of the consolidated spec, scheduled ahead of the math fixes because inline code owns the shared span code path.

Corpus is written: tests/tryscript/fixtures/content/code-inline.md, expanded from a four-line stub into five parts (delimiter runs, whitespace, literal content, block contexts, wrapping). Like math.md it was already present in both repos and referenced by no test in either, and its final line was already the C1 reproducer, so the shipped fixture corrupted itself.

Baseline measured against flowmark 0.7.3: 16 of 30 sections change, of which two are correct (a wider delimiter narrowing with no backticks inside, and a line ending becoming a space). Fourteen defects remain, split between fm-dq8n (C1) and fm-bj2c (C2).

Remaining work: add tests/test_code_spans.py asserting content and delimiter integrity, wire the fixture into formatting.tryscript.md and the idempotency check, fix C1 and C2, then survey and regenerate the goldens the fixes change.
