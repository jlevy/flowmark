---
type: is
id: is-01m0xn1zcv01nmb6qgtw0nsf1z
title: "C2: whitespace inside a code span is normalised"
kind: bug
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
created_at: 2026-08-25T23:45:58.683Z
updated_at: 2026-08-26T00:17:27.675Z
---
Whitespace inside a code span is normalised, though CommonMark 0.31.2 section 6.1 treats internal runs and tabs as significant.

  `a    b`   ->  `a b`     6 bytes of content become 3
  `  a  `    ->  ` a `     then `a` on a second pass; NOT idempotent, and the rendered content changes too
  `   `      ->  ` `       all-space content is exempt from the strip rule
  `a<TAB>b`  ->  `a b`     tabs are significant inside a span

Correct per CommonMark: line endings inside a span become spaces. That case is regression cover, not a defect.

Cause is ordering rather than intent: the paragraph-level re.sub(r"\s+", " ", text) in wrap_paragraph_lines runs before atomic protection, so a span's interior is normalised before anything declares it untouchable. No test pins the current behaviour.

Context asymmetry is the diagnostic: this fires in paragraphs, list items, blockquotes and link text, but NOT in table cells or headings, which take a different emit path that never reaches the normaliser. So the fix belongs at the point the paragraph path diverges from the ones that already behave.

Precondition for math spans being byte-exact by the same code path rather than a special stricter one.

Reproduced by tests/tryscript/fixtures/content/code-inline.md sections B1, B2, B4, B5, D1-D4.
