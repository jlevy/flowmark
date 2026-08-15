---
type: is
id: is-01m01c5fqxcf8rxg1z9fwkae96
title: "PR #69 F2: align direct uv security guidance"
kind: task
status: closed
priority: 2
version: 2
labels:
  - pr-review
dependencies: []
parent_id: is-01m01c59nygwgqjebk8z7b93qr
created_at: 2026-08-15T00:11:52.445Z
updated_at: 2026-08-15T00:15:05.816Z
closed_at: 2026-08-15T00:15:05.815Z
close_reason: "Fixed: direct uv security guidance now selects uv.toml exclusively, states the 0.9.17 feature floor and current 0.12 requirement, and candidate workflows carry corrected comments."
---
The supply-chain policy still says relative durations require uv 0.9 and its direct lock command does not select the exclusive checked-in uv.toml. Align it with 0.9.17 history and the project-required 0.12 line.
