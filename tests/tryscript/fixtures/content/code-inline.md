# Inline Code

A corpus of inline code span forms, covering delimiter runs, whitespace, literal content,
and the block contexts a span can appear in.

Formatting this document must not change the content of any code span, must not change a
span's delimiter run length when the content contains backticks, and must not collapse
whitespace inside a span. Reflowing the surrounding prose is expected and fine.

The governing reference is CommonMark 0.31.2 §6.1: a code span's content has line endings
converted to spaces, and — only if it both begins and ends with a space and is not
entirely spaces — one space is stripped from each end. Everything else inside is
significant, including runs of spaces and tabs. Nothing inside is parsed as Markdown, and
backslash escapes do not apply.

## Part A: Delimiter Runs

A backtick string of length N opens a span and the next backtick string of length N closes
it. The delimiter length is therefore load-bearing whenever the content contains
backticks, and may not be shortened.

### A1. Single delimiter, no backticks inside

Use `printf` to print output.

### A2. Double delimiter, no backticks inside

A ``simple`` span, where the wider delimiter is not required.

### A3. Double delimiter with a backtick inside

Multiple backticks: ``code with `backtick` inside``.

### A4. Double delimiter with a lone backtick inside

A ``has ` tick`` span.

### A5. Triple delimiter with a double-backtick run inside

A ```outer with `` inner``` span.

### A6. A span whose only content is a backtick

The backtick character is `` ` `` on its own.

### A7. Two wide spans on one line

A ``a`` and ``b ` c`` on the same line.

### A8. A single delimiter around a triple-backtick run

Use ` ```math ` as a fenced-block info string.

### A9. Escaped backtick before a span

See `\`` and more text here.

## Part B: Whitespace Inside a Span

### B1. A run of internal spaces

Short `a    b` tail.

### B2. Padded on both sides

Short `  a  ` tail.

### B3. Padded on one side only

Short ` a` tail.

### B4. Content that is entirely spaces

Short `   ` tail.

### B5. A tab inside

Short `a	b` tail.

### B6. A line ending inside the source span

Line endings inside a span become spaces, which is correct and expected here.

Short `a +
b` tail.

## Part C: Literal Content

Nothing in a code span is parsed as Markdown, and backslash escapes do not apply. All of
these must survive unchanged.

### C1. Backslashes

Short `a \$ b` and `\n\t` tail.

### C2. Emphasis markers

Short `a *b* c` and `a _b_ c` tail.

### C3. HTML and entities

Short `<div>` and `&amp; &lt;` tail.

### C4. Straight quotes, which the typographer must not curl

Short `x = "a"` and `x'y` tail.

### C5. Ellipsis and dashes, which the typographer must not rewrite

Short `a ... b` and `a -- b` tail.

### C6. Markdown block markers

Short `# not a heading` and `- not a bullet` and `> not a quote` tail.

## Part D: Block Contexts

The same span in each context flowmark can place one in. Whitespace handling must not
depend on the surrounding block.

### D1. In a paragraph

Short `a    b` tail.

### D2. In a list item

- item with `a    b` inside

### D3. In a blockquote

> quote with `a    b` inside

### D4. In link text

Short [`a    b`](http://example.com) tail.

### D5. In a heading

#### Heading with `a    b` inside

### D6. In a table cell

| Item | Code |
| --- | --- |
| padded | `a    b` |
| wide | ``has ` tick`` |

## Part E: Wrapping

A code span is atomic: a wrap boundary moves it whole rather than splitting it, and its
content is never escaped even when it would otherwise look like a block marker.

### E1. A span crossing the wrap column

Filler words to push the code span across the wrap column boundary here now ok `a + b + c + d` tail.

### E2. A span whose content starts with a list marker

Filler words to push the code span across the wrap column boundary here now x `+ b + c + d` tail.

### E3. A span longer than the wrap column

Filler words to push the code span across the wrap column boundary here now ok `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` tail.
