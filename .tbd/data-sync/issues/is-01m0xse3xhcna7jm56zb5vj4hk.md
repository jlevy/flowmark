---
type: is
id: is-01m0xse3xhcna7jm56zb5vj4hk
title: "M4 fix: make display-math blocks opaque instead of reflowing them"
kind: bug
status: open
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn1kf4s20aga85f298dzww
created_at: 2026-08-26T01:02:30.833Z
updated_at: 2026-08-26T01:02:59.197Z
---
Site: src/flowmark/linewrapping/block_heuristics.py, the block-level path — the analogue of the inline atomic mechanism.

Every display form that is not a fenced code block is currently flattened onto one line. Only ```math and ```{math} survive, and only because a code fence is already opaque.

Regions to make opaque, each opened and closed on its own line:
- $$ ... $$
- \[ ... \]
- \begin{env} ... \end{env}

Emit verbatim, line structure included. Non-whitespace characters already survive today, so the formula usually still renders; what is lost is the line structure of an aligned environment, and every edit to such a block then produces whole-block diff noise.

Open question to settle here: restrict \begin{} to a known environment list (equation, align, gather, matrix, ...) or accept any \begin{word}? Accepting any matches the preserve-don't-parse principle and is the current recommendation.

This changes a checked-in golden. tests/testdocs/testdoc.expected.auto.md line 111 records the collapsed form "$$ L = \frac{1}{2} \rho v^2 S C_L $$" as expected output for a three-line input block, so the corruption is baked into the test suite. Regenerating that golden is evidence the fix works, not a regression — say so in the commit.

In the Rust port this maps onto the existing PUA-marker passthrough in src/formatter/filling.rs (the COMRAK-WORKAROUND mechanism), not new infrastructure.

Verify against math.md sections B1, B2, B3, B4, B7 and E3. B5 and B6 (the fenced forms) pass today and are regression cover.
