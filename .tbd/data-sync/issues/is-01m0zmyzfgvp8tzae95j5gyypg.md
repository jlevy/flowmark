---
type: is
id: is-01m0zmyzfgvp8tzae95j5gyypg
title: Close Rust preservation remote portability gaps
kind: bug
status: closed
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - ci
  - rust
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
created_at: 2026-08-26T18:22:49.314Z
updated_at: 2026-08-26T19:18:44.601Z
closed_at: 2026-08-26T19:18:44.599Z
close_reason: "Rust remote portability is complete at 90d24c1: MSRV, coverage isolation, semver, exact Windows shared-source byte export and provenance, Linux/macOS recursive checkout, and the full PR matrix pass."
resolution: null
duplicate_of: null
---
Rust PR #81 exposes four remote-only portability gaps: a let-chain newer than MSRV 1.85; LLVM coverage artifacts contaminating exact conformance file trees; a semver-breaking public InvalidUtf8 enum variant; and Windows recursive checkout failure on existing colon-named Python documentation. Fix each without weakening the shared contract: retain full recursive checkout on Unix, use an exact-gitlink tests-only sparse checkout on Windows, keep invalid UTF-8 behavior through the existing error surface, and rerun the complete PR matrix.
