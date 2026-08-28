---
type: is
id: is-01m133zbj3ga465wjt0vfveecg
title: Link reference definition titles lose their delimiters and duplicate the link
kind: bug
status: closed
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - parity
  - commonmark
dependencies: []
parent_id: is-01m10nx6jr7fn9m30d8b483fm5
created_at: 2026-08-28T02:42:53.635Z
updated_at: 2026-08-28T02:43:29.732Z
closed_at: 2026-08-28T02:43:29.732Z
close_reason: "Fixed: title/dest delimiters unwrapped before matching, definitions kept verbatim; shared case link-reference-definition.title-delimiters pins both ports."
resolution: null
duplicate_of: null
---
Marko stores a `LinkRefDef`'s destination and title exactly as authored, delimiters
included, while an inline `Link` carries the parsed inner text. `render_link` compared the
two forms directly, so a link whose definition used a single-quoted or parenthesized
title, or an angle-bracketed destination, never matched its own definition.

The consequences compounded:

- `render_link_ref_def` re-quoted the stored title, turning `'title'` into `"'title'"` and
  `"foo\"bar"` into `"foo\\"bar"` — the delimiters and escapes became part of the title
  text.
- The unmatched link was written as an inline link while the (now wrong) definition was
  still emitted, so the same destination appeared twice.
- With preservation active, an angle-bracketed destination is a protected region, so the
  duplicated token made `restore_source` fail closed: CommonMark example 195 exited 2
  with "preservation token stream is missing, duplicated, or malformed" where the same
  input formatted successfully before PR #71. That escalation is what made this a blocker
  rather than a backlog item.

## Fix

`_ref_def_title_text` and `_ref_def_dest_text` unwrap the stored form before comparison,
and `render_link_ref_def` keeps an already-delimited title verbatim instead of re-quoting
it. CommonMark examples 193, 194 and 200 change from the buggy output to the correct one
and their goldens were regenerated through `make accept-conformance`; 195, 196 and 202
improve within the deferred set.

Rust needed no change and now matches Python on every shape the new shared case covers:
`link-reference-definition.title-delimiters`, change ID `FM-LINK-REF-DEF-001`.

## Verification

    540 pytest, 520 conformance cases, 145 tryscript assertions, lint clean.
    Corpus idempotence: 0 regressions against the PR base, 120 checks fixed,
    and all 12 hard errors cleared.
