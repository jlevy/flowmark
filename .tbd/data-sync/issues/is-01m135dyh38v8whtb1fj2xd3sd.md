---
type: is
id: is-01m135dyh38v8whtb1fj2xd3sd
title: "Defect A: a wrapped line beginning with '=' becomes a setext underline"
kind: bug
status: open
priority: 1
version: 1
labels:
  - idempotence
dependencies: []
parent_id: is-01m12nfv9cedx3ma4crtcmjv01
created_at: 2026-08-28T03:08:20.386Z
updated_at: 2026-08-28T03:08:20.386Z
---
Wrapping can push `=` to the start of a continuation line, where the next parse reads it
as a setext H1 underline. The list text above it is promoted to a heading and the list
structure is destroyed, so this is content corruption rather than a spelling difference —
the most serious item the idempotence audit found.

    printf -- '- alpha beta gamma delta epsilon word =\n' | flowmark --width 20 -

Run the result through again and the list is gone.

Six ledger entries, all in `narrow` mode: the five reference testdocs and the raw-HTML
angle-comparisons case. flowmark-rs carries the identical defect as fmr-6zg6, with seven
entries (it also reaches `parity-corner-cases.md`).

Per project convention the intended bytes are agreed here first, pinned as a shared case,
fixed here, and only then replicated in flowmark-rs. Wrapping must not emit a line that
reparses as block structure, so the fix likely belongs in the wrapper's hazardous-prefix
guard rather than in the parser.
