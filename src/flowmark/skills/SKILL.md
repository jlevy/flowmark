---
name: flowmark
description: Auto-format Markdown with semantic line breaks, smart quotes, and diff-friendly output. Use for formatting Markdown files, normalizing LLM outputs, or when user mentions flowmark, markdown formatting, or semantic line breaks.
allowed-tools: Bash(flowmark:*), Bash(uvx flowmark@latest:*), Read, Write
---
# Flowmark - Markdown Auto-Formatter

> **Full documentation: Run `uvx flowmark@latest --docs` for all options and usage.**

Auto-format Markdown with semantic line breaks for clean git diffs and consistent output.

## Quick Start

**Format a file in place with all auto-formatting:**
```bash
uvx flowmark@latest --auto README.md
```

**Preview formatted output to stdout:**
```bash
uvx flowmark@latest README.md
```

## When to Use Flowmark

**Use flowmark for:**
- Auto-formatting Markdown on save or in pipelines
- Normalizing LLM-generated Markdown output
- Preparing documents for git with semantic line breaks
- Converting straight quotes to typographic quotes
- Consistent Markdown styling across a project

**Don't use flowmark for:**
- Syntax highlighting or rendering (use a Markdown viewer)
- Converting between formats (use pandoc)
- Linting without auto-fix (use markdownlint)

## Key Options

| Flag | Purpose |
|------|---------|
| `--auto` | Format in-place with all improvements (semantic, smartquotes, ellipses). Requires file/directory args (use `.` for current directory) |
| `--inplace`, `-i` | Edit file in place |
| `--semantic`, `-s` | Use semantic (sentence-based) line breaks |
| `--smartquotes` | Convert straight to curly quotes |
| `--ellipses` | Convert three dots to ellipsis character |
| `--width WIDTH` | Line width (default: 88, use 0 to disable wrapping) |
| `--plaintext`, `-p` | Process as plain text instead of Markdown |
| `--list-spacing` | Control list spacing: preserve, loose, or tight |
| `--list-files` | Print resolved file paths, don't format (useful for debugging) |
| `--extend-include PAT` | Additional file patterns (e.g., `*.mdx`) |
| `--extend-exclude PAT` | Add to default exclusions (e.g., `drafts/`) |
| `--files-max-size BYTES` | Skip files larger than this (default: 1 MiB, 0 = no limit) |

## Common Workflows

### Format for Git

```bash
uvx flowmark@latest --auto *.md
git diff  # Review clean, semantic diffs
```

### Format LLM Output

```bash
echo "$llm_output" | uvx flowmark@latest --semantic -
```

### Batch Format

```bash
# Format all Markdown files in current directory recursively
uvx flowmark@latest --auto .

# List files that would be formatted (without formatting)
uvx flowmark@latest --list-files .
```

### Stdin/Stdout Processing

```bash
cat document.md | uvx flowmark@latest --semantic > formatted.md
```

## Semantic Line Breaks

Flowmark's `--semantic` option breaks lines at sentence boundaries instead of at fixed
widths. This produces cleaner git diffs because editing one sentence doesn't cause
cascading line changes throughout a paragraph.

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

## Smart Typography

With `--smartquotes` and `--ellipses`:
- `"straight quotes"` → `"curly quotes"`
- `'apostrophes'` → `'apostrophes'`
- `...` → `…`

## Notes

- Flowmark preserves Markdown structure (headers, code blocks, lists)
- Code blocks and inline code are never modified
- Works with stdin/stdout for pipeline integration
- Creates `.bak` backup files with `--inplace` (use `--nobackup` to disable)
