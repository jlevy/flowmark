---
type: is
id: is-01m13728vhe3q9vhxvjperkwc9
title: "PR #71 review CI1: idempotence gate imports tomllib on Python 3.10"
kind: bug
status: in_progress
priority: 1
version: 2
labels:
  - pr-review
  - ci
dependencies: []
parent_id: is-01m137288cj1mnec8gr38287kv
created_at: 2026-08-28T03:36:54.895Z
updated_at: 2026-08-28T03:37:08.145Z
---
Hosted CI run 33139256073 fails at tests/test_idempotence_corpus.py:28 on the supported Python 3.10 job because tomllib exists only in Python 3.11+. Use the already-locked tomli compatibility package on Python 3.10, preserve precise types, add or run a 3.10-specific red/green check, then complete all local and hosted gates.
