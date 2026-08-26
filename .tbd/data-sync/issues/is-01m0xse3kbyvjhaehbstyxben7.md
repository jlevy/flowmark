---
type: is
id: is-01m0xse3kbyvjhaehbstyxben7
title: "M3 fix: route smartquotes and ellipses through iter_atomic_spans"
kind: bug
status: open
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn1kf4s20aga85f298dzww
created_at: 2026-08-26T01:02:30.507Z
updated_at: 2026-08-26T01:02:58.904Z
---
Sites: src/flowmark/typography/smartquotes.py and src/flowmark/typography/ellipses.py.

These operate on text independently of wrapping, so M1 will not fix them. Measured: $x'y$ becomes $x’y$ on a SHORT line with no wrap boundary anywhere, and a curly quote is not valid TeX.

The trigger is narrower than it first looks and the tests should encode that precisely: the apostrophe curls only between two word characters. $x'y$ and $n'th$ are rewritten; $f'(x)$, $a'$, $x' + y$ and $\alpha'\beta$ are not. Straight double quotes inside a span are also curled.

Approach: route both transforms through iter_atomic_spans and rewrite only the non-atomic gaps — the same mechanism as fm-9ey6, which is the argument for doing them together or at least consistently.

Side effect to decide before landing: this also stops smartquotes and ellipses firing inside CODE spans and links. Check whether that is a change from today. Fixture code-inline.md sections C4 and C5 measured as already correct, so it may be a no-op there — confirm rather than assume, and if it does change output, that belongs in the changelog.

Verify against math.md sections C8, C9, C10 and C11. C8 carries both a triggering form ($x'y$) and a non-triggering one ($f'(x)$) as a contrast pair.
