# Flowmark Markdown Support

This is the definitive specification of the Markdown syntax Flowmark supports: what it
parses, how it normalizes each construct, and which extended syntaxes it guarantees to
preserve untouched. It applies equally to the
[Python reference implementation](https://github.com/jlevy/flowmark) and the
[Rust port](https://github.com/jlevy/flowmark-rs), which produce identical output.

This document is a behavioral contract, verified end to end by the test suite (see
[Verification](#verification)). Any change to formatting behavior must update this
document and its tests together.

## How to read this document

Every construct has a **treatment**, one of:

- **Normalized** — parsed and re-emitted in Flowmark’s canonical form.
  The source may be rewritten, but the rewrite is render-identical in CommonMark and
  every dialect surveyed.
  Paragraph text is also re-wrapped (this is Flowmark’s core function: line breaks
  *within* paragraphs are never significant and are always re-chosen).
- **Preserved** — round-trips byte-identical.
  Flowmark may parse it, but re-emits the author’s exact bytes, markers, and line
  structure.
- **Protected block** — a region Flowmark does not model.
  The entire region, fences included, passes through verbatim and is exempt from
  wrapping and normalization.
- **Atomic** — an inline span that is never split across lines during wrapping, though
  the text around it re-wraps normally.
- **Opt-in transform** — a deliberate text change enabled by a flag (`--smartquotes`,
  `--ellipses`, `--cleanups`), never on by default in plain formatting.

Status markers: constructs marked **(planned)** are specified in the
[rare Markdown syntax preservation plan](project/specs/active/plan-2026-07-30-rare-markdown-preservation.md)
(issues [#62](https://github.com/jlevy/flowmark/issues/62),
[#67](https://github.com/jlevy/flowmark/issues/67)) and currently deviate from this
specification; the marker is removed as each lands.
Unmarked rows are current behavior, covered by tests today.

The standing rule behind all of this:

> **Flowmark must never break syntax it does not understand.** A construct Flowmark
> cannot model is passed through verbatim.
> A marker or delimiter choice is only normalized when the normalization is
> render-identical in every supported dialect.
> Formatting is idempotent, and a formatted document is `--check`-clean.

## CommonMark core

Flowmark parses [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/) via a
customized parser.

### Block constructs

| Construct | Example | Treatment |
| --- | --- | --- |
| ATX headings | `## Title` | Normalized: one space after `#`s; closing `#`s removed (`## T ##` → `## T`); one blank line after |
| Setext headings | `Title`⏎`=====` | Normalized to ATX (`# Title`) |
| Paragraphs | prose | Normalized: re-wrapped to width (default 88) or by sentence with `--semantic` |
| Blockquotes | `> text` | Normalized: `> ` prefix per level, content re-wrapped; nesting preserved; no trailing whitespace on empty quote lines (planned) |
| Bullet lists | `- item` | Normalized: author’s bullet char (`-`, `*`, `+`) preserved; 2-space continuation indent |
| Ordered lists | `3. item` | Normalized: start number preserved, numbering sequential; `1)` form converted to `1.` |
| List spacing | tight/loose | Preserved as authored by default; `--list-spacing loose\|tight` converts |
| Fenced code blocks | `` ```lang `` | Preserved: content verbatim; fence char (`` ` ``/`~`) and length preserved, lengthened only if content requires it |
| Indented code blocks | 4-space indent | Normalized to fenced code blocks |
| Thematic breaks | `---`, `***`, `___` | Normalized to `* * *` today; source style preserved (planned) |
| HTML blocks | `<div>`⏎`…`⏎`</div>` | Currently collapsed onto one line; protected block with verbatim line structure (planned) |
| Link reference definitions | `[label]: url "title"` | Normalized: one per line, title quotes normalized to `"` |
| Blank lines |  | Normalized: single blank line between blocks; exactly one trailing newline at EOF (planned; today a trailing heading gains an extra blank line) |

### Inline constructs

| Construct | Example | Treatment |
| --- | --- | --- |
| Emphasis / strong | `*em*`, `_em_`, `**strong**` | Parsed with CommonMark flanking rules. Today re-emitted as `*`/`**`; author’s delimiter preserved (planned) |
| Code spans | `` `code` `` | Preserved verbatim, atomic; backtick padding added only when content starts/ends with a backtick |
| Inline links | `[text](url "title")` | Normalized: title quotes normalized; atomic at wrap |
| Reference links | `[text][label]` | Normalized: kept as references; shortcut form `[label]` converted to collapsed `[label][]` (a shortcut merges with adjacent `(…)`/`[…]` text; see issue #45) |
| Images | `![alt](src "title")` | Normalized like links |
| URI autolinks | `<https://x>` | Preserved |
| Email autolinks | `<user@x.com>` | Normalized to `<mailto:user@x.com>` |
| Hard line breaks | trailing `␠␠` or `\` | Normalized to trailing `\` (the two-space form is invisible in editors) |
| Soft line breaks | newline in paragraph | Not significant; re-chosen by the wrapper (by width, or by sentence with `--semantic`) |
| Backslash escapes | `\*`, `1\.` | Preserved, minimized where provably unnecessary (e.g. escaped periods that cannot start a list) |
| HTML entities | `&amp;`, `&copy;` | Preserved |
| Inline (raw) HTML | `<sup>1</sup>` | Preserved; tags atomic at wrap |

## GFM extensions

Flowmark enables [GitHub Flavored Markdown](https://github.github.com/gfm/) extensions,
with fixes where the stock behavior is wrong.

| Construct | Example | Treatment |
| --- | --- | --- |
| Tables | `\| a \| b \|` | Normalized: delimiter row always `---`/`:---`/`:---:`/`---:` (three dashes; alignment preserved, dash count is not significant); no column padding; leading/trailing pipes added; `\|` escaped in cells |
| Task lists | `- [x] done` | Normalized: `[X]` → `[x]`; marker spacing normalized |
| Strikethrough | `~~gone~~`, `~gone~` | Parsed with corrected GFM flanking rules (stock parsers match `~60 seconds, ~130 words` incorrectly). Today re-emitted as `~~`; author’s delimiter count preserved (planned) — note single `~` is GFM strikethrough but Pandoc subscript, so the count is semantic |
| Bare URL autolinks | `https://x.com` | Preserved; atomic at wrap; trailing sentence punctuation not swallowed |
| Footnotes | `[^1]` and `[^1]: note` | Preserved: references verbatim; definitions with 4-space continuation indent |
| Alerts | `> [!NOTE]`⏎`> text` | Recognized (NOTE, TIP, IMPORTANT, WARNING, CAUTION). Today the label is uppercased; author’s case preserved (planned) |

## Frontmatter

| Format | Delimiters | Treatment |
| --- | --- | --- |
| YAML | `---` … `---` | Preserved verbatim, never formatted; the blank line (or none) after the closing fence preserved (planned; today it is removed) |
| YAML, Pandoc close | `---` … `...` | Recognized and preserved (planned; today unrecognized) |
| TOML (Hugo) | `+++` … `+++` | Preserved verbatim (planned; today reflowed as prose) |

## Template and tag constructs

Flowmark is safe on templated Markdown.
These are supported today and covered by tests:

| Construct | Example | Treatment |
| --- | --- | --- |
| Jinja / Liquid / Jekyll tags | `{% if x %}…{% endif %}` | Atomic; paired open/close tags kept together; block-level tags kept on their own lines |
| Jinja variables / Hugo shortcodes | `{{ var }}`, `{{< shortcode >}}` | Atomic |
| Jinja comments | `{# note #}` | Atomic |
| Markdoc tags | `{% tag %}` | Atomic (same mechanism as Jinja tags) |
| HTML comments | `<!-- note -->`, multi-line | Preserved; atomic; standalone multi-line comments keep their line structure |

## Typography transforms (opt-in)

Off by default in plain formatting; all enabled by `--auto`:

| Flag | Effect |
| --- | --- |
| `--smartquotes` | Straight quotes/apostrophes to typographic (`"x"` → `"x"`); never inside code spans, code blocks, URLs, or math |
| `--ellipses` | `...` to `…` with normalized spacing, same protections |
| `--cleanups` | Safe cleanups for common LLM output defects (e.g. a fully-bolded line that should be a heading) |
| `--semantic` | Line breaks at sentence boundaries within the wrap width, for clean diffs |

## Extended dialect constructs (preserved, not parsed)

Flowmark does not interpret these syntaxes — there is no single standard for several of
them — but guarantees not to break them.
Each row round-trips byte-identical.
All rows in this section are **(planned)** unless marked **current**; the
[plan spec](project/specs/active/plan-2026-07-30-rare-markdown-preservation.md) carries
the full research, citations, and per-construct rules.

### GitLab Flavored Markdown (GLFM)

| Construct | Example | Treatment |
| --- | --- | --- |
| Table of contents | `[[_TOC_]]`, `[TOC]` | Preserved (`[TOC]` current) |
| Wiki links | `[[Page]]`, `[[Text\|slug]]` | Preserved; interior fully opaque (GitLab’s pipe order is display-first, Obsidian’s is target-first, so neither side is safe to touch); atomic at wrap |
| Description lists | `Term`⏎`: description` | Preserved: line structure kept, tight and loose, single and multiple descriptions |
| Multiline blockquotes | `>>>`⏎…⏎`>>>` | Protected block, fences included |
| Block math | `$$`⏎…⏎`$$` | Protected block |
| Inline math | `$x$`, `$`x`$` | Preserved (current); atomic at wrap |
| Math code fences | `` ```math `` | Preserved (current — ordinary code fence) |
| Inline diffs | `{+add+}`, `[-del-]` | Preserved (current) |
| Placeholders / includes | `%{gitlab_server}`, `::include{file=x}` | Preserved (current) |
| References | `#123`, `!456`, `~label`, `%5`, `@user`, `[issue:123]`, `[epic:9]`, commit SHAs… | Preserved (current), including underscore interiors like `[issue:_123_]` (planned via emphasis-delimiter preservation) |
| Emoji shortcodes | `:smile:` | Preserved (current) |

### Pandoc

| Construct | Example | Treatment |
| --- | --- | --- |
| Definition lists | `Term`⏎`:   definition` | Preserved: `:`/`~` marker lines and their spacing kept verbatim |
| Simple / multiline tables | dash-row delimited | Protected block, captions (`Table:`/`:`) included |
| Grid tables | `+---+` / `+===+` | Protected block (current behavior survives by accident; becomes first-class) |
| Fenced divs | `::: note` … `:::` | Protected block, fences and interior verbatim (also covers markdown-it-container, remark-directive, and MyST colon fences) |
| Bracketed spans | `[text]{.mark}` | Preserved; atomic at wrap |
| Line blocks | `\| verse line` | Preserved verbatim, never wrapped |
| Superscript / subscript | `x^2^`, `H~2~O` | Preserved (superscript current; subscript planned via delimiter-count preservation) |
| Display / inline TeX math | `\[`…`\]`, `\(x\)` | Protected block / atomic (MathJax’s default delimiters) |
| YAML metadata `...` close | `---` … `...` | Recognized as frontmatter |

### Obsidian

| Construct | Example | Treatment |
| --- | --- | --- |
| Callouts | `> [!tip]+ My Title` | Preserved: type case, fold marker (`+`/`-`), and custom title verbatim; title line never joined with the body |
| Wikilinks / embeds | `[[Note#^id\|alias]]`, `![[img.png\|100]]` | Preserved; atomic at wrap |
| Comments | `%%inline%%`, `%%` block `%%` | Preserved (inline current via brace-tag atomicity; block planned) |
| Block anchors | `paragraph text ^block-id` | Preserved; anchor never separated from its line end |

### MkDocs / Python-Markdown

| Construct | Example | Treatment |
| --- | --- | --- |
| Admonitions | `!!! note "Title"` + 4-space body | Protected block: opener and indented body verbatim (never re-parsed as code) |
| Collapsible admonitions | `??? tip`, `???+ note` | Protected block |
| Content tabs | `=== "Tab"` + 4-space body | Protected block (a bare `===` line is still a setext underline; openers always carry text) |

### kramdown, PHP Markdown Extra, MyST, CriticMarkup

| Construct | Example | Treatment |
| --- | --- | --- |
| kramdown block IALs | `{: .class #id}` after a block | Preserved on its own line; adjacency kept (no blank line inserted after headings) |
| markdown-it-attrs / MyST attribute lines | `{.class #id}` before/after a block | Preserved on its own line (current for standalone lines; adjacency planned) |
| Heading attributes | `# Title {#custom-id}` | Preserved (current) |
| Abbreviations | `*[HTML]: HyperText Markup Language` | Preserved: one definition per line, never joined |
| MyST roles | `` {sub}`x` `` | Preserved (current); atomic at wrap |
| MyST backtick directives | `` ```{note} `` | Preserved (current — ordinary code fence) |
| CriticMarkup | `{++ins++}`, `{--del--}`, `{~~a~>b~~}`, `{==mark==}`, `{>>note<<}` | Preserved; atomic at wrap |

## Normalization reference

The complete list of Flowmark’s intentional, render-identical rewrites (house style).
Each is locked by a regression test asserting the normalized output:

1. Line breaks within paragraphs re-chosen (width or sentence-based).
2. Setext headings to ATX; closing `#`s removed from ATX headings.
3. Indented code blocks to fenced.
4. Ordered list `1)` markers to `1.`; numbering made sequential from the preserved start
   number.
5. Task list `[X]` to `[x]`.
6. Table delimiter rows to three-dash form with alignment colons; cell padding removed;
   outer pipes added.
7. Email autolinks gain `mailto:`.
8. Shortcut reference links to collapsed form (`[label]` → `[label][]`).
9. Hard breaks to trailing backslash.
10. Link/image title quotes to `"…"`.
11. Unnecessary backslash escapes removed (conservatively).
12. Blank lines collapsed to one between blocks; heading spacing normalized.

If any of these ever becomes semantically significant in a real dialect, it moves to the
preservation set — that is the standing rule.

## Verification

This contract is enforced end to end, in platform-neutral form shared by both
implementations:

- **Tryscript golden tests** (`tests/tryscript/*.tryscript.md`) run the `flowmark` CLI
  against fixture documents and assert exact output; the Rust port runs the same files.
- **Golden testdocs** (`tests/testdocs/`) round-trip full documents in every mode;
  expected outputs are generated from the Python implementation (the reference) and
  consumed by the Rust port’s parity harness.
- The **rare-syntaxes corpus** (per the
  [plan spec](project/specs/active/plan-2026-07-30-rare-markdown-preservation.md))
  asserts byte-identical round-trips for every preserved construct in this document,
  `--check` cleanliness, and idempotency (formatting twice is a fixed point).

When behavior changes: update this document, the corpus, and the goldens in the same
change.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
