---
type: is
id: is-01m0xn1kf4s20aga85f298dzww
title: "Phase 1B: implement the Python preservation core and math"
kind: feature
status: open
priority: 1
version: 13
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
child_order_hints:
  - is-01m0y01fj6agpjn5srgykswtbh
  - is-01m0y01wh744pw4vzp0516rz83
  - is-01m0xse3xhcna7jm56zb5vj4hk
  - is-01m0y02vbss1rhf6xgcwtf8qef
  - is-01m0y03afg7925xv1gk4v82zxw
  - is-01m0y03qynte7p5034zweegvjy
  - is-01m0y042abxn1c7w256z31w81j
  - is-01m0yfybntamn9fw3nefnr2fpt
created_at: 2026-08-25T23:45:46.467Z
updated_at: 2026-08-26T07:35:51.737Z
---
Parent for the Python pre-parse preservation pipeline after shared math cases are red: normalized UTF-8 byte model and registry; inline and container-aware block scanners; collision-safe side-table bridge; thin Marko adapter; token-aware transforms/wrapping; byte-safe CLI integration; and reviewed blast-radius closeout.

This supersedes the earlier post-parse regex/atomic-pattern proposal and the closed experimental M1/M3 beads. Math is implemented before inline-code source fidelity. Completion requires exact shared outputs, minimal native invariant tests, linear behavior, fail-closed restoration, no implicit CLI dedent/global strip, and no unexplained churn outside recognized syntax.
