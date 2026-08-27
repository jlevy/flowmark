---
type: is
id: is-01m0zvn87mm8hma63csx00jc0m
title: Classify and prioritize the live CommonMark 0.31.2 corpus
kind: task
status: open
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - commonmark
  - conformance
  - parity
dependencies:
  - type: blocks
    target: is-01m10nx6jr7fn9m30d8b483fm5
parent_id: is-01m0zvmjwn7hmgcxs7vs5d4py0
created_at: 2026-08-26T20:19:50.644Z
updated_at: 2026-08-27T04:01:23.373Z
---
The live CommonMark 0.31.2 manifest contains 652 default cases: 394 active and 258 deferred. The checked-in review report records the historical 363/289 import split and must not be treated as live status. Deferred ownership is also stale: fm-w467 owns 166, fm-w1tn owns 91, and fm-5vlb owns one, although all three beads are closed. A 2026-08-26 direct audit of the 258 source-preserving desired outputs found Python at 116 exact passes and 142 failures (141 stdout, one exit), Rust at 119 exact passes and 139 stdout failures, 18 first-pass Python/Rust output differences, and 12 Python versus 6 Rust non-fixed-point cases. Re-run and classify every deferred case as source-exact, intentional semantically equivalent normalization, or a real semantic, fixed-point, or parity bug. Prioritize common constructs and route high-impact fixes to fm-2zmv; route uncommon equivalent-spelling cleanup to fm-9wip. Regenerate a current report from executable evidence and replace every closed or missing owner. Acceptance: all 652 examples have a reviewed disposition; stable shared IDs remain; active cases have exact expected output; no deferred case has a closed/missing owner; reports distinguish semantic safety, fixed point, port parity, and source fidelity; no Python/Rust difference is unexplained.
