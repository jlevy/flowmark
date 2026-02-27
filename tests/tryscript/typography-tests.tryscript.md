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

# Typography Tests

Smart quotes, ellipses, and their interaction with code blocks and escapes.

## T1: Smart quotes only

```console
$ flowmark --smartquotes fixtures/content/typography.md
# Typography Tests

He said “hello” to her.

She replied ‘goodbye’ quietly.

It’s a beautiful day, and they don’t know it won’t last.

“Nested 'single quotes’ inside double quotes” are tricky.

The sentence trails off... and then continues.

“The word trailed off...” she said quietly.

This has “bold *emphasis* inside quotes” for testing.

## Quotes in Headings

### “Quoted Heading”

Apostrophes: the cat’s meow, the '90s, rock ‘n’ roll.
```

## T2: Ellipses only

```console
$ flowmark --ellipses fixtures/content/typography.md
# Typography Tests

He said "hello" to her.

She replied 'goodbye' quietly.

It's a beautiful day, and they don't know it won't last.

"Nested 'single quotes' inside double quotes" are tricky.

The sentence trails off … and then continues.

"The word trailed off …" she said quietly.

This has "bold *emphasis* inside quotes" for testing.

## Quotes in Headings

### "Quoted Heading"

Apostrophes: the cat's meow, the '90s, rock 'n' roll.
```

## T3: Smart quotes + ellipses combined

```console
$ flowmark --smartquotes --ellipses fixtures/content/typography.md
# Typography Tests

He said “hello” to her.

She replied ‘goodbye’ quietly.

It’s a beautiful day, and they don’t know it won’t last.

“Nested 'single quotes’ inside double quotes” are tricky.

The sentence trails off … and then continues.

“The word trailed off …” she said quietly.

This has “bold *emphasis* inside quotes” for testing.

## Quotes in Headings

### “Quoted Heading”

Apostrophes: the cat’s meow, the '90s, rock ‘n’ roll.
```

## T4: Smart quotes NOT converted in code blocks

Verify code block content preserved and only text outside code blocks gets converted.
Note: full output cannot be asserted in tryscript format due to nested code fences.
We use `tail -1` to check the final text line. This is NOT a masking pattern — Rust
and Python produce identical output for this test (verified by direct diff).

```console
$ flowmark --smartquotes fixtures/content/code-blocks.md | tail -1
Text after code blocks with “quotes” and ... ellipses.
```

## T5: Ellipses NOT converted in code blocks

Note: full output cannot be asserted due to nested code fences (same as T4).
Rust and Python produce identical output (verified by direct diff).

```console
$ flowmark --ellipses fixtures/content/code-blocks.md | tail -1
Text after code blocks with "quotes" and … ellipses.
```

## T6: Smart quotes with escapes

Backslash-escaped double quotes (`\"`) must be preserved through formatting.
The Python reference output preserves `\"` — Rust must match. When the backslash is
preserved, the escaped quote stays straight (not smart-quoted). When the backslash is
stripped (current Rust bug), the quote gets incorrectly smart-quoted.

```console
$ flowmark --smartquotes fixtures/content/escapes.md
# Escape Tests

Backslash escapes: \* not bold \* and \# not a heading.

Escaped brackets: \[not a link\] and \- not a list.

A “quoted” word with escapes: \"literal quotes\".

Regular text after escapes.
```

## T7: Apostrophes and contractions (inline)

```console
$ printf "It's a test and they don't know.\n" | flowmark --smartquotes -
It’s a test and they don’t know.
```

## T8: Typography edge cases (inline)

```console
$ printf 'He said "hello." And then... nothing.\n' | flowmark --smartquotes --ellipses -
He said “hello.” And then … nothing.
```
