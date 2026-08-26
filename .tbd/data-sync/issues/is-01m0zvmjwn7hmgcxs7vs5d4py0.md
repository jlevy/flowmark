---
type: is
id: is-01m0zvmjwn7hmgcxs7vs5d4py0
title: "Follow-up: close remaining Markdown preservation evidence gaps"
kind: epic
status: open
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - preservation
  - parity
  - testing
dependencies: []
child_order_hints:
  - is-01m0zvn7xdfw27zbdpf54kcabm
  - is-01m0zvn87mm8hma63csx00jc0m
  - is-01m0zvn8jpssxjwtqqq058sxdz
  - is-01m0zvn8xkk9avdzmg1jh9tt65
created_at: 2026-08-26T20:19:28.780Z
updated_at: 2026-08-26T20:19:51.346Z
---
PR #71 and the Rust-port PR #81 have broad shared preservation coverage, but the senior review found correctness and evidence gaps that prevent an unqualified claim of universal Markdown preservation.

Track only the remaining cross-language work here. Every behavior fix must begin with a language-neutral desired-output case in the upstream parity corpus, use a stable change ID, run unchanged through both native runners, and reach a fixed point. Small language-specific unit tests may cover scanner internals, but they cannot replace the shared behavioral case.

The closeout must cover the unresolved GitLab Flavored Markdown examples from issue #67, classify the 289 deferred CommonMark 0.31.2 cases whose owner beads are already closed, verify the scanner complexity promised by the spec, and make the original issue reproductions directly traceable to shared cases. Do not close this epic based on test counts or broad family coverage; require reviewed exact outputs, Python/Rust parity, clean-package execution, and hosted CI evidence.
