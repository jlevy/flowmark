# flowmark

Flowmark is a pure Python Markdown auto-formatter designed for **better LLM workflows**,
**clean git diffs**, and **flexible use from CLI, from IDEs, or as a library**.

With AI tools increasingly using Markdown, having consistent, diff-friendly formatting
has become essential for modern writing, editing, and document processing workflows.
Normalizing Markdown formatting greatly improves collaborative editing and LLM
workflows, especially when committing documents to git repositories.

You can use Flowmark as a CLI, as an autoformatter in your IDE, or as a Python library.

It supports both [CommonMark](https://spec.commonmark.org/0.31.2/) and
[GitHub-Flavored Markdown (GFM)](https://github.github.com/gfm/) via
[Marko](https://github.com/frostming/marko).

The key differences from [other Markdown formatters](#why-another-markdown-formatter):

- Carefully chosen default formatting rules that are effective for use in editors/IDEs,
  in LLM pipelines, and also when paging through docs in a terminal.
  It parses and normalizes standard links and special characters, headings, tables,
  footnotes, and horizontal rules and performing Markdown-aware line wrapping.

- “Just works” support for GFM-style tables, footnotes, YAML frontmatter, template tags
  (Markdoc, Jinja, Nunjucks), and inline HTML comments.

- Advanced and customizable line-wrapping capabilities, including
  [semantic line breaks](#semantic-line-breaks), a feature that is especially helpful in
  allowing collaborative edits on a Markdown document while avoiding git conflicts.

- Optional [automatic smart quotes](#smart-quote-support) for professional-looking
  typography.

General philosophy:

- Be conservative about changes so that it is safe to run automatically on save or after
  any stage of a document pipeline.

- Be opinionated about sensible defaults but not dogmatic by preventing customization.
  You can adjust or disable most settings.
  And if you are using it as a library, you can fully control anything you want
  (including more complex things like custom line wrapping for HTML).

- Be as small and simple as possible, with few dependencies:
  [`marko`](https://github.com/frostming/marko),
  [`pathspec`](https://pypi.org/project/pathspec/),
  [`regex`](https://pypi.org/project/regex/), and
  [`strif`](https://github.com/jlevy/strif).

## Installation

The simplest way to use the tool is to use [uv](https://github.com/astral-sh/uv).

Run with `uvx flowmark --help` or install it as a tool:

```shell
uv tool install --upgrade flowmark
```

Then

```
flowmark --help
```

For use in Python projects, add the [`flowmark`](https://pypi.org/project/flowmark/)
package via uv, poetry, or pip.

## Use Cases

The main ways to use Flowmark are:

- To **autoformat Markdown on save in VSCode/Cursor** or any other editor that supports
  running a command on save.
  See [below](#use-in-vscodecursor) for recommended VSCode/Cursor setup.

- As a **command line formatter** to format text or Markdown files using the `flowmark`
  command.

- As a **library to autoformat Markdown** from document pipelines.
  For example, it is great to normalize the outputs from LLMs to be consistent, or to
  run on the inputs and outputs of LLM transformations that edit text, so that the
  resulting diffs are clean.

- As a more powerful **drop-in replacement library for Python’s default
  [`textwrap`](https://docs.python.org/3/library/textwrap.html)** but with more options.
  It simplifies and generalizes that library, offering better control over **initial and
  subsequent indentation** and **when to split words and lines**, e.g. using a word
  splitter that won’t break lines within HTML tags, template tags (`{% %}`, `{# #}`,
  `{{ }}`), Markdown links (including links with multi-word text), inline code spans
  (`` `code with spaces` ``), or HTML comments.
  See
  [`wrap_paragraph_lines`](https://github.com/jlevy/flowmark/blob/main/src/flowmark/linewrapping/text_wrapping.py).

## Semantic Line Breaks

> [!TIP]
> 
> For an example of what an auto-formatted Markdown doc looks with semantic line breaks
> looks like, see
> [the Markdown source](https://github.com/jlevy/flowmark/blob/main/README.md?plain=1)
> of this readme file.

Some Markdown auto-formatters never wrap lines, while others wrap at a fixed width.
Flowmark supports both, via the `--width` option.

Default line wrapping behavior is **88 columns**. The “[90-ish
columns](https://youtu.be/esZLCuWs_2Y?si=lUj055ROI--6tVU8&t=1288)” compromise was
popularized by Black and also works well for Markdown.

However, in addition, unlike traditional formatters, Flowmark also offers the option to
use a heuristic that prefers line breaks at sentence boundaries.
This is a small change that can dramatically improve diff readability when collaborating
or working with AI tools.

This idea of **semantic line breaks**, which is breaking lines in ways that make sense
logically when possible (much like with code) is an old one.
But it usually requires people to agree on how to break lines, which is both difficult
and sometimes controversial.

However, now we are using versioned Markdown more than ever, it’s a good time to revisit
this idea, as it can **make diffs in git much more readable**. The change may seem
subtle but avoids having paragraphs reflow for very small edits, which does a lot to
**minimize merge conflicts**.

This is my own refinement of
[traditional semantic line breaks](https://github.com/sembr/specification).
Instead of just allowing you to break lines as you wish, it auto-applies fixed
conventions about likely sentence boundaries in a conservative and reasonable way.
It uses simple and fast **regex-based sentence splitting**. While not perfect, this
works well for these purposes (and is much faster and simpler than a proper sentence
parser like SpaCy). It should work fine for English and many other Latin/Cyrillic
languages, but hasn’t been tested on CJK. You can see some
[old discussion](https://github.com/shurcooL/markdownfmt/issues/17) of this idea with
the markdownfmt author.

While this approach to line wrapping may not be familiar, I suggest you just try
`flowmark --auto` on a document and you will begin to see the benefits as you
edit/commit documents.

This feature is enabled with the `--semantic` flag or the `--auto` convenience flag.

## Typographic Cleanups

### Smart Quote Support

Flowmark offers optional **automatic smart quotes** to convert \"non-oriented quotes\"
to “oriented quotes” and apostrophes intelligently.

This is a robust way to ensure Markdown text can be converted directly to HTML with
professional-looking typography.

Smart quotes are applied conservatively and won’t affect code blocks, so they don’t
break code snippets.
It only applies them within single paragraphs of text, and only applies to \' and \"
quote marks around regular text.

This feature is enabled with the `--smartquotes` flag or the `--auto` convenience flag.

### Ellipsis Support

There is a similar feature for converting `...` to an ellipsis character `…` when it
appears to be appropriate (i.e., not in code blocks and when adjacent to words or
punctuation).

This feature is enabled with the `--ellipses` flag or the `--auto` convenience flag.

## Frontmatter Support

Because **YAML frontmatter** is common on Markdown files, any YAML frontmatter (content
between `---` delimiters at the front of a file) is always preserved exactly.
YAML is not normalized.

> [!TIP]
> 
> See the [frontmatter format](https://github.com/jlevy/frontmatter-format) repo for
> more discussion of YAML frontmatter and its benefits.

## Usage

Flowmark can be used as a library or as a CLI.

### Quick Start

```bash
# Format all Markdown files in current directory recursively
flowmark --auto .

# Format a single file in-place with all auto-formatting options
flowmark --auto README.md

# List files that would be formatted (without formatting)
flowmark --list-files .

# Format to stdout
flowmark README.md

# Format from stdin (use '-' explicitly)
echo "Some text" | flowmark -
```

### Batch Formatting

The simplest way to format all Markdown in a project:

```bash
flowmark --auto .
```

This recursively discovers all `.md` files, skips common non-content directories
(`node_modules`, `.venv`, `build`, etc.), respects `.gitignore`, and formats everything
in-place with semantic line breaks, smart quotes, ellipses, and cleanups.

For a legacy alternative (pre-v1.0 behavior):

```bash
find . -name "*.md" -exec flowmark --auto {} \;
```

### CLI Reference

The main flags:

| Flag | Description |
|------|-------------|
| `-o, --output FILE` | Output file (use `-` for stdout) |
| `-w, --width WIDTH` | Line width (default: 88, 0 = disable wrapping) |
| `-p, --plaintext` | Process as plaintext (no Markdown parsing) |
| `-s, --semantic` | Semantic (sentence-based) line breaks |
| `-c, --cleanups` | Safe cleanups (unbold headings, etc.) |
| `--smartquotes` | Convert straight quotes to typographic quotes |
| `--ellipses` | Convert `...` to `…` |
| `--list-spacing` | Control list spacing: `preserve`, `loose`, `tight` |
| `-i, --inplace` | Edit in place |
| `--nobackup` | Skip `.orig` backup with `--inplace` |
| `--auto` | All auto-formatting: `--inplace --nobackup --semantic --cleanups --smartquotes --ellipses`. Requires file/directory args (use `.` for current directory) |

File discovery flags:

| Flag | Description |
|------|-------------|
| `--list-files` | Print resolved file paths, don't format |
| `--extend-include PATTERN` | Additional file patterns (e.g., `*.mdx`) |
| `--exclude PATTERN` | Replace all default exclusions |
| `--extend-exclude PATTERN` | Add to default exclusions (e.g., `drafts/`) |
| `--no-respect-gitignore` | Disable `.gitignore` integration |
| `--force-exclude` | Apply exclusions to explicitly-named files |
| `--files-max-size BYTES` | Skip files larger than this (default: 1 MiB) |

## File Discovery

When you pass a directory to Flowmark (e.g., `flowmark --auto .`), it recursively
discovers files using a smart filter pipeline:

1. **Default includes**: Only `*.md` files by default.
   Use `--extend-include "*.mdx"` to add patterns.

2. **Default exclusions**: ~45 directories are automatically skipped, including `.git`,
   `node_modules`, `.venv`, `venv`, `__pycache__`, `build`, `dist`, `.tox`, `.nox`,
   `.idea`, `.vscode`, `vendor`, `third_party`, and more.
   These directories are pruned during traversal for performance.

3. **`.gitignore` integration**: Enabled by default.
   Reads `.gitignore` at every directory level during traversal.
   Disable with `--no-respect-gitignore`.

4. **`.flowmarkignore`**: A tool-specific ignore file using gitignore syntax.
   Place it in your project root to exclude paths specific to Flowmark formatting.

5. **Max file size**: Files over 1 MiB are skipped by default.
   Change with `--files-max-size` (0 = no limit).

### Customizing Includes and Excludes

```bash
# Also format .mdx files
flowmark --auto --extend-include "*.mdx" .

# Skip a specific directory
flowmark --auto --extend-exclude "drafts/" .

# Replace ALL default exclusions with your own
flowmark --auto --exclude "my_custom_dir/" .

# Debug: see exactly which files would be formatted
flowmark --list-files .
```

### Glob Patterns

When passing glob patterns as arguments, **always quote them** so Flowmark can handle
expansion internally:

```bash
# Correct: Flowmark expands the glob (** works for recursive matching)
flowmark --auto 'docs/**/*.md'

# Risky: shell may expand ** incorrectly if globstar is off (the default in bash)
flowmark --auto docs/**/*.md
```

Without quoting, the shell may expand `**` as a single `*` (matching only one directory
level) or pass nothing if there are no matches.
Flowmark uses Python's `pathlib.Path.glob()` internally, which always supports `**` for
recursive matching regardless of shell settings.

Note: The `--extend-include` and `--extend-exclude` flags use gitignore-style patterns
(e.g., `*.mdx`, `drafts/`), not shell globs.

### Symlinks

During recursive directory traversal, **symlinks are not followed**. This prevents
infinite loops from circular symlinks and avoids accidentally formatting files outside
the project tree.

However, if you pass a symlink **explicitly** as an argument (e.g.,
`flowmark --auto link-to-readme.md`), the symlink is resolved and the target file is
processed.

## Configuration

Flowmark supports TOML-based configuration files.
It searches for config files in this order (first match wins, walking up directories):

1. `.flowmark.toml`
2. `flowmark.toml`
3. `pyproject.toml` (only if it has a `[tool.flowmark]` section)

### Example Config

```toml
# flowmark.toml (or .flowmark.toml)

[formatting]
width = 100
semantic = true
smartquotes = true
ellipses = true
list-spacing = "preserve"

[file-discovery]
extend-include = ["*.mdx", "*.markdown"]
extend-exclude = ["drafts/", "archive/"]
files-max-size = 2097152  # 2 MiB
```

Or in `pyproject.toml`:

```toml
[tool.flowmark]
width = 100
semantic = true
extend-exclude = ["drafts/"]
```

### Config vs `--auto`

The `--auto` flag is a fixed formatting preset that always enables `--semantic`,
`--cleanups`, `--smartquotes`, and `--ellipses`.
It ignores formatting settings from config files.

However, `width` and file discovery settings (excludes, max size, etc.) are always
read from config regardless of `--auto`.

When not using `--auto`, all formatting settings can be configured via the config file
and overridden by explicit CLI flags.

## Use in VSCode/Cursor

You can use Flowmark to auto-format Markdown on save in VSCode or Cursor.
Install the “Run on Save” (`emeraldwalk.runonsave`) extension.
Then add to your `settings.json`:

```json
  "emeraldwalk.runonsave": {
    "commands": [
        {
            "match": "(\\.md|\\.md\\.jinja|\\.mdc)$",
            "cmd": "flowmark --auto ${file}"
        }
    ]
  }
```

The `--auto` option is just the same as
`--inplace --nobackup --semantic --cleanups --smartquotes --ellipses`.

For batch formatting an entire project, use `flowmark --auto .` from the terminal.

## Agent Use (Claude Code and Other AI Coding Agents)

Flowmark can be installed as a skill for Claude Code and other AI coding agents,
enabling automatic Markdown formatting in agent workflows.

### Install the Skill

```bash
# Install globally (available to all projects)
uvx flowmark@latest --install-skill

# Or install to current project only
uvx flowmark@latest --install-skill --agent-base ./.claude
```

After installation, Claude Code will automatically recognize when to use Flowmark for
Markdown formatting tasks.

### Agent Skill Options

| Flag | Description |
|------|-------------|
| `--skill` | Print skill instructions (SKILL.md content) |
| `--install-skill` | Install Claude Code skill for flowmark |
| `--agent-base DIR` | Agent config directory (default: ~/.claude) |
| `--docs` | Print full documentation |

### Manual Usage in Agents

If you prefer to use Flowmark manually within agent sessions:

```bash
# Format with all auto-formatting options
uvx flowmark@latest --auto README.md

# Preview formatted output
uvx flowmark@latest README.md

# Format LLM output (use '-' for stdin)
echo "$llm_output" | uvx flowmark@latest --semantic -
```

## Why Another Markdown Formatter?

There are several other Markdown auto-formatters:

- [markdownfmt](https://github.com/shurcooL/markdownfmt) is one of the oldest and most
  popular Markdown formatters and works well for basic formatting.

- [mdformat](https://github.com/executablebooks/mdformat) is probably the closest
  alternative to Flowmark and it also uses Python.
  It preserves line breaks in order to support semantic line breaks, but does not
  auto-apply them as Flowmark does and has somewhat different features.

- [Prettier](https://prettier.io/blog/2017/11/07/1.8.0) is the ubiquitous Node formatter
  that handles Markdown/MDX

- [dprint-plugin-markdown](https://github.com/dprint/dprint-plugin-markdown) is a
  Markdown plugin for dprint, the fast Rust/WASM engine

- Rule-based linters like
  [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) catch violations
  or sometimes fix, but tend to be far too clumsy in my experience.

- Finally, the [remark ecosystem](https://github.com/remarkjs/remark) is by far the most
  powerful library ecosystem for building your own Markdown tooling in
  JavaScript/TypeScript.
  You can build auto-formatters with it but there isn’t one that’s broadly used as a CLI
  tool.

All of these are worth looking at, but none offer the more advanced line breaking
features of Flowmark or seemed to have the “just works” CLI defaults and library usage I
found most useful.

## Project Docs

For how to install uv and Python, see [installation.md](docs/installation.md).

For development workflows, see [development.md](docs/development.md).

For instructions on publishing to PyPI, see [publishing.md](docs/publishing.md).

* * *

*This project was built from
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).*
