---
type: is
id: is-01m1nqy6dxb2wyjp59wavy69ff
title: Include input paths in invalid UTF-8 file errors
kind: bug
status: closed
priority: 1
version: 5
labels:
  - release-blocker
  - compatibility
dependencies:
  - type: blocks
    target: is-01m1npp6qfkack71ng8czs2qdf
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T08:18:06.908Z
updated_at: 2026-09-04T08:22:16.312Z
closed_at: 2026-09-04T08:22:16.306Z
close_reason: Python now provides path-aware named-file UTF-8 errors without changing stdin or atomicity; shared contract is ready for the release-prep PR.
resolution: null
duplicate_of: null
---
Current Python main reports only 'input is not valid UTF-8' for a named file. Rust synchronized to that output and thereby regressed from flowmark-rs v0.3.2, which named the offending path. Keep stdin diagnostics generic, but make file API/CLI failures include the caller-supplied path, update the shared file conformance case upstream first, and prove failed in-place formatting remains atomic. Batch continuation is separate follow-up scope.

## Notes

Evidence (2026-09-04): changed the Python InvalidUtf8Error to carry an optional caller path and reformat_file to supply it only for named inputs. Added exact API and CLI tests for output/check modes and updated the shared in-place no-mutation expected stderr. Stdin remains generic. Focused API/CLI tests pass; shared named-file and stdin cases both pass.
