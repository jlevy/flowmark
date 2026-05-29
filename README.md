<!-- Generated from docs/shared/flowmark-readme-shared.md via
scripts/generate-python-readme.py.
-->

# flowmark

[![Follow @ojoshe on X](https://img.shields.io/badge/follow_%40ojoshe-black?logo=x&logoColor=white)](https://x.com/ojoshe)
[![CI](https://github.com/jlevy/flowmark/actions/workflows/ci.yml/badge.svg)](https://github.com/jlevy/flowmark/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/flowmark)](https://pypi.org/project/flowmark/)
[![Python versions](https://img.shields.io/pypi/pyversions/flowmark)](https://pypi.org/project/flowmark/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

## What Is Flowmark?

Flowmark is a Markdown auto-formatter, written
[in Python](https://github.com/jlevy/flowmark) with an auto-synced
[Rust port](https://github.com/jlevy/flowmark-rs), designed for **better LLM
workflows**, **clean git diffs**, and **flexible use from CLI, from IDEs, or as a
library**.

With AI tools increasingly producing Markdown, consistent and diff-friendly formatting
has become essential.
It improves collaborative editing and LLM workflows, especially when committing
documents to git repositories.

For CLI auto-formatting, the Python and Rust builds produce identical output: the Rust
port is a fast single native binary, while the Python version is the reference and is
sometimes ahead on the newest features.
Pick whichever fits your environment; for heavy or latency-sensitive formatting, choose
the Rust binary.

## Quick Start

Both Python and Rust versions are best installed with
[**uv**](https://github.com/astral-sh/uv).

### Run With `uvx`

No install needed for one-off usage:

```shell
uvx flowmark-rs --help                  # For native-binary Rust
uvx flowmark-rs --auto somefile.md
uvx flowmark --help                     # For Python
uvx flowmark --auto somefile.md
```

### Install as a Global CLI

```shell
uv tool install --upgrade flowmark-rs   # For native-binary Rust
uv tool install --upgrade flowmark      # For Python
flowmark --auto somefile.md             # One file
flowmark --auto .                       # Whole tree (respects .gitignore / .flowmarkignore)
```

Run `flowmark --help`, `flowmark --docs`, or `flowmark --skill` for more.

### Set Up with Any Coding Agent

Hand your agent this one instruction:

> Set up Flowmark to keep this project’s Markdown auto-formatted.
> Run `uvx --from flowmark==0.7.1 flowmark --skill` for details.

Or run `uvx --from flowmark==0.7.1 flowmark --install-skill` to manually install the
skill into `.agents/`, `.claude/`, and `AGENTS.md` (see
[How to Install the Skill](#how-to-install-the-skill)).

For consistency across users and supply chain security, it’s recommended to pin the
version when installing within a skill or project build.

## Why Another Markdown Auto-Formatter?

Flowmark supports both [CommonMark](https://spec.commonmark.org/0.31.2/) and
[GitHub-Flavored Markdown (GFM)](https://github.github.com/gfm/) via
[Marko](https://github.com/frostming/marko).

The key differences from
[other Markdown formatters](#how-does-flowmark-compare-to-other-markdown-auto-formatters):

- Carefully chosen default formatting rules that are effective for use in editors/IDEs,
  in agent pipelines, and also when paging through docs in a terminal.

- Extensive Markdown feature support.
  “Just works” support including **GFM-style tables**, **footnotes**, **YAML
  frontmatter**, **template tags** (Markdoc, Jinja, Nunjucks), and **inline HTML** and
  HTML comments.

- All line wrapping is Markdown-aware.
  Flowmark offers advanced and customizable line-wrapping capabilities, including
  [semantic line breaks](#semantic-line-breaks), a feature that is especially helpful in
  managing diffs and allowing collaborative edits on a Markdown document while avoiding
  git conflicts.

- Optional typographic fixes such as [automatic smart quotes](#smart-quote-support) for
  professional-looking typography.

- Full-featured globbing, including git-ignore support.

- A **fast, exact Rust port** of the Python reference implementation, compiled to a
  single native binary.
  With the Rust port’s caching feature, it can auto-format thousands of documents in
  milliseconds.

Some general philosophy:

- Be conservative about changes so that it is safe to run automatically on save or after
  any stage of a document pipeline.

- Be opinionated about sensible defaults but not dogmatic by preventing customization.
  You can adjust or disable most settings.
  And if you are using it as a library, you can fully control anything you want
  (including more complex things like custom line wrapping for HTML).

- Be as small and simple as possible, with few dependencies.

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
> For an example of what an auto-formatted Markdown doc looks with semantic line breaks
> looks like, see
> [the Markdown source](https://github.com/jlevy/flowmark/blob/main/README.md?plain=1)
> of this readme file.

Some Markdown auto-formatters never wrap lines, while others wrap at a fixed width.
Flowmark supports both, via the `--width` option.

Default line wrapping behavior is **88 columns**. The
“[90-ish columns](https://youtu.be/esZLCuWs_2Y?si=lUj055ROI--6tVU8&t=1288)” compromise
was popularized by Black and also works well for Markdown.

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
| --- | --- |
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
| `--check` | Don’t write; exit non-zero if any file would be reformatted (for CI / pre-commit) |
| `--auto` | All auto-formatting: `--inplace --nobackup --semantic --cleanups --smartquotes --ellipses`. Requires file/directory args (use `.` for current directory) |

File discovery flags:

| Flag | Description |
| --- | --- |
| `--list-files` | Print resolved file paths, don’t format |
| `--extend-include PATTERN` | Additional file patterns (e.g., `*.mdx`) |
| `--exclude PATTERN` | Replace all default exclusions |
| `--extend-exclude PATTERN` | Add to default exclusions (e.g., `drafts/`) |
| `--no-respect-gitignore` | Disable `.gitignore` integration |
| `--force-exclude` | Apply `--exclude`/default patterns to explicitly-named files too (`.flowmarkignore` always applies) |
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
   As a persistent “never touch” list, it is always honored — even for files named
   explicitly on the command line (e.g. by a pre-commit hook), with no extra flag.
   By contrast, `--exclude`/default patterns apply to explicitly-named files only with
   `--force-exclude` (otherwise naming a file explicitly formats it).

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
Flowmark uses Python’s `pathlib.Path.glob()` internally, which always supports `**` for
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
`--cleanups`, `--smartquotes`, and `--ellipses`. It ignores formatting settings from
config files.

However, `width` and file discovery settings (excludes, max size, etc.)
are always read from config regardless of `--auto`.

When not using `--auto`, all formatting settings can be configured via the config file
and overridden by explicit CLI flags.

## Library Usage

Flowmark is a flexible Python library, not just a CLI. Add it with `uv add flowmark` (or
`pip install flowmark`) and use the high-level helpers or the lower-level building
blocks.

**Format Markdown text or files** with the same engine as the CLI:

```python
from flowmark import reformat_text, reformat_file

# Normalize a Markdown string (semantic line breaks on by default; opt into typography)
clean = reformat_text(messy_markdown, smartquotes=True, ellipses=True)

# Reformat a file in place, atomically (pass output=None with inplace=True)
reformat_file("README.md", None, inplace=True, semantic=True)
```

**Use it as a smarter `textwrap`.** `wrap_paragraph` / `wrap_paragraph_lines` (with the
`Wrap` enum) generalize the stdlib `textwrap` with control over initial vs.
subsequent indentation and pluggable word splitters that never break inside Markdown
links, code spans, HTML/template tags, or URLs.

**Inspect Markdown inline structure** with the public inline API (new in v0.7.0),
exposed so downstream tools can reuse Flowmark’s own primitives instead of
re-implementing them:

```python
from flowmark import flowmark_markdown, extract_links

doc = flowmark_markdown().parse(markdown_text)
for link in extract_links(doc):   # -> list[Link(text, url, title)], reference links resolved
    print(link.text, link.url)
```

- `flowmark.markdown_ast`: `walk_elements`, `extract_links`, the `Link` type, and
  `block_span` for AST-aware inspection of a parsed document.
- `flowmark.atomic_spans`: the atomic-construct patterns Flowmark uses internally (code
  spans, links, autolinks, bare URLs, HTML/Jinja tags), the offset-preserving tokenizers
  `iter_atomic_spans` / `iter_atomic_words`, and the atomic-aware sentence splitter
  `split_sentences_with_spans` / `split_sentences_atomic`.

**Map parsed blocks back to source.** Every block element produced by
`flowmark_markdown().parse(text)` carries an authoritative `element.span = (start, end)`
half-open offset pair, recorded straight from marko’s parser state (no regex, no
heuristic) at every nesting level.
Offsets index the source after marko’s `\r\n -> \n` normalization, so slice against an
LF-normalized copy of the input:

```python
from flowmark import flowmark_markdown
from flowmark.markdown_ast import block_span

source = markdown_text.replace("\r\n", "\n")
doc = flowmark_markdown().parse(source)
for block in doc.children:
    start, end = block_span(block)
    print(type(block).__name__, source[start:end])
```

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

## Recommended Project Setup

To keep a repo’s Markdown consistently formatted across contributors and CI, **pin a
flowmark version** and wire it into your existing build/hook plumbing.
The same pattern works whether you reach for the Python build or the Rust port.

### 1. Pick a pinned invocation

Avoid unpinned `flowmark@latest`: different contributors then silently run different
versions and produce noisy diffs.

- **Rust port (fastest)**: install the
  [`flowmark-rs`](https://github.com/jlevy/flowmark-rs) binary at a specific release.
  Identical formatting to the Python version; great when speed matters in hooks/CI.
- **Python via `uvx` (zero-install)**: invoke as
  `uvx --from flowmark==<X.Y.Z> flowmark --auto`. First call caches the wheel;
  subsequent calls are fast.
- **Python tool install**: `uv tool install flowmark==<X.Y.Z>` (or
  `pip install flowmark==<X.Y.Z>` in a venv) puts `flowmark` on `PATH`.

### 2. Add one project entry point

A single command everyone (and CI) runs.
Makefile target:

```makefile
FLOWMARK := uvx --from flowmark==0.7.1 flowmark

format-docs:
	$(FLOWMARK) --auto .
```

Or as an npm script in `package.json`:

```json
{
  "scripts": {
    "format:docs": "uvx --from flowmark==0.7.1 flowmark --auto ."
  }
}
```

### 3. Run on pre-commit

[lefthook](https://lefthook.dev) example (`lefthook.yml`):

```yaml
pre-commit:
  commands:
    flowmark:
      glob: "*.{md,mdc,markdown}"
      run: uvx --from flowmark==0.7.1 flowmark --auto {staged_files}
      stage_fixed: true
```

Equivalent setups with [pre-commit](https://pre-commit.com) (via a `local` hook) or
`husky` work the same way; the key is the pinned invocation.

### 4. Add a CI check

Run the entry point in CI and fail if anything changed:

```yaml
- run: make format-docs
- run: git diff --exit-code -- '*.md' '*.mdc' '*.markdown'
```

### 5. Exclude generated and vendored Markdown

Add a `.flowmarkignore` (same syntax as `.gitignore`) so batch formatting only touches
files you own:

```
docs/api/_generated/
attic/
third_party/
```

`flowmark --auto .` always respects `.flowmarkignore` and `.gitignore`. For editor-side
on-save formatting, see [Use in VSCode/Cursor](#use-in-vscodecursor) above.

## Agent Use (Claude Code and Other AI Coding Agents)

Flowmark is built to be the **default Markdown auto-formatter for agent workflows**. Its
deterministic, diff-friendly output and semantic line breaks keep LLM-generated and
LLM-edited Markdown clean in git, and the Rust port makes it fast enough to run on every
save or every agent turn.
It works with any agent that can run a shell command, and ships a
[SKILL.md](https://agentskills.io) so capable agents discover when to use it on their
own.

### How to Install the Skill

There are three install paths, ordered by what most users want first:

**1. Cross-agent package manager (no flowmark prerequisite).** If you just want the
skill on disk for any supported agent and don’t already have flowmark, use the
`skills.sh` installer.
It copies the published discovery copy into `.agents/skills/` and symlinks it into each
agent’s native location (Claude Code, Codex, Cursor, Copilot, Gemini, …). The discovery
copy bootstraps its own pinned `uvx` invocation, so no prior flowmark install is
required:

```bash
npx skills add jlevy/flowmark
```

**2. Direct install via the flowmark CLI (recommended once you have flowmark).** Run
from the repo root.
By default this writes all three project-local surfaces: the portable
`.agents/skills/flowmark/` (read by Codex, Gemini CLI, pi, and others), the
`.claude/skills/flowmark/` mirror (Claude Code reads only that path), and a compact
marker-bounded block in `AGENTS.md`:

```bash
flowmark --install-skill                              # all three surfaces (default)
flowmark --install-skill --surfaces=portable,agents-md  # skip the Claude mirror
flowmark --install-skill --surfaces=claude            # only the Claude mirror
flowmark --install-skill --agent-base ~/.claude       # single explicit base (global)
```

The `--surfaces` flag is a comma-separated subset of `portable`, `claude`, `agents-md`,
or the `all` alias. Installs are idempotent (re-running an up-to-date install changes
nothing), version-pinned to the installed flowmark, and generated files are marked
`DO NOT EDIT`. A forward-compat guard refuses to clobber any artifact stamped with a
newer format than this build understands.

**3. Manual copy from the public discovery copy.** Every release publishes a
spec-compliant `SKILL.md` at the repo root:
[`skills/flowmark/SKILL.md`](https://github.com/jlevy/flowmark/blob/main/skills/flowmark/SKILL.md).
You can drop it into your project at `.agents/skills/flowmark/SKILL.md` (and mirror to
`.claude/skills/flowmark/SKILL.md` for Claude Code).
Useful in air-gapped or no-Node-no-Python environments.

Flowmark is also indexed automatically by GitHub-scraping skill discoverers (SkillsMP,
ClaudeSkills.info, LobeHub, claudemarketplaces) just by being a public repo with a
`SKILL.md`, with no extra setup.

### Agent Skill Options

| Flag | Description |
| --- | --- |
| `--skill` | Print the composed skill (SKILL.md content) |
| `--install-skill` | Install the flowmark skill (project-local cross-agent by default) |
| `--surfaces LIST` | Subset of `portable`, `claude`, `agents-md`, or `all` (default) |
| `--agent-base DIR` | Install to a single explicit base dir (e.g. `~/.claude`); incompatible with `--surfaces` |
| `--docs` | Print full documentation |

### Manual Usage in Agents

Any agent with a shell can call Flowmark directly, no skill required:

```bash
# Format with all auto-formatting options
flowmark --auto README.md

# Preview formatted output
flowmark README.md

# Format LLM output (use '-' for stdin)
echo "$llm_output" | flowmark --semantic -
```

In ephemeral or cloud agent environments where nothing is installed, run it via a
**version-pinned** zero-install runner (pin the version so the agent can’t silently pull
a newer release):

```bash
uvx --from flowmark==<version> flowmark --auto README.md   # Python
# or use the Rust binary (flowmark-rs) for maximum speed
```

## How Does Flowmark Compare to Other Markdown Auto-Formatters?

There are several other Markdown auto-formatters.
All of these are worth looking at, but none offer the more advanced line-breaking
features of Flowmark or have the “just works” CLI defaults and library usage I found
most useful.

- [dprint-plugin-markdown](https://github.com/dprint/dprint-plugin-markdown) is a
  Markdown plugin for dprint, the fast Rust/WASM engine.
  It is a good, modern option but does not auto-apply semantic line breaks.

- [markdownfmt](https://github.com/shurcooL/markdownfmt) is one of the oldest and most
  popular Markdown formatters and works well for basic formatting.

- [mdformat](https://github.com/executablebooks/mdformat) is probably the closest
  alternative to Flowmark and it also uses Python.
  It preserves line breaks in order to support semantic line breaks, but does not
  auto-apply them as Flowmark does and has somewhat different features.

- [Prettier](https://prettier.io/blog/2017/11/07/1.8.0) is the ubiquitous Node formatter
  that handles Markdown/MDX.

- Rule-based linters like
  [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) catch violations
  or sometimes fix, but tend to be far too clumsy in my experience.

- Finally, the [remark ecosystem](https://github.com/remarkjs/remark) is by far the most
  powerful library ecosystem for building your own Markdown tooling in
  JavaScript/TypeScript.
  You can build auto-formatters with it but there isn’t one that’s broadly used as a CLI
  tool.

On speed, Flowmark’s auto-synced
[Rust port (flowmark-rs)](https://github.com/jlevy/flowmark-rs) compiles to a single
native binary and is among the fastest Markdown formatters available, in the same
performance class as Rust-based tools like dprint, while keeping the same formatting
behavior as the Python reference implementation.
So you get Flowmark’s formatting either way: the Python library/CLI for flexibility and
embedding, or the Rust binary when you want maximum CLI speed (large repos, hot paths,
latency-sensitive agent loops).

## Project Docs

For development workflows, see [development.md](docs/development.md).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
