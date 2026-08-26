---
type: is
id: is-01m0xwqg0hf3zsw7jsqqv3g69a
title: "PR #71 follow-up: resolve the portable preservation-scanner contract"
kind: task
status: closed
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xv7gxsvfjjetmkryvx4wpj
created_at: 2026-08-26T02:00:03.856Z
updated_at: 2026-08-26T02:43:19.140Z
closed_at: 2026-08-26T02:43:19.034Z
close_reason: "Replaced the review-history draft with a normative portable scanner contract: normalized UTF-8 byte offsets, collision-free sentinels, source-order arbitration, explicit dollar/backtick state machines, container-aware blocks and table-cell scopes, multiline token wrapping, fail-closed restoration, source-exact code spans, and a math-first Python/Rust rollout."
resolution: null
duplicate_of: null
---
Rewrite the revised PR spec as a current-state design. Select a deterministic pre-parse lossless scanner with typed protected regions and a side table; define ordering, dollar/backtick arbitration, container-aware block matching, mismatch/unmatched fail-safe, UTF-8/newline/index/width semantics, collision-safe restoration, code-span source preservation, public API compatibility, and math-first rollout. Remove review-history prose and contradictions.
