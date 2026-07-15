---
type: is
id: is-01kxhnvmnpvrf8hgzvp6rde0w1
title: "PR #78 review F78-2: publish the skill bundle without a broken link"
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01kxhn6b32q7kt5fahacwq37gx
created_at: 2026-07-15T01:22:01.013Z
updated_at: 2026-07-15T01:30:00.918Z
closed_at: 2026-07-15T01:30:00.917Z
close_reason: "Fixed in 22e2211: bundle artifacts are staged before publication and SKILL.md is published last; regression test added."
---
Cursor Bugbot finding at src/skills/mod.rs:355 on commit 331b298. Stage both bundle artifacts before publication and publish the project-setup reference before SKILL.md so a failed install never exposes a new skill that links to a missing reference.
