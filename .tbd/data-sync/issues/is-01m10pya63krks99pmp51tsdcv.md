---
type: is
id: is-01m10pya63krks99pmp51tsdcv
title: Remove the preservation-spec entry from .flowmarkignore
kind: task
status: closed
priority: 2
version: 2
labels: []
dependencies: []
created_at: 2026-08-27T04:16:39.106Z
updated_at: 2026-08-27T04:58:30.319Z
closed_at: 2026-08-27T04:58:30.318Z
close_reason: "Removed the obsolete preservation-spec exclusion after source-exact code spans and issue #58 coverage landed. Formatted the spec with Flowmark auto mode, verified the result is a fixed point with --auto --check, and retained the spec as a live real-world preservation regression."
resolution: null
duplicate_of: null
---
Review suggestion from PR #71 (jlevy/flowmark#71): 'Once #58 is fixed, use this preservation spec itself as a real-world regression case before removing it from .flowmarkignore.'

Verified at PR head 783b445 that this is now safe. Formatting docs/project/specs/active/plan-2026-08-25-markdown-preservation.md produces:
- no construct corruption: the three code spans containing fenced-block info strings and the GitLab dollar-backtick form all survive byte-exactly
- a pure reflow diff only (file is authored at ~92 cols, flowmark wraps at 88); word order identical, blockquote '>' prefix count unchanged (3 -> 3)
- a fixed point: F(F(x)) == F(x)

Action: drop the trailing .flowmarkignore entry and re-run 'make format-docs' so the spec becomes a live regression case.
