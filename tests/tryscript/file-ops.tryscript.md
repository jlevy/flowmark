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

# File Operations Tests

Tests for file input/output modes: stdout, inplace, backup, output flag, and multi-file.

## FO1: File to stdout

```console
$ flowmark fixtures/content/simple.md
# Simple Document

This is a basic paragraph with some text.

Another paragraph here.
```

## FO2: Inplace with backup

Use content that needs reformatting so the file is actually written (and backup created).

```console
$ printf '# Test\nsome   text   here\n' > test-backup.md && flowmark --inplace test-backup.md && cat test-backup.md && test -f test-backup.md.orig && echo "backup exists"
# Test

some text here
backup exists
```

## FO3: Inplace without backup

```console
$ cp fixtures/content/simple.md test-nobackup.md && flowmark --inplace --nobackup test-nobackup.md && cat test-nobackup.md && test ! -f test-nobackup.md.orig && echo "no backup file"
# Simple Document

This is a basic paragraph with some text.

Another paragraph here.
no backup file
```

## FO4: Output to file

```console
$ printf '# Out\n\nSome output text.\n' | flowmark -o output.md - && cat output.md
# Out

Some output text.
```

## FO4b: Output to file with direct file input currently errors

```console
$ flowmark -o output.md fixtures/content/simple.md 2>&1
Error: Cannot specify output file when processing multiple files (use --inplace instead)
? 1
```

## FO5: Output to stdout (explicit dash)

```console
$ flowmark -o - fixtures/content/simple.md
# Simple Document

This is a basic paragraph with some text.

Another paragraph here.
```

## FO6: Multiple files to stdout

```console
$ flowmark fixtures/multi-file/a.md fixtures/multi-file/b.md
# File A

Content of file A.
# File B

Content of file B.
```

## FO7: Multiple files inplace

```console
$ cp fixtures/multi-file/a.md test-a.md && cp fixtures/multi-file/b.md test-b.md && flowmark --inplace --nobackup test-a.md test-b.md && cat test-a.md && echo "---" && cat test-b.md
# File A

Content of file A.
---
# File B

Content of file B.
```

## FO8: Auto mode on single file

```console
$ cp fixtures/content/simple.md test-auto.md && flowmark --auto test-auto.md && cat test-auto.md
# Simple Document

This is a basic paragraph with some text.

Another paragraph here.
```
