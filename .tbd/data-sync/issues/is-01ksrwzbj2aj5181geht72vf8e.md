---
type: is
id: is-01ksrwzbj2aj5181geht72vf8e
title: "CI: add --check mode to devtools/lint.py and run it in CI (fail on unformatted code)"
kind: task
status: open
priority: 2
version: 3
labels: []
dependencies:
  - type: blocks
    target: is-01ksrx01vtyypaf37nj3tz6tvr
created_at: 2026-05-29T03:38:16.513Z
updated_at: 2026-05-29T03:39:10.085Z
---
Source: simple-modern-uv template devtools/lint.py + ci.yml.
flowmark's devtools/lint.py always mutates files (codespell --write-changes, ruff check --fix, ruff format), and CI runs 'uv run python devtools/lint.py' that way -> CI silently reformats and never fails on unformatted/lint-only issues.
Fix: add argparse '--check' flag that runs codespell (no --write), 'ruff check' (no --fix), 'ruff format --check'; CI runs 'devtools/lint.py --check'. Add a 'lint-check' Make target (template has one). Also switch 'exit(main())' -> 'sys.exit(main())'.
