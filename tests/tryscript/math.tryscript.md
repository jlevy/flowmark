---
sandbox: true
env:
  NO_COLOR: "1"
  LC_ALL: C
path:
  - $FLOWMARK_BIN_DIR
before: |
  cp -r $TRYSCRIPT_TEST_DIR/fixtures/. fixtures/
  cp $TRYSCRIPT_TEST_DIR/../parity_corpus/cases/preservation/math-block/topic-width-zero/expected.stdout math.expected.md
---

# Math Preservation

The topic document covers the supported math dialects, Markdown containers, parser
collisions, escape parity, malformed fallbacks, and dollar-shaped prose in one readable
CLI workflow.

## M1: The complete topic output matches the shared golden

```console
$ flowmark --width 0 fixtures/content/math.md > math.first.md && diff -u math.expected.md math.first.md && echo "exact math output matched"
exact math output matched
```

## M2: The complete topic output reaches a fixed point

```console
$ flowmark --width 0 math.first.md > math.second.md && diff -u math.first.md math.second.md && echo "math output is idempotent"
math output is idempotent
```
