---
type: is
id: is-01ksrx01vtyypaf37nj3tz6tvr
title: Align flowmark build/CI infra with simple-modern-uv template (post-v0.7.1)
kind: epic
status: closed
priority: 1
version: 3
labels: []
dependencies: []
created_at: 2026-05-29T03:38:39.354Z
updated_at: 2026-05-29T04:00:32.344Z
closed_at: 2026-05-29T04:00:32.344Z
close_reason: "Epic complete: all three children merged in PR #55"
---
Umbrella for build/CI infra alignment with jlevy/simple-modern-uv, deferred out of the v0.7.1 patch (build-process only; does not affect the published package). Children: fm-pp07 (Node 24 action versions, P1/time-sensitive: 2026-06-02), fm-2u3b (CI lint --check), fm-2tp9 (frozen publish). NOTE: flowmark is AHEAD of the template on supply-chain hardening (frozen lockfile, pip-audit, skill-pin guards, golden tests) and on its extended docs/publishing.md - no need to pull those back from the template.
