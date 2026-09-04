---
type: is
id: is-01m1nnnkv9vya3pm65dx881shh
title: Exclude ignored generated reference outputs from idempotence corpus
kind: bug
status: in_progress
priority: 1
version: 2
labels:
  - release-blocker
dependencies: []
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T07:38:28.583Z
updated_at: 2026-09-04T07:40:48.324Z
---
On clean current main with pre-existing ignored tests/testdocs/testdoc.actual.* files, make test fails tests/test_idempotence_corpus.py because corpus_documents() scans every *.md under tests, including generated local outputs that are explicitly gitignored and are not shipped. Four narrow-mode entries appear as unexpected. Make the corpus select shipped/authoritative documents only and add a regression test proving ignored generated outputs cannot contaminate the gate.
