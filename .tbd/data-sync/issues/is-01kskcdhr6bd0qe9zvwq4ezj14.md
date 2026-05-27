---
type: is
id: is-01kskcdhr6bd0qe9zvwq4ezj14
title: "Phase B: split_sentences_with_spans (atomic-aware, offset-preserving)"
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-05-26-public-inline-api.md
labels: []
dependencies:
  - type: blocks
    target: is-01kskcdjgxdyx2rwyw8nkabwh7
parent_id: is-01kskcc95bk93gn9mz8x57c13z
created_at: 2026-05-27T00:12:43.654Z
updated_at: 2026-05-27T00:12:55.192Z
---
Spec Phase B: apply heuristic_end_of_sentence only at boundaries between atomic tokens; never split inside one; preserve original whitespace/offsets (verbatim spans). Keep lossy split_sentences_regex unchanged.
