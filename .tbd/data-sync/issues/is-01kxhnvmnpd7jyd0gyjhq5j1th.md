---
type: is
id: is-01kxhnvmnpd7jyd0gyjhq5j1th
title: "PR #64 review F64-2: make printed skill reference actionable"
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01kxhn6ahqt9tkyban1xa86bw5
created_at: 2026-07-15T01:22:01.013Z
updated_at: 2026-07-15T01:29:58.137Z
closed_at: 2026-07-15T01:29:58.136Z
close_reason: "Fixed in 37c118c: printed skills now direct users to install the complete bundle; regression test added."
---
Cursor Bugbot finding at src/flowmark/skills/SKILL.md:43 on commit a3bbfc4. flowmark --skill prints SKILL.md without materializing references/project-setup.md, so repository adoption must direct printed-skill users to install the bundle before following the relative reference.
