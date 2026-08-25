---
type: is
id: is-01m0xn1k559xy7eg2a2zgpxqy5
title: "Track A Phase 1: math corpus and red tests"
kind: task
status: open
priority: 1
version: 1
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
created_at: 2026-08-25T23:45:46.149Z
updated_at: 2026-08-25T23:45:46.149Z
---
Replace the dead math.md fixture with Parts A-E, add tests/test_math.py with property assertions per defect class, wire the fixture into formatting.tryscript.md and the idempotency check. Corpus is written and its baseline measured against flowmark 0.7.3: 19 defect instances, 13 content-changing sections and 6 collapsed display blocks. Remaining work is the test runner and the golden wiring. The fixture was referenced by no test in either repo, which is why these defects went unnoticed.
