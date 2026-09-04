---
type: is
id: is-01m1nnnkv9vya3pm65dx881shh
title: Exclude ignored generated reference outputs from idempotence corpus
kind: bug
status: in_progress
priority: 1
version: 4
labels:
  - release-blocker
dependencies:
  - type: blocks
    target: is-01m1npp6qfkack71ng8czs2qdf
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T07:38:28.583Z
updated_at: 2026-09-04T08:31:34.243Z
---
On clean current main with pre-existing ignored tests/testdocs/testdoc.actual.* files, make test fails tests/test_idempotence_corpus.py because corpus_documents() scans every *.md under tests, including generated local outputs that are explicitly gitignored and are not shipped. Four narrow-mode entries appear as unexpected. Make the corpus select shipped/authoritative documents only and add a regression test proving ignored generated outputs cannot contaminate the gate.

## Notes

Fix implemented on codex/release-0.8.0-prep: _test_corpus_documents excludes ignored testdoc.actual.* generated outputs and a TemporaryDirectory regression proves they cannot contaminate the authoritative corpus. Focused regression passed; full make test passed on 2026-09-04 (shared conformance corpus, 554 pytest tests, 145 tryscript tests). Keep in progress until prep PR is merged.
