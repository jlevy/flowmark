---
type: is
id: is-01kxhn6at99m3x5x3f89hn0kaf
title: "PR #64 review F64-1: report the artifact that triggered the newer-format guard"
kind: bug
status: closed
priority: 3
version: 3
labels: []
dependencies: []
parent_id: is-01kxhn6ahqt9tkyban1xa86bw5
created_at: 2026-07-15T01:10:22.792Z
updated_at: 2026-07-15T01:16:33.110Z
closed_at: 2026-07-15T01:16:33.109Z
close_reason: "Fixed in a3bbfc4: blocked-newer now reports the actual newer artifact, with a regression test."
---
Cursor Bugbot finding at src/flowmark/skill.py:378. If references/project-setup.md alone has a newer format stamp, blocked-newer must report that reference path rather than always reporting SKILL.md.
