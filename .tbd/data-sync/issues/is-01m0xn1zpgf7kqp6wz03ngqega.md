---
type: is
id: is-01m0xn1zpgf7kqp6wz03ngqega
title: Document the test corpora and recover attic/test-docs provenance
kind: task
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
created_at: 2026-08-25T23:45:58.991Z
updated_at: 2026-08-25T23:55:38.585Z
---
scripts/corpus-parity-check.sh defaults to attic/test-docs, 623 real-world files. attic/ is gitignored so the corpus is not checked in, and no document in either repo records what those files are, where they came from, or how to rebuild the set. Seven mentions exist across both repos and all are the default path, the file count, the word curated, or how to work around its absence. The gate has already run degraded twice, honestly recorded: 60 tracked files on 2026-05-28 and a repo-Markdown spot-check on 2026-05-30. Recover the provenance from the maintainer, then either check in a redistributable subset or document the reconstruction procedure. The spec has a corpora table covering all six corpora; keep it as the single reference.

## Notes

Research findings, verified across flowmark, flowmark-rs and rust-porting-playbook including git history.

DOCUMENTED — the attic convention itself. `attic/` is a gitignored, machine-local scratch directory: the same place third-party checkouts go under tbd's `checkout-third-party-repo` shortcut, which creates the directory and adds it to `.gitignore`. It persists across sessions on one machine and is never tracked. So `attic/test-docs` is by construction local to whoever assembled it.

NOT DOCUMENTED — the contents. Nothing under `attic/` was ever committed (`git log --diff-filter=A -- "attic/*"` is empty). No download or assembly step exists in any of the three repos. `corpus-parity-check.sh` arrived 2026-02-19 already defaulting to the path, with no accompanying creation step. The porting playbook describes corpus methodology but names no source.

CONSEQUENCE — a container session cannot have that directory, so every fresh session finds it missing. A senior review flagged the non-reproducibility on 2026-05-28; the response documented a substitute (60 tracked repo files) rather than the original, and two later syncs recorded the same substitution. The script exits 2 when the directory is absent, so the degradation is a human decision taken in the open each time, not a silent failure.

MOST LIKELY — a local directory on the maintainer's machine that predates the port. The answer lives there, not in any repository, so this needs jlevy to recover it.

RELATED — fm-o5vk (CommonMark-seeded shared corpus, stalled at Draft) is the structural fix for the same problem: a corpus that is checked in and reproducible needs no provenance archaeology.
