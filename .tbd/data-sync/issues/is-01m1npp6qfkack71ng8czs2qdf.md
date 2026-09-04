---
type: is
id: is-01m1npp6qfkack71ng8czs2qdf
title: Run full Python source and artifact validation
kind: task
status: closed
priority: 1
version: 5
labels:
  - release
dependencies:
  - type: blocks
    target: is-01m1npp70ve3p6fyj8n5qt2xx4
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T07:56:16.494Z
updated_at: 2026-09-04T09:49:12.501Z
closed_at: 2026-09-04T09:49:12.500Z
close_reason: All local Python 0.8.0 validation and artifact gates passed
resolution: null
duplicate_of: null
---
Run the documented locked lint, type, conformance, golden, idempotence, pytest, build, metadata, and installed wheel/sdist smoke gates. Verify supported Python versions in hosted CI and ensure no gate is vacuous or polluted by local ignored artifacts.

## Notes

Python 0.8.0 release validation complete on the prepared tree: make lint-check clean; 527 active shared conformance cases pass; 556 pytest tests pass; 145 tryscript CLI goldens pass; golden coverage passes; skills-ref 0.1.5 validates the public skill; frozen pip-audit 2.10.0 reports no known vulnerabilities; make build succeeds; exact UV_DYNAMIC_VERSIONING_BYPASS=0.8.0 wheel/sdist have correct metadata; wheel installs and both flowmark/flowmark-py entry points report v0.8.0; six-mode old/new cross-port differential over 1,677 tracked UTF-8 Markdown docs reports zero newly divergent outputs.
