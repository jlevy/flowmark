---
type: is
id: is-01m0xv7gxsvfjjetmkryvx4wpj
title: "Address review: PR #71 — senior review of the preservation spec"
kind: task
status: closed
priority: 1
version: 11
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
child_order_hints:
  - is-01m0xv7h8kk9pkv2manjd0y6f6
  - is-01m0xv7hk355b1anaasjhtqqe6
  - is-01m0xv7hzw3n3rneka8wbgswq5
  - is-01m0xv7jbva5chx6mvrsr9mpk8
  - is-01m0xv7jntgc2frvg09d778cgc
  - is-01m0xv7jzx9wedx8s4scnqcgtr
  - is-01m0xv7ka05y737bj012y5fj5f
  - is-01m0xwqg0hf3zsw7jsqqv3g69a
created_at: 2026-08-26T01:33:51.917Z
updated_at: 2026-08-27T04:17:19.755Z
closed_at: 2026-08-26T02:45:43.818Z
close_reason: Takeover audit completed. Replaced the draft with a normative portable preservation design, added the shared-first language-neutral conformance architecture, expanded the math/code integration seeds, updated the PR description and review response, pushed commit 3867808, and verified all local and GitHub checks.
---

## Notes

Re-verified 2026-08-27 against the implementation head 783b445 (the original dispositions were made at 1c41b95/3867808, when this PR was plan-only).

All seven findings confirmed satisfied by running the review's own reproduction probes against the built CLI, not by re-reading the spec:
- FM-PR71-01: all three corruption probes now round-trip byte-exactly.
- FM-PR71-02: H$_2$O, 1$a$, $a$B, '$$ a + b $$' and soft-newline inline math all preserved; currency still correctly unprotected; backslash escaping is odd/even parity.
- FM-PR71-03: tests/parity_corpus/ manifest is real — 14 CLI cases + 81 registry cases + CommonMark 0.31.2, with change_id ledger and a reachability gate.
- FM-PR71-04: fence precedence, unmatched-opener fail-safe, container prefixes verified; 5000 unmatched dollars in 192ms (linear).
- FM-PR71-05: public iter_atomic_spans output for $`a+b`$ is unchanged (3 spans, inline_code_span intact) — no API break.
- FM-PR71-06: CRLF normalized, BOM retained, terminal newline added, F(F(x))==F(x).
- FM-PR71-07: phase order is Phase 0 contract -> 1A/1B math -> 2 Rust math -> 3 inline code -> 4 extensions.

Local gates at this head: make lint-check clean, 535 pytest + 143 tryscript passing, conformance reachability passing. GitHub CI 5/5 green on Python 3.10-3.14.

Open follow-ups from the review's suggestion list, now tracked separately: fm-gp64 (.flowmarkignore entry, verified safe to remove), fm-slpk (user-facing docs before release), fm-pib9 (tbd config split, author decision).
