---
type: is
id: is-01m10pyp90kykaqmna4ct4yb02
title: Document the preservation dialect policy and I/O contracts in user-facing docs before release
kind: task
status: open
priority: 2
version: 1
labels: []
dependencies: []
created_at: 2026-08-27T04:16:51.487Z
updated_at: 2026-08-27T04:16:51.487Z
---
Review suggestion from PR #71 (jlevy/flowmark#71): 'Record the normative dialect/superset policy, complexity guarantee, encoding/newline contract, and compatibility choice in user-facing docs before release.'

Verified still open at PR head 783b445. These contracts are pinned in docs/project/architecture/current/language-neutral-conformance-corpus.md, which is project-internal. README.md has no coverage: grep for preserv|math|dialect|opaque returns 5 incidental hits (frontmatter, --list-spacing, offset-preserving tokenizers) and nothing on the math/preservation policy.

To document before release:
- the preservation-biased default recognizer as a superset of Pandoc/MyST/GitHub dollar forms, with no dialect flag required
- O(n) scanning guarantee
- encoding/newline contract: strict UTF-8, BOM retained, CRLF normalized to LF, terminal newline added
- compatibility: public iter_atomic_spans span names/offsets are unchanged
