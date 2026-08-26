---
type: is
id: is-01m0zvn87mm8hma63csx00jc0m
title: Classify and resolve the deferred CommonMark 0.31.2 corpus
kind: task
status: open
priority: 1
version: 1
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - commonmark
  - conformance
  - parity
dependencies: []
parent_id: is-01m0zvmjwn7hmgcxs7vs5d4py0
created_at: 2026-08-26T20:19:50.644Z
updated_at: 2026-08-26T20:19:50.644Z
---
The shared CommonMark 0.31.2 review report currently contains 652 cases: 363 active and 289 deferred. Every deferred case points to a closed owner bead (fm-ocpw: 71, fm-ucy8: 10, fm-w1tn: 102, fm-w467: 106), so the ledger no longer represents actionable ownership.

Re-run all cases in both ports and classify every deferred result as source-exact preservation, intentional Flowmark normalization, an upstream-spec semantic equivalence, or a real bug. Activate reviewed cases with exact expected output; create narrowly scoped follow-up bugs for any behavior that should change. Regenerate the report from current evidence and reject stale closed owners.

Acceptance requires no deferred case with a closed or missing owner, an explicit reviewed disposition for all 652 examples, stable shared case IDs, a documented distinction between CommonMark semantic support and source-exact spelling preservation, and zero unexplained Python/Rust differences.
