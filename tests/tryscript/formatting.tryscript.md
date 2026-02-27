---
sandbox: true
env:
  NO_COLOR: "1"
  LC_ALL: C
path:
  - $TRYSCRIPT_GIT_ROOT/.venv/bin
before: |
  cp -r $TRYSCRIPT_TEST_DIR/fixtures/. fixtures/
---

# Formatting Tests

Core formatting tests covering width, plaintext, semantic, cleanups, and combinations.

## F1: Default width (88)

```console
$ flowmark fixtures/content/paragraphs-long.md
# Long Paragraphs

This is a paragraph that is right at the boundary of the default width setting. It has
exactly enough text to test.

This is a very long paragraph that should definitely be wrapped at any reasonable width
setting because it goes on and on and on with many words and phrases that make it extend
well beyond the default eighty-eight character width limit that flowmark uses by default
for line wrapping purposes in formatted output.

Short paragraph.

A paragraph with **bold text** and [a link](https://example.com) and some `inline code`
mixed in with regular text that makes wrapping more interesting because of inline
formatting.
```

## F2: Custom width (60)

```console
$ flowmark --width 60 fixtures/content/paragraphs-long.md
# Long Paragraphs

This is a paragraph that is right at the boundary of the
default width setting. It has exactly enough text to test.

This is a very long paragraph that should definitely be
wrapped at any reasonable width setting because it goes on
and on and on with many words and phrases that make it
extend well beyond the default eighty-eight character width
limit that flowmark uses by default for line wrapping
purposes in formatted output.

Short paragraph.

A paragraph with **bold text** and
[a link](https://example.com) and some `inline code` mixed
in with regular text that makes wrapping more interesting
because of inline formatting.
```

## F3: Custom width (30)

```console
$ flowmark --width 30 fixtures/content/paragraphs-long.md
# Long Paragraphs

This is a paragraph that is
right at the boundary of the
default width setting. It has
exactly enough text to test.

This is a very long paragraph
that should definitely be
wrapped at any reasonable
width setting because it goes
on and on and on with many
words and phrases that make it
extend well beyond the default
eighty-eight character width
limit that flowmark uses by
default for line wrapping
purposes in formatted output.

Short paragraph.

A paragraph with **bold text**
and
[a link](https://example.com)
and some `inline code` mixed
in with regular text that
makes wrapping more
interesting because of inline
formatting.
```

## F4: Width zero (no wrap)

```console
$ flowmark --width 0 fixtures/content/paragraphs-long.md
# Long Paragraphs

This is a paragraph that is right at the boundary of the default width setting. It has exactly enough text to test.

This is a very long paragraph that should definitely be wrapped at any reasonable width setting because it goes on and on and on with many words and phrases that make it extend well beyond the default eighty-eight character width limit that flowmark uses by default for line wrapping purposes in formatted output.

Short paragraph.

A paragraph with **bold text** and [a link](https://example.com) and some `inline code` mixed in with regular text that makes wrapping more interesting because of inline formatting.
```

## F5: Plaintext mode

```console
$ flowmark --plaintext fixtures/content/plaintext.txt && echo ""
This is plain text content without any Markdown formatting.

It has multiple paragraphs that should be wrapped at the appropriate width just like
Markdown paragraphs but without any special structure handling.

A short paragraph.

This is another long paragraph that goes on and on with enough text to test that
plaintext wrapping works correctly at various width settings for the flowmark tool.

```

## F6: Semantic line breaks

```console
$ flowmark --semantic fixtures/content/semantic-sentences.md
# Semantic Sentences

This is the first sentence.
This is the second sentence that follows it.

The quick brown fox jumps over the lazy dog.
The dog was not amused by this behavior.
It growled softly in response.

Dr. Smith went to Washington.
He met with Mr. Jones at 3 p.m. to discuss the proposal.

This sentence ends with an exclamation!
And this one ends with a question?
The last one is normal.

Here is a sentence with a (parenthetical aside) in the middle.
And here is another one.

Check the documentation at [example.com](https://example.com).
It has all the details you need.
```

## F7: Cleanups (unbold headings)

