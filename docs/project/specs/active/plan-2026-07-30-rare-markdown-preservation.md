# Feature: Rare Markdown Syntax Preservation

**Date:** 2026-07-30 (last updated 2026-07-30)

**Author:** Claude (drafted for review), from issues by k0pernikus and jlevy

**Status:** Draft

## Overview

Flowmark parses Markdown to an AST and re-emits it normalized and re-wrapped.
Any construct the parser does not model as an opaque node is treated as prose and
reflowed, and several renderer methods re-emit hardcoded markers regardless of the
source form. Both behaviors silently corrupt real-world Markdown dialects: GitLab
Flavored Markdown (GLFM), Pandoc, Obsidian, MkDocs/Python-Markdown, kramdown/Jekyll,
MyST, and others.

This spec is the research document and implementation plan for fixing that.
It maps out every known rare-but-real construct family, cites the authoritative syntax
documentation for each, records flowmark’s current (empirically verified) behavior, and
defines the correct desired behavior.
It then defines the mechanisms, the platform-neutral test strategy (a rare-syntaxes test
document plus tryscript golden tests, portable unchanged to the Rust port), and the
implementation phases.

The underlying principle this work enforces, permanently:

> **Flowmark must never break syntax it does not understand.** A construct flowmark
> cannot model is passed through verbatim.
> A marker or delimiter choice is only normalized when the normalization is
> render-identical in every supported dialect.
> Formatting is idempotent, and a formatted document is `--check`-clean.

## Goals

- Fix every construct in the corruption ledger below so it round-trips byte-identical
  (Tier 1 and Tier 2) or survives with render-identical output (Tier 3).
- Preserve author marker choices where the choice is semantic in any major dialect:
  emphasis `_`/`*`, strikethrough `~`/`~~`, thematic break style, alert label case and
  titles.
- Add a block-level opaque-passthrough mechanism (the Python analog of the Rust port’s
  pre-parse passthrough), covering fenced and line-prefixed block families.
- Ship a new, self-contained rare-syntaxes test corpus: fixture documents plus a
  tryscript golden file plus a golden testdoc, all platform-neutral and runnable
  unchanged against the Rust port’s binary.
- Keep `flowmark --check` clean and formatting idempotent across the whole corpus,
  including the GLFM reproducer corpus from issue #67.

## Non-Goals

- Parsing or rendering any of these dialects (no TOC generation, no description-list
  AST, no `:::` info-string semantics).
  We preserve; we do not interpret.
- Formatting the *interior* of protected regions (e.g. re-wrapping prose inside a `:::`
  div or a `>>>` quote).
  Interiors pass through verbatim in this iteration; interior formatting is a possible
  future enhancement, noted per-construct.
- New CLI flags or configuration.
  Corruption fixes are unconditional; a formatter must never corrupt regardless of
  flags. Marker preservation becomes the default behavior.
- Changing intentional, render-identical normalizations that are safe in all dialects
  (setext to ATX headings, `1)` to `1.` markers, table delimiter width, two-space to
  backslash hard breaks, reference-link normalization).
  These remain flowmark house style.

## Background

Three GitHub issues drive this work:

