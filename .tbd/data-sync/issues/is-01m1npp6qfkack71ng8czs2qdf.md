---
type: is
id: is-01m1npp6qfkack71ng8czs2qdf
title: Run full Python source and artifact validation
kind: task
status: open
priority: 1
version: 3
labels:
  - release
dependencies:
  - type: blocks
    target: is-01m1npp70ve3p6fyj8n5qt2xx4
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T07:56:16.494Z
updated_at: 2026-09-04T08:31:34.542Z
---
Run the documented locked lint, type, conformance, golden, idempotence, pytest, build, metadata, and installed wheel/sdist smoke gates. Verify supported Python versions in hosted CI and ensure no gate is vacuous or polluted by local ignored artifacts.

## Notes

Pre-version-bump validation on 2026-09-04 is clean: make lint-check (codespell, Ruff lint/format, BasedPyright 0 errors/0 warnings); make test (CommonMark import checksum, conformance schema/reachability, entire shared corpus including new fence and invalid-UTF-8 cases, 554 pytest tests, 145 golden tryscript tests); make build produced sdist and wheel. Remaining: metadata/version pin checks and installed-artifact smoke after final 0.8.0 bump.
