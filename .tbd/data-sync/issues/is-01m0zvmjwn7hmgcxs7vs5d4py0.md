---
type: is
id: is-01m0zvmjwn7hmgcxs7vs5d4py0
title: "Follow-up: close remaining Markdown preservation evidence gaps"
kind: epic
status: open
priority: 1
version: 11
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
  - is-01m10nx6jr7fn9m30d8b483fm5
  - is-01m10nx6xr86enx1x2h5mkcqs8
  - is-01m10tmze6n4sjk67mcbngzb72
created_at: 2026-08-26T20:19:28.780Z
updated_at: 2026-08-27T05:21:27.492Z
---
PR #71 and Rust-port PR #81 have broad shared preservation coverage, but the senior review found correctness and evidence gaps that prevent an unqualified claim of universal Markdown preservation. The baseline contract is practical support: common CommonMark, GFM, and GLFM constructs plus registered extension forms must preserve meaning and content, reach a fixed point, and agree exactly across Python and Rust with little or no dialect configuration. CommonMark compatibility is mandatory; reviewed Flowmark line wrapping and canonicalization are expected, while source-exact treatment is selective for opaque or fragile syntax. Track only the remaining cross-language work here. Every behavior fix begins with a language-neutral desired-output case, uses a stable change ID, runs unchanged through both native runners, and reaches a fixed point. Small language-specific unit tests may cover internals but cannot replace shared observable evidence. The live CommonMark ledger is 394 active and 258 deferred default cases; the historical import report's 363/289 split is not current. Resolve the GitLab examples from issue #67, classify all deferred cases, fix common semantic/fixed-point/parity failures under fm-2zmv before lower-impact source-spelling work under fm-9wip, verify scanner complexity, and make issue reproductions traceable. Close only with reviewed exact outputs, documented remaining gaps, clean-package execution, and hosted CI.
