---
type: is
id: is-01m0xn1zpgf7kqp6wz03ngqega
title: Document the test corpora and recover attic/test-docs provenance
kind: task
status: open
priority: 2
version: 1
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
created_at: 2026-08-25T23:45:58.991Z
updated_at: 2026-08-25T23:45:58.991Z
---
scripts/corpus-parity-check.sh defaults to attic/test-docs, 623 real-world files. attic/ is gitignored so the corpus is not checked in, and no document in either repo records what those files are, where they came from, or how to rebuild the set. Seven mentions exist across both repos and all are the default path, the file count, the word curated, or how to work around its absence. The gate has already run degraded twice, honestly recorded: 60 tracked files on 2026-05-28 and a repo-Markdown spot-check on 2026-05-30. Recover the provenance from the maintainer, then either check in a redistributable subset or document the reconstruction procedure. The spec has a corpora table covering all six corpora; keep it as the single reference.
