---
type: is
id: is-01kskcdf783b4t174gr6yr2ymf
title: "Phase A: add autolink/bare-URL atomic patterns + extend prose subset"
kind: task
status: open
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-05-26-public-inline-api.md
labels: []
dependencies:
  - type: blocks
    target: is-01kskcdhdk340wm07vmsmjcfqw
parent_id: is-01kskcc95bk93gn9mz8x57c13z
created_at: 2026-05-27T00:12:41.064Z
updated_at: 2026-05-27T00:12:54.350Z
---
Review #2: MARKDOWN_INLINE_PATTERNS is exactly (INLINE_CODE_SPAN, MARKDOWN_LINK), so <https://...> angle autolinks and GFM bare URLs are NOT atomic under the advertised prose set; sentence spans could bisect URL punctuation. Add explicit angle-autolink and bare-URL AtomicPatterns, include them in MARKDOWN_INLINE_PATTERNS, and update the test that locks the tuple. Add tests.
