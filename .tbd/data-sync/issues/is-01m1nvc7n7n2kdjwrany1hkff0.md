---
type: is
id: is-01m1nvc7n7n2kdjwrany1hkff0
title: Recover Python formatter throughput after preservation expansion
kind: bug
status: closed
priority: 1
version: 3
labels:
  - release-blocker
  - performance
dependencies: []
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T09:18:12.616Z
updated_at: 2026-09-04T09:39:17.955Z
closed_at: 2026-09-04T09:39:17.940Z
close_reason: Release performance blocker resolved with full correctness and differential evidence
resolution: null
duplicate_of: null
---
A release-audit benchmark on tests/testdocs/testdoc.orig.md (81,548 characters, 1,428 lines) measured current main at 426 ms mean versus published 0.7.3 at 219 ms mean over five semantic-mode iterations, about 1.95x slower. Reproduce with warm runs in semantic and default wrapping, profile the added preservation pipeline, verify scaling remains linear, and optimize avoidable work before 0.8.0 or explicitly stop the release if prior-release throughput cannot be preserved safely.

## Notes

Resolved the release-blocking Python throughput regression with scanner admission/recognizer gates, single-pass UTF-8 offset construction, cached byte-to-scalar lookups, and scalar coordinates on container lines. Focused preservation tests: 61 passed. Full release gates: lint/type clean, 527 active shared cases pass, 556 pytest pass, 145 CLI goldens pass. Twenty-iteration comparison against 0.7.3 on the 81,548-character stress document improved from 1.95x/4.26x slower to 1.20x semantic and 0.89x plain by mean despite scheduler noise; the residual semantic cost exercises the newly supported protected syntaxes. Six-mode four-way differential over 1,677 tracked UTF-8 Markdown documents remains at zero newly divergent Python/Rust outputs in every mode.
