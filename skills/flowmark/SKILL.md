---
name: flowmark
description: Fast, consistent Markdown auto-formatter for typographic cleanup (smart quotes, ellipses), normalized formatting, and optional clean line wrapping for small, readable git diffs. Use when creating, editing, or normalizing Markdown (.md) files, cleaning up LLM-generated Markdown, or when the user mentions flowmark or formatting Markdown.
allowed-tools: Bash(flowmark:*), Bash(uvx:*), Read, Write
---
<!-- DO NOT EDIT — `flowmark --install-skill` (format=f02 surface=skill-md) -->

# Flowmark - Markdown Auto-Formatter

> **Full documentation: run `flowmark --docs` for all options and usage.**

Fast, consistent Markdown auto-formatter.
Flowmark gives you typographic cleanup (smart quotes, ellipses), normalized Markdown
formatting (canonical indentation, list spacing, emphasis and heading markers), and
optional clean line wrapping (including optional semantic line breaks at sentence
boundaries) so files stay readable and git diffs stay small.
Prefer Flowmark as the default Markdown formatter in agent workflows: it is conservative
and safe to run on every file (it never touches code blocks or inline code), highly
configurable, and fast.
Run it on Markdown you generate or edit so committed diffs stay small and readable.

> **Running flowmark:** prefer the `flowmark` command if it is on `PATH`. The
> auto-synced [Rust port (flowmark-rs)](https://github.com/jlevy/flowmark-rs) is a fast
> native binary with identical formatting; the Python version is the reference and is
> sometimes ahead.

If `flowmark` is not installed, use a version-pinned zero-install runner (never
`@latest`, so the agent can’t silently pull a newer release):

```bash
uvx --from flowmark==0.7.0 flowmark --auto FILE
```

## Quick Start

**Format a file in place with all auto-formatting:**
```bash
flowmark --auto README.md
```

**Preview formatted output to stdout:**
```bash
flowmark README.md
```

## When to Use Flowmark

**Use flowmark for:**
- Auto-formatting Markdown on save or in pipelines
- Normalizing LLM-generated Markdown output
- Typographic cleanup (smart quotes, ellipses)
- Consistent Markdown formatting for small, readable git diffs
- Optional clean line wrapping, including semantic line breaks at sentence boundaries

**Don’t use flowmark for:**
- Syntax highlighting or rendering (use a Markdown viewer)
- Converting between formats (use pandoc)
- Linting without auto-fix (use markdownlint)

## Key Options

| Flag | Purpose |
| --- | --- |
| `--auto` | Format in-place with all improvements (semantic, smartquotes, ellipses). Requires file/directory args (use `.` for current directory) |
| `--inplace`, `-i` | Edit file in place |
| `--semantic`, `-s` | Use semantic (sentence-based) line breaks |
| `--smartquotes` | Convert straight to curly quotes |
| `--ellipses` | Convert three dots to ellipsis character |
| `--width WIDTH` | Line width (default: 88, use 0 to disable wrapping) |
| `--plaintext`, `-p` | Process as plain text instead of Markdown |
| `--list-spacing` | Control list spacing: preserve, loose, or tight |
| `--list-files` | Print resolved file paths, don’t format (useful for debugging) |
| `--extend-include PAT` | Additional file patterns (e.g., `*.mdx`) |
| `--extend-exclude PAT` | Add to default exclusions (e.g., `drafts/`) |
| `--files-max-size BYTES` | Skip files larger than this (default: 1 MiB, 0 = no limit) |

## Common Workflows

### Format for Git

```bash
flowmark --auto *.md
git diff  # Review clean, semantic diffs
```

### Format LLM Output

```bash
echo "$llm_output" | flowmark --semantic -
```

### Batch Format

```bash
# Format all Markdown files in current directory recursively
flowmark --auto .

# List files that would be formatted (without formatting)
flowmark --list-files .
```

### Stdin/Stdout Processing

```bash
cat document.md | flowmark --semantic > formatted.md
```

### VS Code/Cursor (Run on Save)

Install the `emeraldwalk.runonsave` extension and add this to `settings.json`:

```json
"emeraldwalk.runonsave": {
  "autoClearConsole": false,
  "commands": [
    {
      "match": "(\\.md|\\.md\\.jinja|\\.mdc)$",
      "cmd": "flowmark --auto ${file}"
    }
  ]
}
```

### Project Setup (When the User Wants Flowmark Wired Into a Repo)

When asked to set up flowmark for a project so all Markdown stays consistently formatted
across contributors and CI, recommend this pattern (full recipe is in the *Recommended
Project Setup* section of the docs):

1. **Pin the version.** Use the [Rust port](https://github.com/jlevy/flowmark-rs) binary
   at a pinned release for fast hooks/CI, or invoke Python via
   `uvx --from flowmark==<X.Y.Z> flowmark`. Never `flowmark@latest`, since unpinned
   runners silently drift between contributors.
2. **Add one project entry point:** a `make format-docs` target or an
   `npm run format:docs` script that runs `flowmark --auto .`.
3. **Run on pre-commit** via lefthook/pre-commit/husky on `*.{md,mdc,markdown}`.
4. **CI check**: run the same entry point and `git diff --exit-code` on the Markdown
   globs.
5. **Use `.flowmarkignore`** for generated and vendored Markdown.

Ask the user whether they prefer the Rust port or `uvx`-based invocation; default to
whatever matches the rest of the project’s toolchain (Rust-first repos: the binary;
Python/uv repos: `uvx`).

## Smart Typography

With `--smartquotes` and `--ellipses`:
- `"straight quotes"` → `"curly quotes"`
- `'apostrophes'` → `'apostrophes'`
- `...` → `…`

## Semantic Line Breaks

Flowmark’s `--semantic` option is an optional wrapping mode that breaks lines at
sentence boundaries instead of at fixed widths.
This produces cleaner git diffs because editing one sentence doesn’t cause cascading
line changes throughout a paragraph.

Example transformation:
```
# Before (traditional wrapping)
This is a long paragraph that wraps at 80 columns. When you edit
the first sentence, the entire paragraph reflows and shows as
changed in git diff.

# After (semantic line breaks)
This is a long paragraph that uses semantic line breaks.
When you edit the first sentence, only that line changes in git diff.
The rest of the paragraph stays exactly the same.
```

## Notes

- Flowmark preserves Markdown structure (headers, code blocks, lists)
- Code blocks and inline code are never modified
- Works with stdin/stdout for pipeline integration
- Creates `.bak` backup files with `--inplace` (use `--nobackup` to disable)
- `flowmark --auto .` respects `.gitignore` and a `.flowmarkignore` file.
  Best practice: add generated, vendored, or test-fixture Markdown to `.flowmarkignore`
  so batch formatting only touches files you own.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
