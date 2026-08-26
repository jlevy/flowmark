---
type: is
id: is-01m0yfybntamn9fw3nefnr2fpt
title: Support atomic --output for one direct input file
kind: bug
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y042abxn1c7w256z31w81j
parent_id: is-01m0xn1kf4s20aga85f298dzww
created_at: 2026-08-26T07:35:51.737Z
updated_at: 2026-08-26T09:34:26.384Z
closed_at: 2026-08-26T09:34:26.382Z
close_reason: Implemented atomic explicit output for one direct file while retaining deterministic multiple-file rejection. Native routing tests, FM-CLI-OUTPUT-001, and all file-ops tryscript cases pass in commit 8e7d178.
resolution: null
duplicate_of: null
---
Implement the intentional FM-CLI-OUTPUT-001 behavior exposed by the shared preservation I/O matrix.

Current Python v0.7.3 rejects flowmark --output output.md input.md even for exactly one resolved input, although stdin-to-output works. Permit one direct resolved file to write atomically to the requested output, retain the multiple-input guard, and keep source/input bytes unchanged.

Update:
- src/flowmark/reformat_api.py::reformat_files() single-file output routing;
- Python direct unit coverage only for routing/error invariants;
- tests/tryscript/file-ops.tryscript.md FO4b/FO4c from documented error to exact successful behavior;
- shared preservation.math.io.output-file case under FM-CLI-OUTPUT-001;
- public docs/help wording if necessary;
- Rust CLI/reformat routing in the direct port with the identical shared case.

Acceptance: one direct file plus --output succeeds atomically, multiple files plus --output still fail deterministically, input remains unchanged, shared before/after tree matches exactly, and Python/Rust exit/stdout/stderr/file bytes are identical.
