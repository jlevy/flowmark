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

# Auto Mode Tests

Tests for --auto mode which enables --inplace --nobackup --semantic --cleanups
--smartquotes --ellipses.

## A1: Auto on single file with typography and semantic

```console
$ printf '# Test\n\nHe said "hello" to them. And then... nothing happened at all.\n' > auto-test.md && flowmark --auto auto-test.md && cat auto-test.md
# Test

He said “hello” to them.
And then … nothing happened at all.
```

## A2: Auto on directory formats all md files

```console
$ mkdir -p autodir && printf '# Dir File\n\nContent here.\n' > autodir/one.md && printf '# Another\n\nMore content.\n' > autodir/two.md && flowmark --auto autodir && cat autodir/one.md && echo "---" && cat autodir/two.md
# Dir File

Content here.
---
# Another

More content.
```

## A3: Auto is idempotent (running twice produces identical output)

```console
$ cp fixtures/content/comprehensive.md idem-test.md && flowmark --auto idem-test.md && cp idem-test.md first-pass.md && flowmark --auto idem-test.md && diff first-pass.md idem-test.md && echo "idempotent"
idempotent
```

## A4: Auto skips non-markdown files

```console
$ mkdir -p skipdir && printf '# MD File\n\nContent.\n' > skipdir/file.md && printf 'not markdown\n' > skipdir/code.py && printf 'text file\n' > skipdir/notes.txt && flowmark --auto skipdir && cat skipdir/code.py && echo "---" && cat skipdir/notes.txt
not markdown
---
text file
```

## A5: Auto with cleanups removes bold from headings

```console
$ printf '# Normal\n\n## **Bold Heading**\n\nParagraph.\n' > cleanup-test.md && flowmark --auto cleanup-test.md && cat cleanup-test.md
# Normal

## Bold Heading

Paragraph.
```

## A6: Auto mode overrides config semantic=false

```console
$ mkdir -p auto-cfg && printf 'semantic = false\n' > auto-cfg/flowmark.toml && printf '# Test\n\nFirst sentence here. Second sentence follows it.\n' > auto-cfg/test.md && cd auto-cfg && flowmark --auto test.md && cat test.md
# Test

First sentence here.
Second sentence follows it.
```
