---
type: is
id: is-01m11w25y7epjy7fyfr24j11sx
title: Share unterminated-fence escape cases for Rust parity
kind: task
status: closed
priority: 2
version: 5
labels:
  - parity
  - preservation
  - pr-review
dependencies: []
created_at: 2026-08-27T15:05:23.142Z
updated_at: 2026-08-27T16:42:45.112Z
closed_at: 2026-08-27T16:42:45.111Z
close_reason: "Added the language-neutral FM-FENCED-CODE-001 regression on PR #71 at 85b6093; Rust PR #81 consumes it at c50df77. Full local validation and both hosted CI matrices passed."
resolution: null
duplicate_of: null
---
Found during independent verification of flowmark-rs PR #81 at head f833ce8.
Python behaves CORRECTLY here; this is a Rust divergence, but it needs a shared
case so the contract pins the agreed behavior.

## Inputs (no trailing newline)

Case A, pre-existing Rust bug (Rust flowmark-rs bead fmr-5vfu):

    ```\`

- Python 9e9fd7c: "```\`\n" -> stable, backslash preserved (correct)
- Rust v0.3.2 and f833ce8: "````\n" -> "````\n````\n", drops the backslash and
  is non-idempotent

Case B, Rust PR regression (flowmark-rs bead fmr-sh2b):

    ```\$`$

- Python 9e9fd7c: "```\$`$\n" -> stable, backslash preserved (correct)
- Rust v0.3.2: "```$`$\n" -> stable (drops backslash but idempotent)
- Rust f833ce8: "```$`$\n" -> "```$`$\n```\n", newly non-idempotent

## Ask

Add both to the shared preservation manifest as malformed-fallback cases with
declared idempotence, following the pattern used by
preservation.extension.callout.adjacent-inline (fm-e7n5), so the Rust port has
an executable target for the fix and the escape-inside-unterminated-fence
behavior is pinned for both languages.

No Python code change is expected; Python already produces the desired bytes.

## Notes

Reopened: Shared golden exists only on a side branch; reopen until it lands on PR #71 and the Rust submodule/mapping consumes it.
