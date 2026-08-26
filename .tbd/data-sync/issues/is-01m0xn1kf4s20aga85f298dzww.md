---
type: is
id: is-01m0xn1kf4s20aga85f298dzww
title: "Track A Phase 3: fix the four math defect classes"
kind: bug
status: open
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
child_order_hints:
  - is-01m0xse38rtqj4zy9m2k5f1awj
  - is-01m0xse3kbyvjhaehbstyxben7
  - is-01m0xse3xhcna7jm56zb5vj4hk
created_at: 2026-08-25T23:45:46.467Z
updated_at: 2026-08-26T01:02:30.833Z
---
M5 first, since it is the shared code path: stop normalising whitespace inside atomic spans so code spans become byte-exact, and math inherits it. Then M3 (route smartquotes and ellipses through iter_atomic_spans), M1 (add the three inline math patterns, M2 falls out), M4 (make dollar-dollar, bracket and begin-environment blocks deliberately opaque). Regenerate goldens including testdoc.expected.auto.md line 111, which currently records the collapsed block form as expected output.
