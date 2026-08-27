---
type: is
id: is-01m10ntxm4570ja5wmb0zk7t7q
title: Define practical Markdown support and CommonMark fidelity policy
kind: task
status: in_progress
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0zvnkyqktm79pza59a36k3b
created_at: 2026-08-27T03:57:19.362Z
updated_at: 2026-08-27T04:02:08.139Z
---
Make the preservation spec, conformance architecture, and corpus authoring guide state one two-level support contract. Baseline support means common Markdown, CommonMark, GFM, GLFM, and supported extension forms are handled safely with preserved meaning, deterministic output, fixed points, and Python/Rust parity. Strict CommonMark fidelity then pursues source-exact output where practical and requires every intentional normalization or known gap to be classified and documented. Prioritize common/high-impact semantic corruption, non-idempotence, and cross-port divergence before rare equivalent-spelling differences. Update the gap and documentation beads so future implementation and public claims follow the same hierarchy. Acceptance: the three durable documents agree; current CommonMark counts are accurate; high- and low-priority follow-up beads are separated; Markdown is Flowmark-formatted; relevant validation passes.

## Notes

Policy added to the preservation spec, conformance architecture, corpus README, and CommonMark provenance. Live ledger corrected to 394 active/258 deferred. Follow-up split into high-impact fm-2zmv and low-impact fm-9wip; related docs beads now require the two-level contract.