- [#67 — Feature Request: Support GitLab Flavored Markdown](https://github.com/jlevy/flowmark/issues/67):
  a sweep of all 22 GLFM construct families against flowmark 0.7.3 found three
  constructs destroyed (`[[_TOC_]]`, tight description lists, `>>>` multiline
  blockquotes), five rewritten cosmetically, and the rest byte-identical.
  Reproducer:
  [k0pernikus/flowmark-glfm-repro](https://github.com/k0pernikus/flowmark-glfm-repro)
  (checked out and verified locally; its three minimal inputs are incorporated into the
  new corpus here).
- [#62 — Preserve uncommon-but-real Markdown constructs verbatim](https://github.com/jlevy/flowmark/issues/62):
  a corruption ledger verified against the Rust port (flowmark-rs 0.3.1), covering
  Pandoc tables, Obsidian callouts, `:::` containers, `+++` frontmatter, definition
  lists, block math, attribute lists, line blocks, and more, with the explicit
  “preserve, don’t parse” doctrine and the observation that no single standard exists
  for several of these families.
- Prior incidents in the same family: [#35](https://github.com/jlevy/flowmark/issues/35)
  (multi-line HTML comment line breaks),
  [#17](https://github.com/jlevy/flowmark/issues/17) (Markdoc tags),
  [#11](https://github.com/jlevy/flowmark/issues/11) (GitHub callouts in quotations).

### How corruption happens (three mechanisms)

Empirical verification of the full battery below against the current Python head shows
every corruption arises from one of three mechanisms:

1. **Paragraph reflow of continuation lines.** CommonMark lazy continuation makes
   `Term`⏎`: Def` a single paragraph; the line wrapper then joins the lines.
   This destroys description lists, `:::` div fences adjacent to content, `+++`
   frontmatter bodies, abbreviation definition lines, kramdown IALs, Obsidian callout
   title lines, `$$`/`\[ \]` math blocks, raw HTML blocks, and `%%` comment blocks.
   Line blocks lose their `|` on wrapped continuation lines the same way.
2. **Parse-time misinterpretation.** The parser models the bytes as a *different*
   construct, after which the original spelling is unrecoverable: `>>>` becomes three
   nested `Quote` nodes; `_TOC_` becomes an `Emphasis` node; `~2~` becomes a
   `Strikethrough` node; a 4-space-indented admonition body becomes an indented code
   block (then re-emitted as a *fenced* code block); a Pandoc multiline table’s dash
   rows become thematic breaks and setext headings.
3. **Renderer marker normalization.** The renderer re-emits a hardcoded marker
   regardless of the source: emphasis is always `*`
   ([flowmark_markdown.py](../../../src/flowmark/formats/flowmark_markdown.py)
   `render_emphasis`), strikethrough always `~~`, thematic breaks always `* * *`,
   blockquotes always one `> ` per nesting level (producing `> > > ` with trailing
   whitespace from a `>>>` fence), alert labels always uppercase, table delimiters
   always `:---:`.

Mechanisms 1 and 2 destroy constructs (rendered output loses the construct); mechanism 3
rewrites them (output renders the same in the origin dialect but breaks tokens that
other dialects treat as opaque, e.g. `[[_TOC_]]`).

### Why “preserve, don’t parse”

CommonMark lists both directives and attributes only as
[proposed extensions](https://github.com/commonmark/commonmark-spec/wiki/Proposed-Extensions).
The `:::` fence alone has at least four mutually incompatible dialects (Pandoc
`fenced_divs`, markdown-it-container, generic directives/remark-directive, MyST
`colon_fence`), and `{.class}` has incompatible Pandoc, kramdown, and markdown-it-attrs
forms (issue #62 documents this in detail).
Wikilinks are worse: GitLab’s pipe order is `[[display|target]]` while Obsidian’s is
`[[target|display]]`, so no formatter can even know which side of the pipe is the link
target. There is no correct way to *parse* these; there is only a correct way to *not
break* them. This mirrors the Rust port’s existing pre-parse passthrough mechanism
(`flowmark-rs/src/formatter/filling.rs`, COMRAK-WORKAROUND1–12), which already protects
reference links, footnote definitions, autolinks, escapes, and template tags — the gap
is which constructs are wired in, and that the existing protections are inline-level
while several corruptions are block-level.

## Research: dialect documentation survey

This section records the authoritative syntax rules for every construct family in scope,
with citations.
Rules quoted here are the basis for the detection patterns in the design.
Quotes were pulled from the cited pages on 2026-07-30.

### Sources

| Dialect | Document | URL |
| --- | --- | --- |
| GLFM | GitLab Flavored Markdown reference | <https://docs.gitlab.com/user/markdown/> |
| GLFM (wikis) | GitLab wiki Markdown links | <https://docs.gitlab.com/user/project/wiki/markdown/> |
| GLFM | `[TOC]` behavior called unintended | <https://gitlab.com/gitlab-org/gitlab/-/issues/359077> |
| GFM | GitHub Flavored Markdown spec | <https://github.github.com/gfm/> |
| GitHub | Alerts documentation | <https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax> |
| CommonMark | Spec 0.31.2 | <https://spec.commonmark.org/0.31.2/> |
| CommonMark | Proposed extensions wiki | <https://github.com/commonmark/commonmark-spec/wiki/Proposed-Extensions> |
| Pandoc | Manual, “Pandoc’s Markdown” | <https://pandoc.org/MANUAL.html> |
| Obsidian | Callouts | <https://help.obsidian.md/callouts> |
| Obsidian | Basic/advanced syntax (comments, embeds, block refs) | <https://help.obsidian.md/syntax> |
| Python-Markdown | Admonition extension (MkDocs) | <https://python-markdown.github.io/extensions/admonition/> |
| MkDocs Material | Admonitions, content tabs | <https://squidfunk.github.io/mkdocs-material/reference/admonitions/>, <https://squidfunk.github.io/mkdocs-material/reference/content-tabs/> |
| kramdown | Syntax (IALs) | <https://kramdown.gettalong.org/syntax.html> |
| PHP Markdown Extra | Abbreviations | <https://michelf.ca/projects/php-markdown/extra/> |
| markdown-it | Container plugin | <https://github.com/markdown-it/markdown-it-container> |
| markdown-it | Attrs plugin | <https://github.com/arve0/markdown-it-attrs> |
| MyST | Optional syntax (colon fence, attrs), roles | <https://myst-parser.readthedocs.io/en/latest/syntax/optional.html>, <https://myst-parser.readthedocs.io/en/latest/syntax/roles-and-directives.html> |
| CriticMarkup | Spec / toolkit | <https://github.com/CriticMarkup/CriticMarkup-toolkit> |
| Hugo | Front matter formats | <https://gohugo.io/content-management/front-matter/> |
| MathJax | TeX delimiters (`\(`/`\[` defaults) | <https://docs.mathjax.org/en/latest/input/tex/delimiters.html> |

### GLFM constructs (issue #67)

**Table of contents.** GitLab: “Add one of these tags on their own line …: `[[_TOC_]]`
or `[TOC]`.” GitLab’s own docs present the tag inside a code block “to work around a
Markdown bug” — the token is fragile by design, and the `[TOC]` single bracket behavior
is documented as unintended (GitLab issue 359077). `[[…]]` is also GitLab’s wiki-link
syntax; GitLab’s parser treats the interior of `[[…]]` as opaque (verified in #67:
asterisks survive verbatim into both `href` and link text — GitLab does not parse
emphasis inside wikilinks).

**Wiki links.** `[[Home]]`, or with display text: “If the page slug is different from
the title you want to display, use the pipe (`|`) character to separate the display text
from the page slug” — i.e. `[[How to use GitLab|how-to-use-gitlab]]`, display text
*first*. Note this is the reverse of Obsidian’s `[[target|display]]` order — a formatter
must treat both sides as opaque.

**Description lists.** GitLab (introduced 17.7, GitLab issue 26314): “place the term on
one line, with the description on the next line beginning with a colon.”
Multiple `:` lines give multiple descriptions; “You can also have a blank line between
the term and description” (the loose form, which flowmark already keeps as separate
blocks).

**Multiline blockquote.** GitLab: “Create multi-line blockquotes fenced by `>>>`.” The
fences are lines containing exactly `>>>`; everything between is one quote.

**Math.** Inline: `$`a^2`$` or `$a^2$`. Block: “Math written between double dollar signs
(`$$...$$`) or in a code block with the language declared as `math`.”

**Alerts.** GLFM supports the same five types as GitHub (note, tip, important, caution,
warning); GitLab’s examples are lowercase, GitHub’s docs specify the uppercase keywords
`[!NOTE]` etc., and both platforms render either case.
Case is an author choice, not a syntax requirement.
GitHub: “Alerts cannot be nested within other elements,” and GitHub supports no custom
titles (Obsidian and GLFM do).

**Reference tokens.** `#123`, `!456`, `~label`, `%milestone`, `[issue:123]`,
`[work_item:123]`, `@user`, etc.
are plain-text tokens to CommonMark; they only break when their interior accidentally
parses as emphasis (`[issue:_123_]`).

### Pandoc constructs

Quotes below are from the Pandoc manual ("Pandoc’s Markdown" chapter).

**Definition lists.** “Each term must fit on one line, which may optionally be followed
by a blank line, and must be followed by one or more definitions.
A definition begins with a colon or tilde, which may be indented one or two spaces.”
Loose form: “If you leave space before the definition …, the text of the definition will
be treated as a paragraph.”
Multiple definitions per term are allowed.

**Line blocks.** “A line block is a sequence of lines beginning with a vertical bar
(`|`) followed by a space.
The division into lines will be preserved in the output, as will any leading spaces.”
Continuation: “The lines can be hard-wrapped if needed, but the continuation line must
begin with a space.”

**Multiline tables.** “They must begin with a row of dashes, before the header text
(unless the header row is omitted)” and “must end with a row of dashes, then a blank
line. The rows must be separated by blank lines.”
Captions: “a paragraph beginning with the string `Table:` (or `table:` or just `:`),”
before or after the table.
Simple tables use the same per-column dashed header separator without the bounding rows.

**Grid tables.** Borders from `+`, `-`, `|`; “The row of `=`s separates the header from
the table body, and can be omitted for a headerless table.”
Alignment colons on the separator line.

**Fenced divs.** “A Div starts with a fence containing at least three consecutive colons
plus some attributes.”
Attributes are braced (`{.class}`) or “a single unbraced word, which will be treated as
a class name.” “The Div ends with another line containing a string of at least three
consecutive colons,” and “the number of colons in the closing fence need not match the
number in the opening fence.”
Nesting: “Opening fences are distinguished because they *must* have attributes”; “fences
without attributes are always closing fences.”

**Bracketed spans.** `[text]{.class key="val"}` — “a bracketed sequence of inlines …
will be treated as a `Span` with attributes if it is followed immediately by
attributes.”

**Superscript/subscript.** `^text^` and `~text~`; “The text between `^...^` or `~...~`
may not contain spaces or newlines” (spaces must be backslash-escaped).
Note the direct conflict with GFM strikethrough below: `H~2~O` is subscript in Pandoc
and strikethrough on github.com.

**YAML metadata blocks.** “delimited by a line of three hyphens (`---`) at the top and a
line of three hyphens (`---`) or three dots (`...`) at the bottom.”
“The initial line `---` must not be followed by a blank line.”

**Math.** `tex_math_dollars` is `$…$`/`$$…$$`; MathJax’s *default* TeX delimiters are
`\(…\)` inline and `\[…\]` display (per MathJax docs), so `\[`/`\]` display blocks are
common in the wild even though Pandoc models them under `tex_math_single_backslash`.

### Obsidian constructs

**Callouts.** `> [!type]` on the first line of a blockquote.
“The type identifier is case-insensitive.”
An optional custom title follows on the same line (`> [!tip] My Title`); a fold marker
directly after the closing bracket makes it collapsible: `> [!faq]-` (collapsed by
default) or `> [!faq]+` (expanded).
Unknown type identifiers silently fall back to the `note` style, so arbitrary `[!word]`
tokens are meaningful.
Callouts nest via additional `>` levels.

**Comments.** Inline `%%…%%` and block form: `%%` on its own line opens, `%%` on its own
line closes, spanning multiple lines.
“Comments are only visible in Editing view.”
No escape mechanism exists.

**Wikilinks, embeds, block references.** `[[Page]]`, `[[Page#Heading]]`,
`[[Page|display]]` (target first — the reverse of GitLab’s order); `![[Page]]` embeds
("Prefixing an internal link with an exclamation mark (!) allows you to embed the linked
content"), including `![[image.png|100x145]]` dimensions.
`^block-id` appended at the end of a block creates a block anchor (IDs limited to Latin
letters, numbers, and dashes) targeted by `[[Page#^block-id]]`.

### MkDocs / Python-Markdown constructs

**Admonitions.** Opener `!!! type "Optional Title"` on its own line; the type “must be a
single word” (extra words become additional CSS classes); an empty title `""` suppresses
the title. Body content is indented four spaces beneath the opener.

**Collapsible admonitions and tabs (MkDocs Material).** `???` instead of `!!!` renders a
collapsed `<details>` block; “adding a `+` after the `???` token renders the block
expanded” (`???+`). Content tabs: `=== "Tab Title"` with the body indented four spaces;
consecutive `===` blocks form a tab set.
All three use the same 4-space-indented body rule as admonitions.

### kramdown (Jekyll) constructs

**Inline attribute lists (IALs).** Block IAL `{: .class #id key="value"}` (colon after
the brace): “A block IAL … has to be put directly before or after the block-level
element to which the attributes should be attached”; “the block IAL is ignored in all
other cases, for example, when the block IAL is surrounded by blank lines.”
Span IALs attach “directly after the span-level element … no additional character is
allowed between.” The strict adjacency rule means a formatter that *joins* an IAL line
into a paragraph or *inserts* a blank line between a heading and its IAL silently breaks
the attachment.

### PHP Markdown Extra constructs

**Abbreviations.** Definition lines of the form `*[HTML]: HyperText Markup Language`,
one per line, anywhere in the document; definitions are stripped from output and
“abbreviations are case-sensitive, and will span on multiple words when defined as
such.” Empty definitions (`*[ABBR]:`) are valid.

### markdown-it and MyST constructs

**markdown-it-container.** `::: name` opens (info string validated by the plugin), bare
`:::` closes; “content is rendered as markdown markup.”
Nesting by longer outer fences (`::::` outer, `:::` inner), following fence conventions.

**markdown-it-attrs.** `{.class #id key=value}` (no colon, unlike kramdown), placed on
the line after a block, or immediately after an inline element; spacing before the `{`
selects inline vs list-item vs container scope.

**MyST.** Colon fence directives `:::{note}` … `:::` — “a closing colon fence with *at
least* as many colons as the opening fence will close the block”; block attrs
`{#id .class}` on the line *before* a block; inline attrs immediately *after* an inline
element; roles `` {rolename}`content` ``; backtick-fence directives `` ```{name} `` are
ordinary code fences to other parsers (already safe).

### CriticMarkup

Five inline patterns, which may contain spaces: `{++ins++}`, `{--del--}`,
`{~~old~>new~~}` (substitution separator `~>`), `{==mark==}`, `{>>comment<<}`.
Highlights are conventionally paired: `{==text==}{>>comment<<}`. “Newlines should be
avoided as much as possible within CriticMarkup tags,” and there is no escape mechanism,
so a formatter must not reflow across these delimiters.

### Hugo front matter

“Hugo determines the front matter format by examining the delimiters”: YAML `---`, TOML
`+++`, JSON `{`…`}`, each at the start of the file.

### CommonMark and GFM rules relevant to normalization decisions

- Thematic breaks: three or more matching `-`, `_`, or `*`, optionally spaced
  ([spec §4.1](https://spec.commonmark.org/0.31.2/#thematic-breaks)) — `---`, `***`, and
  `* * *` all render identically *in CommonMark*; but `---` is also a setext underline
  and a frontmatter delimiter, and Pandoc multiline tables are delimited by dash rows,
  so thematic-break rewriting is not context-free.
- Emphasis: `*` and `_` with flanking rules
  ([spec §6.2](https://spec.commonmark.org/0.31.2/#emphasis-and-strong-emphasis)).
  `_TOC_` between `[[`/`]]` is genuinely emphasis under CommonMark — the corruption is
  re-emitting it with a different delimiter, not parsing it.
- Hard line breaks: trailing two spaces or trailing backslash
  ([spec §6.7](https://spec.commonmark.org/0.31.2/#hard-line-breaks)).
- Setext headings ([spec §4.3](https://spec.commonmark.org/0.31.2/#setext-headings)):
  the underline is a bare run of `=` or `-`, which is what disambiguates it from MkDocs
  `=== "Tab"` openers (which always carry trailing text).
- GFM strikethrough ([GFM spec §6.5](https://github.github.com/gfm/)): “Strikethrough
  text is any text wrapped in a matching pair of one or two tildes (`~`)” — single tilde
  is spec-valid, the pair must match in length, and “three or more tildes do not create
  a strikethrough.” Since `~x~` is subscript in Pandoc and strikethrough in GFM, the
  delimiter count is semantic across dialects and must be preserved, never normalized.

## The construct ledger: current vs. desired behavior

Current behavior was verified empirically on this repo’s head (equivalent to 0.7.3) with
a 47-file battery, under default flags and under `--semantic --cleanups`; the result
classes were identical in both modes except where noted.
“Verbatim” in the desired column means byte-identical round-trip, and `--check` exits
clean.

Severity tiers: **T1** = construct destroyed (rendering loses it); **T2** = rewritten in
a way that breaks it in some real dialect; **T3** = render-identical rewrite or
hardening of an accidental pass; **OK** = already byte-identical (locked in by new
tests).

| # | Construct | Dialects | Input example | Current behavior (verified) | Desired behavior | Tier |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | TOC tag | GLFM | `[[_TOC_]]` | `[[*TOC*]]` — becomes broken wikilink | Verbatim | T1 |
| 2 | Wikilinks w/ underscores | GLFM, Obsidian | `[[_draft_]]`, `[[Home\|_sub_]]` | `[[*draft*]]`, `[[Home\|*sub*]]` | Verbatim | T1 |
| 3 | Reference tokens w/ underscores | GLFM | `[issue:_123_]` | `[issue:*123*]` | Verbatim | T1 |
| 4 | Underscore emphasis | CommonMark | `_em_`, `__strong__` | `*em*`, `**strong**` | Verbatim (preserve delimiter) | T2 |
| 5 | Description list, tight | GLFM | `Term`⏎`: Def` | Joined: `Term : Def` | Verbatim (keep line breaks) | T1 |
| 6 | Description list, multi | GLFM | `Fruits`⏎`: apple`⏎`: orange` | Joined into one line | Verbatim | T1 |
| 7 | Definition list, loose | Pandoc, GLFM | `Term`⏎⏎`:   Def` | `:   ` → `: ` (marker spacing collapsed) | Verbatim (keep `:` line as authored) | T2 |
| 8 | Multiline blockquote fence | GLFM | `>>>`⏎…⏎`>>>` | `> > > ` ×2 with trailing spaces; content leaves the quote | Verbatim, incl. fences | T1 |
| 9 | Fenced divs / containers | Pandoc, markdown-it, MyST, remark | `::: warning`⏎…⏎`:::` | Fence joined into prose | Verbatim block (fences + interior) | T1 |
| 10 | TOML frontmatter | Hugo | `+++`⏎…⏎`+++` | Reflowed into one paragraph | Verbatim, like `---` frontmatter | T1 |
| 11 | YAML frontmatter closed by `...` | Pandoc | `---`⏎…⏎`...` | Not recognized; body gains stray blank line | Recognized; verbatim | T2 |
| 12 | Block math `$$` | GLFM, GFM, Pandoc | `$$`⏎`a^2`⏎`$$` | Joined: `$$ a^2 $$` | Verbatim | T1 |
| 13 | Display math `\[…\]` | MathJax default | `\[`⏎`E=mc^2`⏎`\]` | Joined onto one line | Verbatim | T1 |
| 14 | Inline math `\(…\)` | MathJax default | `\(x^2\)` | Survives only by luck; splittable at wrap | Atomic at wrap | T3 |
| 15 | Pandoc multiline table | Pandoc | dash-row–delimited block | **Catastrophic**: dash rows → `* * *` + `##` headings; not idempotent | Verbatim block | T1 |
| 16 | Pandoc simple table | Pandoc | per-column dash separator | Same failure family as #15 | Verbatim block | T1 |
| 17 | Pandoc grid table | Pandoc | `+---+` / `+===+` | Survives via table-row heuristic (accidental) | Verbatim block (first-class) | T3 |
| 18 | Obsidian callout title/fold | Obsidian | `> [!tip]+ My Title`⏎`> body` | Title line joined with body | Verbatim first line; body preserved as quote | T1 |
| 19 | Alert label case | GFM, GLFM, Obsidian | `> [!note]` | `> [!NOTE]` | Verbatim (preserve case) | T2 |
| 20 | MkDocs admonition | Python-Markdown | `!!! note "Title"` + 4-space body | Body converted to fenced code block | Verbatim block (opener + indented body) | T1 |
| 21 | MkDocs collapsible/tabs | MkDocs Material | `??? tip`, `???+ note`, `=== "Tab"` + body | Body converted to fenced code block | Verbatim block | T1 |
| 22 | Pandoc sub/superscript | Pandoc | `H~2~O`, `x^2^` | `H~~2~~O` (single `~` re-emitted as `~~`); `^…^` safe | Verbatim (preserve delimiter count) | T1 |
| 23 | Strikethrough | GFM | `~~gone~~`, `~gone~` | `~~` stays; single `~` doubled | Verbatim (preserve delimiter count) | T2 |
| 24 | Line blocks | Pandoc | `\| verse line` | Long lines wrap; continuation loses `\|` | Verbatim lines, never wrapped | T1 |
| 25 | Abbreviations | PHP Extra, kramdown | `*[HTML]: …` lines | Consecutive lines joined | Verbatim lines | T1 |
| 26 | Raw multi-line HTML block | HTML | `<div>`⏎…⏎`</div>` | Collapsed onto one line | Verbatim line structure | T1 |
| 27 | `<details>/<summary>` | GFM (HTML) | multi-line details block | Collapsed onto one line | Verbatim line structure | T1 |
| 28 | Obsidian `%%` comment block | Obsidian | `%%`⏎…⏎`%%` | Joined onto one line | Verbatim block | T2 |
| 29 | kramdown block IAL | kramdown/Jekyll | para⏎`{: .class}` | Joined into paragraph (default mode); heading IAL separated by forced blank line | IAL line kept on own line, adjacency preserved | T2 |
| 30 | Attribute span | Pandoc, markdown-it-attrs | `[text]{.mark}` | Survives (atomic gluing) — accidental | Atomic at wrap (first-class) + tests | T3 |
| 31 | Standalone `{.attr}` line / heading `{#id}` | Pandoc, markdown-it-attrs, MyST | `# H {#id}`, `{.attr}` | Survives | Lock in with tests | OK |
| 32 | CriticMarkup | CriticMarkup | `{==mark==}`, `{>>c<<}`, `{~~a~>b~~}` | Survives short lines; splittable at wrap | Atomic at wrap | T3 |
| 33 | MyST roles | MyST | `` {sub}`x` `` | Survives (code-span gluing) | Lock in with tests | OK |
| 34 | Wikilink wrap atomicity | GLFM, Obsidian | `[[Wiki Page]]`, `![[Embed]]` mid-sentence | Survives; splittable in principle | Atomic at wrap | T3 |
| 35 | Obsidian block anchor | Obsidian | `text ^block-id` | Semantic wrap may move `^id` to next line | Keep anchor glued to sentence end | T3 |
| 36 | Thematic break style | CommonMark | `---`, `***`, `___` | Always rewritten to `* * *` | Verbatim (preserve source style) | T2 |
| 37 | Table delimiter width/alignment | GFM | `\| :----: \|` | Normalized to `:---:` | Keep normalizing (render-identical, house style) | — |
| 38 | Setext headings | CommonMark | `Title`⏎`=====` | Converted to ATX `#` | Keep converting (render-identical, house style) | — |
| 39 | Hard break two-space | CommonMark | `line␠␠`⏎ | Converted to `\` | Keep converting (two-space form is invisible; documented) | — |
| 40 | Ordered list `1)` | CommonMark | `1) item` | Converted to `1.` | Keep converting (house style; note adjacent-list edge in docs) | — |
| 41 | Frontmatter trailing blank | — | `---`⏎…⏎`---`⏎⏎body | Blank line after closing fence removed | Preserve as authored | T3 |
| 42 | Heading at EOF | — | file ends `## S`⏎ | Gains an extra trailing blank line | Single trailing newline, no growth | T3 |
| 43 | GLFM inline diff | GLFM | `{+add+}`, `[-del-]` | Byte-identical | Lock in with tests | OK |
| 44 | GLFM placeholders / includes | GLFM | `%{gitlab_server}`, `::include{file=x}` | Byte-identical | Lock in with tests | OK |
| 45 | `[TOC]` bare form | GLFM, Python-Markdown | `[TOC]` | Byte-identical | Lock in with tests | OK |
| 46 | GitLab references | GLFM | `#123`, `!456`, `~"x"`, `[epic:9]`… | Byte-identical | Lock in with tests | OK |
| 47 | Inline math | GLFM, Pandoc | `$x$`, `$`x`$` | Byte-identical | Lock in with tests | OK |
| 48 | Emoji shortcodes | GFM et al. | `:smile:` | Byte-identical | Lock in with tests | OK |
| 49 | Multi-line HTML comments | HTML | `<!--`⏎…⏎`-->` | Byte-identical standalone (see #35 for in-paragraph case) | Lock in with tests, incl. #35 case | OK |
| 50 | Tilde/long code fences | CommonMark | `~~~lang`, four-backtick fences | Byte-identical (fence char/len preserved) | Lock in with tests | OK |

Notes on the “house style” rows (37–40): these are deliberate normalizations that are
render-identical in CommonMark and all surveyed dialects, so they stay.
They are listed so the decision is explicit and documented, and each gets a regression
test asserting the *normalized* output.
If a future dialect makes one of them semantic, it moves into the preservation set —
that is the standing rule from the principle above.

## Design

### Approach: four mechanisms, matched to the corruption paths

**Mechanism A — opaque block passthrough (new).** A pre-parse scan identifies protected
block regions by line patterns, dialect-agnostically.
Protected regions are carried through parse/render byte-identical and re-emitted at
their block position.
Implementation options, decided at implementation time, in preference order:

1. *Span-faithful re-emission:* the `CustomParser` already records exact source spans
   for every block element (`element.span`, see `markdown_ast.block_span`); a protected
   region renders as `source[start:end]` verbatim.
   This requires the region to parse as a clean sequence of block elements, which the
   pre-parse scan guarantees by construction for fence-delimited families.
2. *Pre-parse extraction:* replace the region with a placeholder block (the Rust port’s
   PUA-marker technique, COMRAK-WORKAROUND-style) and restore after render.
   Proven in the Rust port; use where span-faithful re-emission is awkward.

Detection rules (all anchored at line starts, outside code fences and frontmatter; first
match wins; regions never nest across each other):

| Family | Opens | Closes | Notes |
| --- | --- | --- | --- |
| Multiline blockquote | line is `>{3,}` exactly | next line that is `>{3,}` exactly | Unclosed: protect to EOF (never corrupt). Ledger #8 |
| Colon fence (divs/containers/MyST) | `:{3,}` + info text | bare `:{3,}` line, stack-matched; closer length need not match opener (Pandoc; MyST requires ≥, satisfied trivially since fences are preserved verbatim) | Openers have info; bare colon runs are closers (Pandoc rule). An unmatched bare fence line is left verbatim. Ledger #9 |
| Dollar math | line is `$$` or starts `$$` | line is/ends `$$` | Single-line `$$…$$` paragraphs also protected. Ledger #12 |
| Bracket math | line is `\[` exactly | line is `\]` exactly | Ledger #13 |
| Admonition/tab | `!!!`, `???`, `???+`, or `===` + space + text | end of its indented (≥4 spaces) body, including interior blank lines | `===` opener requires trailing text (a bare `=`/`-` run is a setext underline, ledger #38). Ledger #20–21 |
| Table, dashed | block containing a multi-group dash row `:?-+( +:?-+)+` | per Pandoc: closing dash row + blank line (multiline); else end of the contiguous block (simple) | Covers simple + multiline tables incl. bounding rows; caption lines (`Table:`/`:` prefix) ride along. A *single-group* dash row alone is never a table trigger (stays thematic break / setext). Ledger #15–16 |
| Table, grid | line starts `+-` or `+=` | last contiguous line starting `+` or `\|` | Ledger #17 |
| `%%` comment block | line is `%%` exactly | next line that is `%%` exactly | Obsidian. Ledger #28 |
| HTML block | line starts `<[a-zA-Z!/]` | end of contiguous non-blank block | Preserves internal line structure only; no HTML parsing. Replaces reliance on the disabled marko `HTMLBlock` (see `CustomHTMLBlock`, disabled due to marko #202). Ledger #26–27 |
| Frontmatter `+++` | first line of file is `+++` | `+++` | Extends `split_frontmatter`, mirroring `---`. Ledger #10 |
| Frontmatter `...` close | first line `---` | `---` **or** `...` | Pandoc rule. Ledger #11 |

**Mechanism B — paragraph-interior line protection (new).** For constructs that are
*lines inside a paragraph* rather than delimited regions, the paragraph renderer keeps
the line break before (and the verbatim content of) any line matching:

| Line pattern | Construct | Ledger |
| --- | --- | --- |
| `:` or `~` + space(s) + text, at 0–2 spaces indent (incl. the deep-indent `:   ` form) | Description/definition list description line | #5–7 |
| `\| ` at line start | Line block line (when every line of the block matches and it is not a GFM table, the whole block becomes verbatim lines) | #24 |
| `*[…]: ` | Abbreviation definition | #25 |
| `{:` … `}` alone on line (kramdown), or `{.`/`{#` … `}` alone (markdown-it-attrs, MyST) | Block IAL / attribute line; also: do not force a blank line between a heading and a following IAL line (kramdown adjacency rule) | #29, #31 |
| `[!word]` + optional `+`/`-` + optional title, as first line inside a quote | Callout marker line: preserved verbatim (case, fold, title) and never joined with the following body line | #18–19 |

These lines are excluded from sentence-joining, wrapping, and inline whitespace
normalization (verbatim within the line).

**Mechanism C — source-faithful marker re-emission (renderer changes).** The renderer
re-emits the marker the author wrote:

- *Emphasis/strong:* capture the delimiter at parse time and re-emit it.
  Marko’s `Emphasis`/`StrongEmphasis` do not record the delimiter (verified against
  marko 2.2.3), so this needs a small parser extension in the pattern of the existing
  `CustomFencedCode` (which already preserves fence char/length).
  Fixes ledger #1–4 in one rule, with no opacity heuristics and no CommonMark conflicts:
  `[[_TOC_]]` parses as `[[` + emphasis + `]]` and re-emits byte-identically once the
  delimiter is preserved.
- *Strikethrough/subscript:* `CustomStrikethrough` already captures the delimiter run in
  its match group; re-emit `match.group(1)` instead of hardcoded `~~`. Fixes #22–23 (and
  the GFM-vs-Pandoc single-tilde conflict dissolves: whatever the author meant, the
  bytes are unchanged).
- *Thematic break:* re-emit the source bytes (available via the element’s span).
  Fixes #36.
- *Alert/callout marker:* re-emit the source label case plus any trailing title/fold
  text verbatim (also covered by Mechanism B for unrecognized types).
  Fixes #18–19.
- *Blockquote:* never emit trailing whitespace after `>` prefixes on otherwise-empty
  lines (defense in depth behind the `>>>` fence protection; also fixes plain
  empty-nested-quote output).
  Part of #8.
- *Document tail:* end output with exactly one trailing newline; do not add a blank line
  after a trailing heading; preserve the authored blank line (or its absence) after
  closing frontmatter.
  Fixes #41–42.

**Mechanism D — atomic inline patterns (wrap hardening).** Additions to
`ATOMIC_PATTERNS` so the wrapper never splits: `[[…]]` wikilinks and `![[…]]` embeds,
`\(…\)` inline math, the five CriticMarkup patterns, `]{…}` attribute spans (make the
current accidental gluing explicit), and trailing `^block-id` anchors (glue to the
preceding word). Fixes #14, #30, #32, #34–35.

### Components

- `src/flowmark/formats/frontmatter.py` — `+++` and `...` delimiters (Mechanism A).
- New module (indicatively `src/flowmark/formats/protected_blocks.py`) — the pre-parse
  block scanner + restore step, invoked from `fill_markdown` alongside
  `preprocess_tag_block_spacing`.
- `src/flowmark/formats/flowmark_markdown.py` — parser subclasses capturing emphasis and
  strikethrough delimiters; renderer changes (Mechanism C); callout/description line
  handling (Mechanism B) in paragraph/quote rendering.
- `src/flowmark/linewrapping/atomic_patterns.py` — new patterns (Mechanism D).
- `tests/` — new corpus (below).

### Behavior compatibility

Marker preservation changes default output for documents that mix markers (`_em_` no
longer becomes `*em*`; `---` no longer becomes `* * *`; `> [!note]` keeps its case).
These are deliberate behavior changes, called out in the changelog and README; existing
golden files are regenerated in the same change that introduces each, and every other
normalization is locked by the house-style regression tests (ledger #37–40). Documents
previously formatted by flowmark remain stable: `* * *`, uppercase labels, and `*`
emphasis are themselves preserved forms, so a second pass changes nothing — the change
strictly reduces rewrites and cannot cause churn on already-formatted trees.

## Testing Strategy

The requirements: tests must be **platform-neutral, end-to-end, and portable to the Rust
port unchanged** — behavior expressed in test *documents*, not in Python test logic.
Flowmark already has exactly the right two vehicles, and both are shared with
flowmark-rs today:

1. **Tryscript golden tests** (`tests/tryscript/*.tryscript.md`) — Markdown documents of
   `console` blocks run against whatever `flowmark` binary is on the configured path.
   The Rust port runs the same files via its `test_tryscript_golden.rs` harness.
   Nothing about them is Python-specific.
2. **Golden testdocs** (`tests/testdocs/`) — full before/after documents compared
   byte-for-byte per mode.
   The Rust port consumes the same files, and its `tests/parity/` corner-case expected
   outputs are *generated from the Python implementation* — Python is the source of
   truth, so behavior defined here flows to the Rust port mechanically.

New test assets, all plain Markdown/fixture files:

- `tests/tryscript/fixtures/rare/` — one minimal fixture per ledger family (~30 files),
  incorporating the three files from the #67 reproducer verbatim, the #62 ledger
  examples, and the additional families found in this spec’s battery (MkDocs admonitions
  and tabs, kramdown IALs, abbreviations, sub/superscript, `%%` blocks, `...`
  frontmatter close, the line-block wrap case).
- `tests/tryscript/rare-constructs.tryscript.md` — for every *preserved* fixture:
  `flowmark <file>` output equals the input (shown inline in the console block),
  `flowmark --check <file>` exits 0, and a format-twice case per family proves
  idempotency. For *house-style* fixtures (ledger #37–40): asserts the exact normalized
  output. This one file is the end-to-end, portable statement of every behavior in the
  ledger.
- `tests/testdocs/rare-syntaxes.orig.md` (+
  `rare-syntaxes.expected.{plain,semantic,cleaned,auto}.md`) — a single comprehensive
  document embedding all 50 ledger rows with prose between them, golden-compared in all
  four standard modes like the existing testdoc.
  For preserved constructs the expected bytes equal the source bytes; any regression
  shows as a diff. Expected files are generated, reviewed hunk-by-hunk against the
  ledger, then frozen.
- Idempotency: the golden test formats each expected file a second time and asserts a
  fixed point (this catches the multiline-table class of bug, which is not idempotent
  today). The sweep must run with the full `--auto` flag set, not only default flags:
  while drafting this spec we observed a second smartquotes non-idempotency (straight
  quotes in prose adjacent to other inline elements converted only on a second pass),
  which only the full flag set exposes.
- Unit tests (Python) only for parser-internal details with no CLI surface (delimiter
  capture on the marko subclasses); everything behavioral lives in the portable layers
  above.

Porting flow to Rust after implementation: copy `fixtures/rare/`,
`rare-constructs.tryscript.md`, and the `rare-syntaxes` testdoc pair into flowmark-rs
unchanged; regenerate its parity expected files from the Python binary; implement until
green. No test logic needs translating.

## Implementation Plan

### Phase 1: Block-level protection (Mechanism A) + its tests

- [ ] `+++` frontmatter and `...` YAML close in `split_frontmatter`.
- [ ] Pre-parse protected-block scanner + verbatim restore (`>>>`, `:::`, `$$`, `\[ \]`,
  dashed/grid tables, admonitions/tabs, `%%`, HTML blocks).
- [ ] Trailing-whitespace guarantee for quote prefixes.
- [ ] Fixtures + tryscript sections for every Phase-1 family, including format-twice
  idempotency cases.

### Phase 2: Line-level and inline fidelity (Mechanisms B, C, D) + its tests

- [ ] Description/definition lines, line blocks, abbreviations, IAL lines, callout
  marker lines (Mechanism B).
- [ ] Emphasis and strikethrough delimiter capture + re-emission; thematic-break and
  alert-marker source fidelity; document-tail and frontmatter blank-line fidelity
  (Mechanism C).
- [ ] New atomic patterns: `[[…]]`/`![[…]]`, `\(…\)`, CriticMarkup, `]{…}`, `^block-id`
  (Mechanism D).
- [ ] Fixtures + tryscript sections for every Phase-2 family; house-style regression
  cases (ledger #37–40).

### Phase 3: End-to-end goldens, parity, and docs

- [ ] `rare-syntaxes` testdoc + expected files for all four modes; wire into the golden
  test run.
- [ ] Verify the #67 reproducer corpus round-trips (equivalent of `mise run format`
  producing an empty diff) and keep its three files in the corpus permanently.
- [ ] Regenerate existing goldens affected by marker preservation; review every hunk
  against the ledger.
- [ ] README + changelog: preservation guarantees, the principle statement, and the
  house-style table.
- [ ] Flip the **(planned)** status markers in
  [docs/markdown-support.md](../../../markdown-support.md) — the long-lived, definitive
  syntax-support specification — as each construct lands; that document and this spec
  must never disagree.
- [ ] flowmark-rs porting notes (files to copy, parity regeneration steps) recorded in
  the PR description and a short doc under `docs/project/research/`.

## Acceptance criteria

1. Every T1/T2 ledger row round-trips byte-identical through `flowmark`,
   `flowmark --semantic --cleanups`, and `--width 0`; `flowmark --check` is clean on the
   whole rare corpus.
2. Every OK row is locked by a test; every house-style row asserts its exact normalized
   output.
3. Formatting is idempotent across the corpus (format twice = fixed point), including
   the Pandoc multiline-table fixture that is non-idempotent today.
4. The #67 definition-of-done items all pass: `[[_TOC_]]`, `[[_draft_]]`,
   `[[Home|_sub_]]`, `[issue:_123_]` round-trip; tight description lists keep line
   breaks; `>>>` fences round-trip with no trailing whitespace; the 22-family GLFM
   corpus is `--check`-clean; two passes are a fixed point.
5. All existing tests pass, with golden regenerations reviewed and limited to
   marker-preservation diffs.
6. The new tests contain no Python logic: fixtures + tryscript + testdocs only (except
   the two parser-internal unit tests noted above).

## Open Questions

1. Should protected `:::` div *interiors* eventually be formatted as sub-documents
   (Pandoc divs contain normal Markdown, and markdown-it-container “content is rendered
   as markdown markup”)? Out of scope here; verbatim is safe and matches #62’s request.
   Revisit after adoption feedback.
2. `>>>` unclosed-fence fallback: this spec says protect to EOF (never corrupt).
   The alternative (fall back to nested-quote parsing) re-introduces the corruption for
   truncated documents.
   Confirm during review.
3. Setext `===` vs MkDocs `=== "Tab"`: the trailing-text rule disambiguates cleanly;
   flagged in case a reviewer knows a dialect writing bare `===` openers.
4. JSON (`{`-delimited) Hugo frontmatter: rare and risky to detect; deliberately
   excluded. Revisit only if reported.

## References

- [docs/markdown-support.md](../../../markdown-support.md) — the long-lived, user-facing
  specification of supported syntax that this plan implements; its **(planned)** markers
  track this spec’s ledger.
- Issues: [#67](https://github.com/jlevy/flowmark/issues/67),
  [#62](https://github.com/jlevy/flowmark/issues/62),
  [#35](https://github.com/jlevy/flowmark/issues/35),
  [#17](https://github.com/jlevy/flowmark/issues/17),
  [#11](https://github.com/jlevy/flowmark/issues/11)
- Reproducer: <https://github.com/k0pernikus/flowmark-glfm-repro> (checked out under
  `attic/`; its CI runs one job per construct)
- Rust port: <https://github.com/jlevy/flowmark-rs> (checked out under `attic/`; see
  `src/formatter/filling.rs` COMRAK-WORKAROUND1–12 and `tests/parity/`)
- All dialect documentation URLs: see the Sources table in the Research section.
- Prior art on formatter corruption: prettier
  [#19040](https://github.com/prettier/prettier/issues/19040) and
  [#15479](https://github.com/prettier/prettier/issues/15479); mdformat’s plugin
  round-trip model: <https://github.com/hukkin/mdformat>

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
