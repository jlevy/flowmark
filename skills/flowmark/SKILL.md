---
name: flowmark
description: Fast, consistent Markdown auto-formatter for typographic cleanup (smart quotes, ellipses), normalized formatting, and optional clean line wrapping for small, readable git diffs. Use when creating, editing, or normalizing Markdown (.md) files, cleaning up LLM-generated Markdown, or when the user mentions flowmark or formatting Markdown.
allowed-tools: Bash(flowmark:*), Bash(uvx:*), Read, Write
---
<!-- DO NOT EDIT: `flowmark --install-skill` (format=f02 surface=skill-md) -->

# Flowmark - Markdown Auto-Formatter

Fast, consistent Markdown auto-formatter.
Run it on Markdown you generate or edit so committed diffs stay small and readable.
It is conservative and safe to run on every file: it never modifies code blocks or
inline code.

## Default Usage

Format in place with all auto-formatting (typography, cleanups, semantic line breaks):

```bash
flowmark --auto FILE   # one file
flowmark --auto .      # whole tree (respects .gitignore and .flowmarkignore)
```

Omit `--auto` to preview to stdout; pipe stdin with `-` (e.g. `cat FILE | flowmark -`).

If `flowmark` is not on `PATH`, use a version-pinned runner (never `@latest`):

```bash
uvx --from flowmark==0.7.1 flowmark --auto FILE
```

> Prefer the `flowmark` command when it is on `PATH`. The auto-synced
> [Rust port (flowmark-rs)](https://github.com/jlevy/flowmark-rs) is a fast native
> binary with identical formatting; the Python version is the reference.

## When to Use It

- Auto-format Markdown you create or edit, before committing.
- Normalize and clean up LLM-generated Markdown.
- Typographic cleanup (smart quotes, ellipses) and consistent formatting.
- Optional semantic (sentence-based) line breaks for cleaner git diffs (`--semantic`).

## Full Documentation

Flowmark documents itself.
Use the CLI rather than reproducing details here:

- `flowmark --help` — every flag: `--semantic`, `--smartquotes`, `--ellipses`,
  `--width`, `--check`, list spacing, and file discovery
  (`--extend-include`/`--extend-exclude`).
- `flowmark --docs` — the full guide: editor on-save setup (VS Code/Cursor), project
  wiring (pre-commit/CI, `.flowmarkignore`), config files, the Python library API, and
  installing this skill for other agents (`flowmark --install-skill`).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
