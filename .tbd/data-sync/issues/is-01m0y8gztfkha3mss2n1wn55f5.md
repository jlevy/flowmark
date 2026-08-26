---
type: is
id: is-01m0y8gztfkha3mss2n1wn55f5
title: Audit and close the Rust v0.7.2-to-v0.7.3 baseline gap
kind: task
status: open
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn1krnmt64xkaw4dkzvc3k
created_at: 2026-08-26T05:26:13.582Z
updated_at: 2026-08-26T05:40:11.028Z
---
Current flowmark-rs main already completes Python v0.7.2 parity. After fm-mfvi merges main into the preservation branch, produce a behavior/test/interface/dependency inventory for v0.7.2..v0.7.3, refresh the legacy function mapping only where it adds evidence, port or explicitly track every remaining behavior delta, and prove the resulting baseline before claiming the preservation phase represents whole-program parity. Shared conformance remains authoritative for portable behavior; language-specific unit mappings are supplementary.
