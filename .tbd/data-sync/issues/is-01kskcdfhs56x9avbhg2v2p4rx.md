---
type: is
id: is-01kskcdfhs56x9avbhg2v2p4rx
title: "Phase A: define a clean public pattern type/factory"
kind: task
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-05-26-public-inline-api.md
labels: []
dependencies:
  - type: blocks
    target: is-01kskcdf783b4t174gr6yr2ymf
  - type: blocks
    target: is-01kskcdhdk340wm07vmsmjcfqw
parent_id: is-01kskcc95bk93gn9mz8x57c13z
created_at: 2026-05-27T00:12:41.400Z
updated_at: 2026-05-27T00:12:54.078Z
---
Review #3: re-exported AtomicPattern requires open_delim/close_delim/open_re/close_re, which are tag-handling internals, not a general tokenization contract. Before stabilizing, expose a smaller public pattern type or factory (name+pattern, sensible defaults) and adapt the internal tag metadata behind it, so 'consumers may pass custom AtomicPatterns' is actually ergonomic.
