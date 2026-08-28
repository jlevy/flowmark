---
type: is
id: is-01m133znn1655vq0qmn7wbmdfm
title: Escaped link reference destinations and titles still duplicate the link
kind: bug
status: open
priority: 2
version: 1
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - parity
  - commonmark
dependencies: []
parent_id: is-01m10nx6jr7fn9m30d8b483fm5
created_at: 2026-08-28T02:43:03.969Z
updated_at: 2026-08-28T02:43:03.969Z
---
Follow-on to fm-10ra, which unwrapped a link reference definition's authored delimiters
before matching. Backslash escapes are still unresolved on the definition side, so a
definition whose destination or title carries one does not match the link that uses it:

    [Baz]: /url\bar "quo\"ted"

    [Baz]

Python keeps the definition and also writes the link inline, so the destination appears
twice. Rust drops the definition entirely (see the sibling Rust bead) — both ports are
wrong, in different directions.

The definition stores `quo\"ted` while marko's `Link.title` carries the resolved `quo"ted`,
so `_ref_def_title_text` needs to resolve CommonMark backslash escapes (section 2.4:
a backslash before ASCII punctuation) before comparing, and `_ref_def_dest_text` the same.
This was left out of fm-10ra deliberately: it is not part of the PR #71 regression, and
fixing only Python would widen the gap with Rust while that port still drops the
definition. Land both together, with a shared conformance case covering the escaped shape.

Reproduces identically on the PR base 195b5ce, so this is not a PR #71 regression.
