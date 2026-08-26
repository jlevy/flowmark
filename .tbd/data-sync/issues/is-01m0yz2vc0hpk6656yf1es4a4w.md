---
type: is
id: is-01m0yz2vc0hpk6656yf1es4a4w
title: Ellipses after closing curly quotes must match Python and Rust
kind: bug
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0y08z09p26pakg08h937pfd
created_at: 2026-08-26T12:00:27.518Z
updated_at: 2026-08-26T12:02:09.388Z
closed_at: 2026-08-26T12:02:09.387Z
close_reason: Shared TOML desired output now requires a real ellipsis after closing curly quotes; Python regex and focused unit regression fixed in 6831aea, Rust already matched, and both FM-EXT-TOML-FRONTMATTER-001 selectors pass.
resolution: null
duplicate_of: null
---
The TOML-frontmatter shared case revealed that Python leaves three dots after a closing curly quote because ELLIPSIS_PATTERN admits opening curly quotes but not closing ones; Rust already emits the intended ellipsis. Make the language-neutral golden require the ellipsis, fix Python's typography boundary symmetrically, add a focused native regression, and validate both implementations against FM-EXT-TOML-FRONTMATTER-001.
