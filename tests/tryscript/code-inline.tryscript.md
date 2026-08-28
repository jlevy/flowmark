---
sandbox: true
env:
  NO_COLOR: "1"
  LC_ALL: C
path:
  - $FLOWMARK_BIN_DIR
before: |
  cp -r $TRYSCRIPT_TEST_DIR/fixtures/. fixtures/
  cp $TRYSCRIPT_TEST_DIR/../parity_corpus/cases/preservation/code-span/topic-width-zero/expected.stdout code-inline.expected.md
---

# Source-Exact Inline Code

The topic document covers arbitrary delimiter runs, authored whitespace, literal syntax,
Markdown containers, wrapping, and malformed fallback in one readable CLI workflow.

## C1: The complete topic output matches the shared golden

```console
$ flowmark --width 0 fixtures/content/code-inline.md > code-inline.first.md && diff -u code-inline.expected.md code-inline.first.md && echo "exact inline-code output matched"
exact inline-code output matched
```

## C2: The complete topic output reaches a fixed point

```console
$ flowmark --width 0 code-inline.first.md > code-inline.second.md && diff -u code-inline.first.md code-inline.second.md && echo "inline-code output is idempotent"
inline-code output is idempotent
```
