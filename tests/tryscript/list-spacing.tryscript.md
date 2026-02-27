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

# List Spacing Tests

Tests for list spacing modes: preserve, loose, and tight.

## LS1: Preserve tight list (stays tight)

```console
$ flowmark --list-spacing preserve fixtures/content/lists-tight.md
# Tight Lists

A tight unordered list:

- First item
- Second item
- Third item

A tight list with longer content:

- This item has more text that might wrap
- Another item with some content
- Yet another item here
```

## LS2: Preserve loose list (stays loose)

```console
$ flowmark --list-spacing preserve fixtures/content/lists-loose.md
# Loose Lists

A loose unordered list:

- First item

- Second item

- Third item

A loose list with longer content:

- This item has more text that might wrap

- Another item with some content

- Yet another item here
```

## LS3: Tight list made loose

```console
$ flowmark --list-spacing loose fixtures/content/lists-tight.md
# Tight Lists

A tight unordered list:

- First item

- Second item

- Third item

A tight list with longer content:

- This item has more text that might wrap

- Another item with some content

- Yet another item here
```

## LS4: Loose list made tight

```console
$ flowmark --list-spacing tight fixtures/content/lists-loose.md
# Loose Lists

A loose unordered list:

- First item
- Second item
- Third item

A loose list with longer content:

- This item has more text that might wrap
- Another item with some content
- Yet another item here
```

## LS5: Nested lists with loose spacing

```console
$ flowmark --list-spacing loose fixtures/content/lists-nested.md
# Nested Lists

A nested list:

- First level item one

  - Second level item one

    - Third level item one

    - Third level item two

  - Second level item two

- First level item two

  - Another second level item

- First level item three
```

## LS6: Ordered lists with tight spacing

```console
$ flowmark --list-spacing tight fixtures/content/lists-ordered.md
# Ordered Lists

An ordered list:

1. First item
2. Second item
3. Third item

A mixed ordered list:

1. First item
2. Second item
3. Third item
```
