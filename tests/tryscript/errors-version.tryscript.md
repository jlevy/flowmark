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

# Error Cases and Version

Tests for error handling and version output.

## E1: Version

```console
$ flowmark --version
[VERSION]
```

## E2: No arguments

```console
$ flowmark 2>&1
Error: No input specified. Provide files, directories (use '.' for current directory), or '-' for stdin. Use --help for more options.
? 1
```

## E3: Auto with no arguments

```console
$ flowmark --auto 2>&1
Error: --auto requires at least one file or directory argument (use '.' for current directory, --help for more options)
? 1
```

## E4: List-files with no arguments

```console
$ flowmark --list-files 2>&1
Error: --list-files requires at least one file or directory argument (use '.' for current directory, --help for more options)
? 1
```

## E5: Auto + list-files with no arguments (auto message takes priority)

```console
$ flowmark --auto --list-files 2>&1
Error: --auto requires at least one file or directory argument (use '.' for current directory, --help for more options)
? 1
```

## E6: Nonexistent file

```console
$ flowmark nonexistent.md 2>&1
Error: [Errno 2] No such file or directory: 'nonexistent.md'
? 2
```

## E7: Output with multiple files

```console
$ flowmark -o out.md fixtures/multi-file/a.md fixtures/multi-file/b.md 2>&1
Error: Cannot specify output file when processing multiple files (use --inplace instead)
? 1
```

## E8: Inplace with stdin

```console
$ printf 'hello\n' | flowmark --inplace - 2>&1
Error: Cannot use `inplace` with stdin
? 1
```

## E9: Explicit dash with --semantic

```console
$ printf '# Hello\n\nFirst sentence here. Second sentence here.\n' | flowmark --semantic -
# Hello

First sentence here.
Second sentence here.
```
