---
type: is
id: is-01m11x4c1ykrefwx8400n52j2h
title: Escaped backslash in a fence info string loses one escape level per pass
kind: bug
status: open
priority: 2
version: 2
labels:
  - idempotence
  - parity
  - preservation
dependencies: []
created_at: 2026-08-27T15:24:03.518Z
updated_at: 2026-08-27T15:24:12.080Z
---
Found by the generated-input property test added for fmr-htol. This is a SHARED
bug: Python and Rust agree with each other and both are wrong, so the shared
conformance corpus does not catch it.

## Reproducer: 6 bytes

Input `~~~\\[` (hex `7e 7e 7e 5c 5c 5b`), a tilde fence whose info string holds
an escaped backslash followed by an escaped bracket:

    pass 1: "~~~\\[\n~~~\n"   -> renders the escaped backslash as one backslash
    pass 2: "~~~[\n~~~\n"     -> that backslash is consumed too
    pass 3: stable

Confirmed identical on flowmark-rs v0.3.2, flowmark-rs PR #81 head f833ce8, and
Python flowmark 9e9fd7c. Every implementation loses one level of escaping per
formatting pass until none is left.

## Why it matters

`flowmark --check` reports a file the formatter itself just wrote, so a
pre-commit hook or CI gate fails on its own output. It also silently rewrites
authored content on repeated runs, which is the class of defect the preservation
contract exists to prevent.

## Suggested handling

Decide the intended bytes for an escape sequence in a fence info string, add a
shared malformed-fallback case with `idempotent = true` to the language-neutral
manifest, then fix both ports to match. Rust tracks this as flowmark-rs bead fmr-c6xs; this bead is fm-ww33.
