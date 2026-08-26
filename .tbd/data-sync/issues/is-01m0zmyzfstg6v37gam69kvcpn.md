---
type: is
id: is-01m0zmyzfstg6v37gam69kvcpn
title: Restore declared Python 3.10 preservation compatibility
kind: bug
status: closed
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - ci
  - python
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
created_at: 2026-08-26T18:22:49.336Z
updated_at: 2026-08-26T19:18:44.208Z
closed_at: 2026-08-26T19:18:44.207Z
close_reason: Python 3.10 compatibility is restored at 783b445 with stable string-enum behavior; the full local Python 3.10 lint/test/golden matrix and GitHub CI on Python 3.10 through 3.14 pass.
resolution: null
duplicate_of: null
---
PR #71 fails its Python 3.10 lint/type gate because preservation/model.py imports enum.StrEnum, which was added in Python 3.11. Replace it with a 3.10-compatible stable string enum without changing serialized values or string behavior; run focused tests, lint/types, and the full Python matrix through PR CI.
