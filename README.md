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

```
usage: flowmark [-h] [-o OUTPUT] [-w WIDTH] [-p] [-s] [-c] [--smartquotes] [--ellipses] [-i]
                [--nobackup] [--auto] [--version]
                [file]

Flowmark: Better auto-formatting for Markdown and plaintext

positional arguments:
  file                 Input file (use '-' for stdin)

options:
  -h, --help           show this help message and exit
  -o, --output OUTPUT  Output file (use '-' for stdout)
  -w, --width WIDTH    Line width to wrap to, or 0 to disable line wrapping (default: 88)
  -p, --plaintext      Process as plaintext (no Markdown parsing)
  -s, --semantic       Enable semantic (sentence-based) line breaks (only applies to Markdown
                       mode)
  -c, --cleanups       Enable (safe) cleanups for common issues like accidentally boldfaced
                       section headers (only applies to Markdown mode)
  --smartquotes        Convert straight quotes to typographic (curly) quotes and apostrophes
                       (only applies to Markdown mode)
  --ellipses           Convert three dots (...) to ellipsis character (…) with normalized
                       spacing (only applies to Markdown mode)
  -i, --inplace        Edit the file in place (ignores --output)
  --nobackup           Do not make a backup of the original file when using --inplace
  --auto               Same as `--inplace --nobackup --semantic --cleanups --smartquotes
                       --ellipses`, as a convenience for fully auto-formatting files
  --version            Show version information and exit

Flowmark provides enhanced text wrapping capabilities with special handling for
Markdown content. It can:

- Format Markdown with proper line wrapping while preserving structure
  and normalizing Markdown formatting

- Optionally break lines at sentence boundaries for better diff readability

- Process plaintext with HTML-aware word splitting

It is both a library and a command-line tool.

Command-line usage examples:

  # Format a Markdown file to stdout
  flowmark README.md

  # Format a Markdown file in-place without backups and all auto-formatting
  # options enabled
  flowmark --auto README.md

  # Format a Markdown file and save to a new file
  flowmark README.md -o README_formatted.md

  # Edit a file in-place (with or without making a backup)
  flowmark --inplace README.md
  flowmark --inplace --nobackup README.md

  # Process plaintext instead of Markdown
  flowmark --plaintext text.txt

  # Use semantic line breaks (based on sentences, which is helpful to reduce
  # irrelevant line wrap diffs in git history)
  flowmark --semantic README.md

For more details, see: https://github.com/jlevy/flowmark
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
`--inplace --nobackup --semantic --cleanups --smartquotes`.

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
