---
type: is
id: is-01m0y0543cmz5ta9mnenqqq4c6
title: Prove zero-divergence Rust math parity and update the port ledger
kind: task
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
delegate: codex@spud10.local
labels: []
dependencies:
  - type: blocks
    target: is-01m0xscyy7w21twx4n4p5pgvh5
  - type: blocks
    target: is-01m0y06s6yse0c28j4fa8mz1vs
parent_id: is-01m0xn1krnmt64xkaw4dkzvc3k
hold: null
hold_until: null
created_at: 2026-08-26T02:59:56.138Z
updated_at: 2026-08-26T11:00:54.607Z
started_at: 2026-08-26T11:00:54.385Z
closed_at: 2026-08-26T11:00:54.606Z
close_reason: "Proved the pinned language-neutral corpus at 0d2bebb: 404 exact active cases and 35 inherited exact ledger entries, with three stale CommonMark entries removed. Full Rust/all-feature/no-default, tryscript, admin mapping, docs, build, package, and packaged-resource gates pass; evidence is recorded in c8ec803."
resolution: null
duplicate_of: null
---
Complete the direct Rust math port through the shared acceptance surface.

Run in ../flowmark-rs:
- every FM-PRESERVE-CORE-001, FM-MATH-INLINE-001, and FM-MATH-BLOCK-001 manifest case;
- upstream tryscript and topic fixtures through repos/flowmark;
- upstream reference and CommonMark documents;
- retained Rust-native unit/integration diagnostics, real-world differential sweeps, lint, tests, and build.

Update repos/rust-porting-playbook and admin/port-coverage-mapping to report upstream commit, change IDs, and exact case IDs rather than translated Python test counts. Remove stale copied portable fixtures and stale preservation workarounds only after replacement coverage is green. The known-divergence baseline must gain no preservation entries, and stale entries that pass must be removed.

Respect unrelated dirty-worktree changes when implementation begins. Acceptance: the pinned submodule plus native Rust runner provide an offline, language-neutral proof of exact parity and the next upstream change is mechanically discoverable.
