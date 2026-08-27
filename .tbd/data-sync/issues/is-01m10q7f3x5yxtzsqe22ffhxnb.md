---
type: is
id: is-01m10q7f3x5yxtzsqe22ffhxnb
title: Upgrade repository tbd integration to 0.8.1
kind: chore
status: closed
priority: 1
version: 3
labels: []
dependencies: []
created_at: 2026-08-27T04:21:39.068Z
updated_at: 2026-08-27T04:33:28.751Z
closed_at: 2026-08-27T04:33:28.746Z
close_reason: "Upgraded the official managed integration and exact fallback to tbd 0.8.1 in PR #71; local full gates and all five Python CI jobs passed."
resolution: null
duplicate_of: null
---
Run the official tbd 0.8.1 setup upgrade on the active Flowmark PR branch. Refresh checked-in launchers, skills, agent integration, and repository metadata; verify every executable fallback pins get-tbd@0.8.1; review the generated diff; run tbd doctor plus the repository lint/test/build gates; commit and push to PR #71. The maintainer explicitly approved a first-party exception to the normal 14-day cool-off for this maintained package; record the exact package version, registry integrity, advisory checks, and approval in the PR.
