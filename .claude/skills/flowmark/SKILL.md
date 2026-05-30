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

Flowmark ships as two packages with identical formatting and the same `flowmark`
command: the fast native Rust port [`flowmark-rs`](https://github.com/jlevy/flowmark-rs)
(recommended) and the Python reference [`flowmark`](https://github.com/jlevy/flowmark).
Prefer flowmark-rs; reach for the Python build only when you need its library API or the
very latest patch release not yet ported to Rust.
If `flowmark` is not on `PATH`, run it with a version-pinned runner (never `@latest`):

```bash
# Recommended: fast native Rust port
uvx --from flowmark-rs==0.3.0 flowmark --auto FILE
# Python reference (library API or newest patch releases)
uvx --from flowmark==0.7.2 flowmark --auto FILE
```

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
