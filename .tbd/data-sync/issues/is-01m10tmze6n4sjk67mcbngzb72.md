---
type: is
id: is-01m10tmze6n4sjk67mcbngzb72
title: Share callout-plus-inline regression for Rust parity
kind: task
status: closed
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - parity
  - preservation
dependencies: []
parent_id: is-01m0zvmjwn7hmgcxs7vs5d4py0
created_at: 2026-08-27T05:21:27.492Z
updated_at: 2026-08-27T05:21:34.508Z
closed_at: 2026-08-27T05:21:34.507Z
close_reason: Added preservation.extension.callout.adjacent-inline with the reviewer matrix under FM-EXT-OBSIDIAN-CALLOUT-001. Python passes the exact expected output twice and corpus coverage/reachability passes.
resolution: null
duplicate_of: null
---
Add the PR #81 R1 callout-plus-protected-inline reproductions to the language-neutral corpus under FM-EXT-OBSIDIAN-CALLOUT-001 before the Rust fix. Python must establish exact desired output and two-pass idempotence; Rust consumes the unchanged case.