```console
$ flowmark --cleanups fixtures/content/headings.md
# Heading Level 1

## Heading Level 2

### Heading Level 3

#### Heading Level 4

##### Heading Level 5

###### Heading Level 6

## Bold Heading That Should Be Cleaned

### Another Bold Heading

Regular paragraph after headings.
```

## F8: Semantic + width 60

```console
$ flowmark --semantic --width 60 fixtures/content/semantic-sentences.md
# Semantic Sentences

This is the first sentence.
This is the second sentence that follows it.

The quick brown fox jumps over the lazy dog.
The dog was not amused by this behavior.
It growled softly in response.

Dr. Smith went to Washington.
He met with Mr. Jones at 3 p.m. to discuss the proposal.

This sentence ends with an exclamation!
And this one ends with a question?
The last one is normal.

Here is a sentence with a (parenthetical aside) in the
middle. And here is another one.

Check the documentation at
[example.com](https://example.com).
It has all the details you need.
```

## F9: Semantic + cleanups

```console
$ flowmark --semantic --cleanups fixtures/content/headings.md
# Heading Level 1

## Heading Level 2

### Heading Level 3

#### Heading Level 4

##### Heading Level 5

###### Heading Level 6

## Bold Heading That Should Be Cleaned

### Another Bold Heading

Regular paragraph after headings.
```

## F10: Comprehensive default formatting

Tests that ALL Markdown structures are preserved through formatting.
Asserts full output with no truncation. This test validates:
- Reference links preserved as reference syntax (not inlined)
- Footnote definitions stay in their original position (not moved to end)
- Nested list spacing matches Python (no extra blank lines)
- All other Markdown structures round-trip correctly

~~~console
$ flowmark fixtures/content/comprehensive.md
---
title: Comprehensive Test Document
author: Test Suite
date: 2024-01-15
---
# Heading Level 1

## Heading Level 2

### Heading Level 3

#### Heading Level 4

##### Heading Level 5

###### Heading Level 6

## **Bold Heading for Cleanup Testing**

This is a long paragraph that should be wrapped at various widths for testing purposes.
It contains enough text to definitely exceed the default eighty-eight character width
limit and also the sixty character width. The quick brown fox jumps over the lazy dog
and keeps running.

First sentence of a multi-sentence paragraph. Second sentence that follows the first
one. Third sentence that wraps up the paragraph.

- Tight item one

- Tight item two

- Tight item three

- Loose item one

- Loose item two

- Loose item three

- First level
  - Second level
    - Third level deep
  - Back to second level

- Back to first level

1. Ordered item one
2. Ordered item two
3. Ordered item three

> This is a blockquote with a paragraph of text inside it.
> 
> Second paragraph in the blockquote.

```python
def example():
    return "code block preserved"
```

~~~bash
echo "tilde code block"
~~~

Use `inline code` with special characters like `"quotes"` and `it's`.

He said "hello" and she said 'goodbye' to everyone.

It's a test of don't and won't contractions.

The sentence trails off... and then continues.

Backslash escapes: \* not bold \* and \# not a heading.

An [inline link](https://example.com) and a [reference link][ref1].

[ref1]: https://example.com "Example Reference"

![An image](https://example.com/image.png)

**Bold text** and *italic text* and ~~strikethrough~~.

<div class="html-block"> HTML block content. </div>

Inline <em>HTML emphasis</em> here.

> [!NOTE]
> This is a note alert block.

* * *

| Col A | Col B |
| --- | --- |
| 1 | 2 |
| 3 | 4 |

This has a footnote[^1] reference.

[^1]: Footnote definition here.

Inline math $x^2 + y^2 = z^2$ and display math:

$$ \sum_{i=1}^{n} i = \frac{n(n+1)}{2} $$

Final paragraph of the comprehensive document.
~~~

## F11: Width 2 (edge case — very small width does not crash)

```console
$ flowmark --width 2 fixtures/content/simple.md
# Simple Document

This
is
a
basic
paragraph
with
some
text.

Another
paragraph
here.
```

## F12: Idempotency — running twice produces identical output

```console
$ flowmark fixtures/content/comprehensive.md > /tmp/first.md && flowmark /tmp/first.md > /tmp/second.md && diff /tmp/first.md /tmp/second.md && echo "idempotent"
idempotent
```
