---
type: is
id: is-01m0xse38rtqj4zy9m2k5f1awj
title: "M1 fix: add inline math atomic patterns for $…$, one-line $$…$$ and \\(…\\)"
kind: bug
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn1kf4s20aga85f298dzww
created_at: 2026-08-26T01:02:30.167Z
updated_at: 2026-08-26T02:58:28.474Z
---
Site: src/flowmark/linewrapping/atomic_patterns.py. Add three AtomicPattern entries beside INLINE_CODE_SPAN and MARKDOWN_LINK, then list them in ATOMIC_PATTERNS and in MARKDOWN_INLINE_PATTERNS (a sentence boundary must not fire inside a formula either).

Ordering: $$ before $, and both AFTER INLINE_CODE_SPAN. Resolved decision — code spans stay first, because treatment is identical so the two readings of the GitLab dollar-backtick form emit identical bytes, and the existing order wins on risk. A test pins it.

Delimiter rule for $…$, the union of the strictest Pandoc and GitHub constraints:
1. opening $ not backslash-escaped and not preceded by an alphanumeric
2. character after the opening $ is not whitespace
3. character before the closing $ is neither whitespace nor a backslash
4. character after the closing $ is not a letter or digit
5. no newline between them

Body rule, and it is load-bearing: the body may contain an escaped \$ but never a bare $. As a fragment: (?:[^$\n\\]|\\.)+? — the simpler "exclude $ entirely" loses real math. Verified against the interleaved line in tests/testdocs/testdoc.orig.md (three math spans, two currency amounts, escaped dollars inside the math): the permissive body finds 3 of 3 true spans and captures neither currency; excluding $ finds 1 of 3.

\(…\) has unambiguous delimiters and needs only the no-newline constraint.

M2 (escape injection) requires no separate change: once a span is one atomic word, _md_specials_pat in text_wrapping.py:63 cannot match it, since that pattern is anchored to the whole word. Add a test that would fail if atomicity regressed.

Verify against tests/tryscript/fixtures/content/math.md: A2, A3, A4 and C1-C12 currently fail; A5, A6 and all of Part D pass today and are regression cover — especially D2, D3, D8 and D11, which are what the delimiter rule exists to protect.
