---
type: is
id: is-01m10ntxm4570ja5wmb0zk7t7q
title: Define practical Markdown support and CommonMark fidelity policy
kind: task
status: closed
priority: 1
version: 7
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0zvnkyqktm79pza59a36k3b
created_at: 2026-08-27T03:57:19.362Z
updated_at: 2026-08-27T04:13:24.866Z
closed_at: 2026-08-27T04:13:24.862Z
close_reason: "Defined and committed the two-level Markdown compatibility policy, corrected CommonMark ledger status, split high- versus low-impact follow-up beads, updated related documentation beads, passed full local validation, pushed commit 8877c0c, and confirmed all PR #71 CI jobs pass."
resolution: null
duplicate_of: null
---
Make the preservation spec, conformance architecture, and corpus authoring guide state one two-level support contract. Baseline support means common Markdown, CommonMark, GFM, GLFM, and supported extension forms are handled safely with preserved meaning, deterministic output, fixed points, and Python/Rust parity. CommonMark compatibility is mandatory; line wrapping and canonicalization remain intended formatter behavior, while selective source preservation and known gaps are classified and documented. Prioritize common/high-impact semantic corruption, non-idempotence, and cross-port divergence before rare equivalent-spelling differences. Update the gap and documentation beads so future implementation and public claims follow the same hierarchy. Acceptance: the three durable documents agree; current CommonMark counts are accurate; high- and low-priority follow-up beads are separated; Markdown is Flowmark-formatted; relevant validation passes.

## Notes

Policy added to the preservation spec, conformance architecture, corpus README, and CommonMark provenance. The final contract requires semantic CommonMark compatibility, useful Flowmark line wrapping/canonicalization, fixed points, and Python/Rust parity; source-exact treatment is selective for opaque or fragile syntax. Live ledger corrected to 394 active/258 deferred. Follow-up split into high-impact fm-2zmv and low-impact policy review fm-9wip. Full lint, 535 pytest cases, 143 tryscript cases, active conformance corpus, and package build pass.
