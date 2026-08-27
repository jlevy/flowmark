---
type: is
id: is-01m12nfv9cedx3ma4crtcmjv01
title: Document and fix idempotence gaps in the Python reference implementation
kind: epic
status: open
priority: 1
version: 1
labels:
  - idempotence
  - parity
dependencies: []
created_at: 2026-08-27T22:29:45.387Z
updated_at: 2026-08-27T22:29:45.387Z
---
Idempotence audit of the Python reference implementation, run alongside the same audit
of flowmark-rs so the two can be compared directly.

## Method

Every Markdown document the shared corpus ships (plus the port's own docs), formatted
twice in process and compared byte for byte, across six modes: default, semantic,
cleanups, full typography, width 0, width 40. Python at 9e9fd7c, Rust at flowmark-rs
c00f74b.

## Result

    Python:  9,168 checks, 138 failing (1.51%), 28 distinct files
    Rust:    9,114 checks,  68 failing (0.75%), 18 distinct files
    overlap: 54 checks, 14 files
    Python only: 84 checks, 14 files
    Rust only:   14 checks,  4 files

Python, the reference implementation, is the less stable of the two. About two thirds of
its instability has no Rust counterpart, so fixing it will change bytes the port must
then match.

## Python-only defect classes

E. Blockquote holding a heading then prose (CommonMark 0228-0232). Passes oscillate
   between splitting the quote in two and rejoining it:
     input   "> # Foo\n> bar\n> baz\n"
     pass 1  "> # Foo\n\n> bar baz\n"
     pass 2  "> # Foo\n> bar baz\n"

F. Nested list indentation (CommonMark 0307, 0315). The second pass inserts a blank line
   after the outer item, turning a tight list loose:
     pass 1  "- foo\n  - bar\n\n    - baz\n\n      bim\n"
     pass 2  "- foo\n\n  - bar\n\n    - baz\n\n      bim\n"

Rust is stable on both shapes today, so aligning after a Python fix may require a Rust
change too.

## Shared classes (also in Rust)

A. A wrapped line beginning with '=' is reparsed as a setext H1 underline, promoting list
   text to a heading and destroying the list. Content corruption, and the most serious
   item found. Reproducer:
     printf -- '- alpha beta gamma delta epsilon word =\n' | flowmark --width 20 -
   run twice.
B. Setext heading with multi-line content splits on the second pass (0081, 0082, 0095).
C. Empty ordered-list item dropped, then the list renumbers (0283).
G. Escape sequences in a fence info string lose one level per pass (fm-ww33).
H. Interior U+FEFF with leading whitespace drops a space on the second pass (fm-jtwj).

## Ask

Document scope first; no fixes yet. For each class decide the intended bytes, pin them as
shared cases in the language-neutral manifest, fix here in Python, and only then have
flowmark-rs replicate exactly. Several first passes are already arguably wrong (C drops
an empty list item), so idempotence alone is not the right target without that decision.

Rust-side scope, gate and ledger are tracked in flowmark-rs beads fmr-1xlk (epic),
fmr-6zg6 (A), fmr-gmqc (B/C/D) and fmr-dlu9 (E/F), with the spec at
docs/project/specs/active/plan-2026-08-27-idempotence-verification.md.
