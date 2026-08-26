---
type: is
id: is-01m0y06s6yse0c28j4fa8mz1vs
title: Port source-exact inline code spans to Rust and prove shared parity
kind: task
status: closed
priority: 1
version: 8
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y08y0hrt3jw0wmxpb0yzm3
  - type: blocks
    target: is-01m0y08yazbdhdyj1a450qdjfa
  - type: blocks
    target: is-01m0y08yndjbv5a1832kbagpd6
  - type: blocks
    target: is-01m0y08z09p26pakg08h937pfd
  - type: blocks
    target: is-01m0y08zeydjc34a7dyd0feamy
parent_id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
created_at: 2026-08-26T03:00:50.523Z
updated_at: 2026-08-26T11:36:45.315Z
closed_at: 2026-08-26T11:36:45.314Z
close_reason: Rust source-exact code-span parity proven by the shared corpus and focused native diagnostics.
resolution: null
duplicate_of: null
---
Bump ../flowmark-rs/repos/flowmark to the reviewed Python code-span commit and port FM-CODE-SPAN-001 through the existing Rust preservation package.

Files:
- src/preservation/scanner.rs and registry.rs: exact backtick-run recognizer and composite-math arbitration.
- src/formatter/filling.rs and src/wrapping/text_wrapping.rs: route code tokens through the same side table, transform skipping, logical widths, and exact restoration.
- tests/test_preservation.rs: only small native scanner/adapter diagnostics.
- shared runners: consume all code-span manifest, tryscript, topic, reference, and CommonMark assets through repos/flowmark.

Retire renderer/placeholder workarounds only when replacement coverage is green. Do not translate Python unit tests or add a divergence entry. Acceptance: every FM-CODE-SPAN-001 case and shared integration layer passes exact bytes in Rust, C1/C2 have the same closure evidence, and the port ledger names the upstream commit/change IDs.

## Notes

Implemented in Rust commit b040416 against pinned Python contract 921a47e. The scanner now preserves valid code spans through the same side table; token-aware typography supplies immutable CommonMark-normalized code context while restoring exact authored bytes. All 29 FM-CODE-SPAN-001 cases pass twice, full shared conformance passes at 433 exact plus 35 current divergences, and Rust smartquote/parity/edge suites, clippy, fmt, and tryscript pass.
