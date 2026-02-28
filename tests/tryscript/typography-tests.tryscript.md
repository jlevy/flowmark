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

Verify full output so code fences and code content are preserved while text outside code
blocks is transformed.

````console
$ flowmark --smartquotes fixtures/content/code-blocks.md
# Code Blocks

A backtick fenced code block:

```python
def hello():
    print("Hello, world!")
    x = 'single quotes'
    y = "double quotes"
    z = "it's a test..."
```

A tilde fenced code block:

~~~javascript
function greet() {
    console.log("Hello...");
    const msg = 'Don\'t worry';
}
~~~

Text after code blocks with “quotes” and ... ellipses.
````

## T5: Ellipses NOT converted in code blocks

Verify full output so code fences and code content are preserved while text outside code
blocks is transformed.

````console
$ flowmark --ellipses fixtures/content/code-blocks.md
# Code Blocks

A backtick fenced code block:

```python
def hello():
    print("Hello, world!")
    x = 'single quotes'
    y = "double quotes"
    z = "it's a test..."
```

A tilde fenced code block:

~~~javascript
function greet() {
    console.log("Hello...");
    const msg = 'Don\'t worry';
}
~~~

Text after code blocks with "quotes" and … ellipses.
````

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
