---
type: is
id: is-01m0xscdmzyb7m84p8mtscn2j5
title: "C2 fix: exclude atomic spans from the paragraph whitespace normalisation"
kind: bug
status: open
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0xsczjbncpddwkvxsehvmsz
  - type: blocks
    target: is-01m0xse38rtqj4zy9m2k5f1awj
parent_id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
created_at: 2026-08-26T01:01:35.262Z
updated_at: 2026-08-26T01:02:59.486Z
---
Sites, all in the paragraph wrap path:

1. src/flowmark/linewrapping/text_wrapping.py:112 and :118, inside wrap_paragraph_lines — two calls to re.sub(r"\s+", " ", text), one on the width<=0 early return and one on the normal path. Both run BEFORE the splitter tokenizes, so a span's interior is normalised before anything marks it atomic.
2. src/flowmark/linewrapping/line_wrappers.py:130 — " ".join(text.split()) on the no-wrap branch, the same collapse by another route.

Entry point is line_wrappers.py:145, the by-sentence wrapper calling wrap_paragraph_lines per sentence; that is reached from flowmark_markdown.py:425 where the paragraph renderer calls self._line_wrapper.

Why the context asymmetry in the measurement: render_heading (flowmark_markdown.py:564) and the table renderer never call the line wrapper, so C2 does not fire in headings or table cells. Those two paths are the reference for correct behaviour — they already preserve interiors. The fix belongs where the paragraph path diverges from them.

Approach: normalise only the non-atomic gaps. iter_atomic_spans (src/flowmark/linewrapping/atomic_patterns.py) already yields alternating atomic and non-atomic spans covering the input exactly, so run the whitespace collapse per non-atomic span and pass atomic spans through untouched. Preferred over protecting-then-restoring because it reuses the tokenizer that already defines "atomic" rather than adding a second notion of it.

Must preserve the one correct behaviour measured here: a line ending INSIDE a span still becomes a space, per CommonMark 0.31.2 section 6.1. Only runs of spaces and tabs are significant. Fixture section B6 is that regression cover.

Verify against tests/tryscript/fixtures/content/code-inline.md sections B1-B6 and D1-D6. B3 and B6 pass today and must keep passing; B1, B2, B4, B5 and D1-D4 currently fail. D5 (heading) and the padded-cell half of D6 already pass and must not regress.

Note the interaction with fm-fa8p: once C1 pads correctly, an all-space content case must not then be stripped by this path either.
