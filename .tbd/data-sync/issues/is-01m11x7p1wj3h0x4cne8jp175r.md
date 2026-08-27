---
type: is
id: is-01m11x7p1wj3h0x4cne8jp175r
title: Interior BOM with leading whitespace is not a fixed point in either port
kind: bug
status: open
priority: 3
version: 2
labels:
  - idempotence
  - parity
  - preservation
dependencies: []
created_at: 2026-08-27T15:25:52.060Z
updated_at: 2026-08-27T15:25:58.772Z
---
Found by the generated-input property test added for fmr-htol. Like fmr-c6xs
this is a SHARED bug: Python and Rust both fail to reach a fixed point, so the
language-neutral corpus does not catch it.

## Reproducer: 7 bytes

Input `" \ufeff\t\\("` — space, interior U+FEFF, tab, escaped open paren
(hex `20 ef bb bf 09 5c 28`):

    flowmark-rs (this branch):  " \\(\n"       -> "\\(\n"        -> stable
    Python flowmark 9e9fd7c:    "\ufeff \\(\n" -> "\ufeff\\(\n"  -> stable

Both keep a leading space on the first pass and drop it on the second, so
neither is idempotent. They also disagree on the interior BOM: Python re-emits
one at the start of the document, Rust does not.

flowmark-rs v0.3.2 produced a fenced code block here instead (the tab made it an
indented code block), so the shape changed with the preservation work, but the
non-idempotence is present in Python too and is not a Rust-only regression.

## Why it matters

Same class as fmr-c6xs: `flowmark --check` reports a file the formatter itself
just wrote. Degenerate input, but the fixed-point guarantee should hold for
every input or the --check contract is not trustworthy.

## Suggested handling

Decide whether an interior U+FEFF is content or a stray BOM, pin the intended
bytes as a shared malformed-fallback case with `idempotent = true`, then align
both ports. Rust tracks this as fmr-uao3; Python tracks it as fm-jtwj.
