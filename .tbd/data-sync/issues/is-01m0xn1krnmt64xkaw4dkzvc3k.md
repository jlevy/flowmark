---
type: is
id: is-01m0xn1krnmt64xkaw4dkzvc3k
title: "Track A Phase 3: port math fixes to flowmark-rs and re-establish parity"
kind: task
status: open
priority: 1
version: 1
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
created_at: 2026-08-25T23:45:46.773Z
updated_at: 2026-08-25T23:45:46.773Z
---
Mirror math.md and the tryscript changes into flowmark-rs. Port the fixes to src/wrapping/atomic_patterns.rs, src/formatter/filling.rs and the typography module. Regenerate admin/port-coverage-mapping/*.yaml, bump the literal counts in python/tests/test_smoke.py, and drive test_no_unmapped_entries back to zero. Run scripts/corpus-parity-check.sh and record which corpus it ran against.
