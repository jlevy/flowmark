---
type: is
id: is-01kyss8gskyz68yaky5j8vrnpx
title: "Phase 4C: extension-registry integration and parity closeout"
kind: task
status: closed
priority: 2
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
created_at: 2026-07-30T15:11:06.035Z
updated_at: 2026-08-26T17:58:30.006Z
closed_at: 2026-08-26T17:58:30.005Z
close_reason: "Completed shared extension/fixed-point integration and corpus provenance closeout: 476 exact shared passes plus 34 inherited ledger entries, 143 tryscript cases, complete test/reference/CommonMark layers, zero differences across all 670 recovered-corpus files, documented unrecoverable 623-file provenance, and hardened retained audit evidence."
resolution: null
duplicate_of: null
---
After the P0 and P1/P2 parent groups are complete, run the complete shared corpus, upstream tryscript/topic fixtures, reference documents, CommonMark, repository Markdown, and real-world diagnostics in both ports. Review cross-family precedence and interactions, ensure every new change ID is present in the port ledger, reject dangling/dead fixtures, remove superseded workarounds, and require no unexplained golden churn or new divergence.

This is an integration closeout, not the place to define missing family semantics or copy test assets.

## Notes

Shared corpus discovery: reference.testdoc.semantic.fixed-point, reference.testdoc.cleaned.fixed-point, and reference.testdoc.auto.fixed-point are deferred to this bead. The first two expose second-pass indentation drift in footnote [^217]; auto also reapplies smart quotes/ellipses on pass two. Their one-pass whole-document cases remain active.
