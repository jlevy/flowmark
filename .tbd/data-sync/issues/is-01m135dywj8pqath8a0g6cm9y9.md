---
type: is
id: is-01m135dywj8pqath8a0g6cm9y9
title: "Defects B and C: setext heading content and empty ordered items are unstable"
kind: bug
status: open
priority: 2
version: 1
labels:
  - idempotence
dependencies: []
parent_id: is-01m12nfv9cedx3ma4crtcmjv01
created_at: 2026-08-28T03:08:20.754Z
updated_at: 2026-08-28T03:08:20.754Z
---
Two shared shapes that both ports carry (flowmark-rs: fmr-gmqc).

**B — setext heading with multi-line content** (CommonMark 0081, 0082, 0095). The first
pass keeps the heading whole; the second splits it, and the trailing line escapes into a
paragraph.

**C — ordered list with an empty item** (CommonMark 0283). The first pass drops the empty
item and the second renumbers what is left. The first pass is already arguably wrong, so
idempotence alone is the wrong target: the intended bytes have to be decided before either
port changes.

36 ledger entries across six documents (each example's input and its golden, in all six
modes).
