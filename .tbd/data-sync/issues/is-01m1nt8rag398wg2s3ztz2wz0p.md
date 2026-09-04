---
type: is
id: is-01m1nt8rag398wg2s3ztz2wz0p
title: Preserve authored sentinel width across collision escaping
kind: bug
status: closed
priority: 1
version: 3
labels:
  - release-blocker
  - parity
  - wrapping
dependencies: []
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T08:58:50.062Z
updated_at: 2026-09-04T09:15:08.568Z
closed_at: 2026-09-04T09:15:08.566Z
close_reason: Restored prior-release and cross-port width behavior with exact shared regression coverage and zero new differences in the full release sweep.
resolution: null
duplicate_of: null
---
The four-way release sweep found a Python 0.7.3 regression: at width 40, collision escaping expands each authored U+F0000/U+F0001/U+F0002 control scalar to two parser-facing scalars, and Python wrapping measures both. Python current therefore wraps the shared sentinel-collision input one word earlier, while Python 0.7.3, Rust 0.3.2, and Rust current agree. Decode canonical authored-marker escapes for logical width measurement, add a narrow shared desired-output case, and prove exact prior-release/cross-port output.

## Notes

Implemented canonical authored-marker escape decoding only for logical width measurement, leaving parser-facing collision protection unchanged. Added an exact narrow shared case with its own uniquely reached fixture. Red evidence measured 9 parser scalars instead of 5 logical scalars and wrapped one word early. Post-fix evidence: focused unit and two-pass shared case pass in both ports; Python full conformance, 555 pytest tests, and 145 tryscript scenarios pass; the 1,677-document four-version sweep across default, semantic, cleanups, typography, nowrap, and width-40 modes reports zero newly divergent current Python/Rust documents.
