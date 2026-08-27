---
type: is
id: is-01m0zvn7xdfw27zbdpf54kcabm
title: Complete source-exact GitLab Flavored Markdown preservation
kind: bug
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - glfm
  - preservation
  - parity
dependencies: []
parent_id: is-01m0zvmjwn7hmgcxs7vs5d4py0
created_at: 2026-08-26T20:19:50.315Z
updated_at: 2026-08-27T05:14:50.963Z
closed_at: 2026-08-27T05:14:50.962Z
close_reason: "Completed the unresolved source-destructive GLFM forms from issue #67 with five language-neutral fixed-point cases and direct Python/Rust implementations. Both ports preserve the same recognized source regions and fail closed for lookalikes; the issue ledger and stable FM-EXT-GLFM-001 mapping are reviewed."
resolution: null
duplicate_of: null
---
Issue #67 still has exact forms that are not protected correctly. Reproduce and fix at least the paired GitLab blockquote form using `>>>` delimiters and bracketed directive/reference text such as `[issue:_123_]`, then reconcile every syntax family and example in the issue ledger against the current implementation.

Add the missing cases to the upstream language-neutral corpus before changing either port. Cover valid forms, nesting and adjacency, quote/list containers, Unicode and escapes, malformed or unmatched fallbacks, CRLF/BOM normalization boundaries, all transform modes, and second-pass idempotence. Preserve complete recognized source regions without making ordinary Markdown more opaque.

Acceptance requires the same stable case IDs and exact expected bytes to pass in Python and Rust, the issue #67 family ledger to be complete and reviewed, and the public support catalog to withhold an unqualified GLFM claim until all tracked forms pass.

## Notes

Completed as shared-first FM-EXT-GLFM-001. Five shared desired-output cases cover recognized references, headings/lists/links/quotes/GFM tables (including reference-owned pipes), paired >>> blocks, list/quote containers, Unicode and transform shielding, unknown/escaped/empty/unmatched/code-contained fallback, and two-pass idempotence. Layered core cases own BOM/CRLF and CLI-mode normalization, per the approved golden design. Python and Rust both pass unchanged exact bytes; Rust reports 483 exact cases overall with the unchanged 34 CommonMark ledger entries.
