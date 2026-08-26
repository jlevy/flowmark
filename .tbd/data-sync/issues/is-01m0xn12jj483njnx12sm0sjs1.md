---
type: is
id: is-01m0xn12jj483njnx12sm0sjs1
title: "Markdown preservation: never corrupt what the parser does not model"
kind: epic
status: open
priority: 1
version: 15
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
child_order_hints:
  - is-01m0xn2b9tnj99k484920ysv9z
  - is-01m0xn1k559xy7eg2a2zgpxqy5
  - is-01m0xn1kf4s20aga85f298dzww
  - is-01m0xn1krnmt64xkaw4dkzvc3k
  - is-01m0xpsz0wkaw5gvdzc6q1xa9b
  - is-01kyss8ewf9ys49pyefybdyyw9
  - is-01kyss8fvgc7k0yb2xqjz8b0h2
  - is-01kyss8gskyz68yaky5j8vrnpx
  - is-01m0xn1zpgf7kqp6wz03ngqega
  - is-01m0y0gk7fpnyp7bhqrmpfq89x
created_at: 2026-08-25T23:45:29.170Z
updated_at: 2026-08-26T17:58:29.717Z
---
Top-level implementation epic for the accepted lossless-preservation and language-neutral conformance architecture.

Order:
1. Establish the shared built-CLI corpus and all reusable upstream test layers.
2. Define desired math behavior in shared red cases.
3. Implement the Python preservation core and math.
4. Port the same change IDs directly to Rust and prove zero divergence.
5. Add source-exact inline code in the same shared-first sequence.
6. Add other Markdown extension families as end-to-end Python/Rust vertical slices.

The scanner is a portable pre-parse UTF-8 byte state machine with typed regions, a collision-safe side table, structured wrapping metadata, and fail-closed restoration. Post-parse regex repair, copied Rust fixtures, Python-generated Rust truth, and test-count parity are superseded. Children carry exact file/function scopes and dependencies; the linked spec is the normative behavior.

## Notes

All in-scope Python behavior, shared language-neutral tests, Rust implementation, integration closeout, and corpus provenance work are locally complete at Python b027fde and Rust 90203d2. The only program blocker is fm-zah1 under Phase 2A: publish the exact Python submodule commit and prove a fresh recursive clone/remote CI.
