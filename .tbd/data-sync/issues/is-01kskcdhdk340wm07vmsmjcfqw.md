---
type: is
id: is-01kskcdhdk340wm07vmsmjcfqw
title: "Phase B: iter_atomic_spans (offset-preserving, selectable patterns)"
kind: task
status: open
priority: 2
version: 4
spec_path: docs/project/specs/active/plan-2026-05-26-public-inline-api.md
labels: []
dependencies:
  - type: blocks
    target: is-01kskcdhr6bd0qe9zvwq4ezj14
  - type: blocks
    target: is-01kskcdj5jkydhmc0v9ye1pcvh
parent_id: is-01kskcc95bk93gn9mz8x57c13z
created_at: 2026-05-27T00:12:43.315Z
updated_at: 2026-05-27T00:42:35.179Z
---
Spec Phase B: yield AtomicSpan(text,start,end,is_atomic) covering text exactly (round-trips); selectable/custom patterns arg. Becomes the single atomic-span primitive. Naming per spec Terminology: 'span'=located text region, 'range'=bare offsets (was iter_atomic_tokens).
