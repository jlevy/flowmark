---
sandbox: true
env:
  NO_COLOR: "1"
path:
  - $TRYSCRIPT_GIT_ROOT/.venv/bin
patterns:
  VERSION: 'v\d+\.\d+\.\S+'
before: |
  mkdir -p docs node_modules/pkg .venv/lib
  printf '# Root\n' > README.md
  printf '# Guide\n' > docs/guide.md
  printf '# API\n' > docs/api.md
  printf '# Excluded\n' > node_modules/pkg/README.md
  printf '# Also excluded\n' > .venv/lib/README.md
  printf 'not markdown\n' > code.py
---

# Flowmark CLI Golden Tests

End-to-end tests for the flowmark CLI, covering formatting, file discovery,
and configuration.

## Version

```console
$ flowmark --version
[VERSION]
```

## Stdin: default formatting

```console
$ printf '# Title\n\nThis is a long paragraph that should be wrapped at the default width. The quick brown fox jumps over the lazy dog and keeps on running for quite a while.\n' | flowmark -
# Title

This is a long paragraph that should be wrapped at the default width. The quick brown
fox jumps over the lazy dog and keeps on running for quite a while.
```

## Stdin: semantic mode

```console
$ printf '# Title\n\nFirst sentence. Second sentence that is long enough to trigger wrapping when used with semantic mode enabled.\n' | flowmark --semantic -
# Title

First sentence. Second sentence that is long enough to trigger wrapping when used with
semantic mode enabled.
```

## Stdin: custom width

```console
$ printf '# Title\n\nThe quick brown fox jumps over the lazy dog.\n' | flowmark --width 30 -
# Title

The quick brown fox jumps over
the lazy dog.
```

## File discovery: list files in a directory

```console
$ flowmark --list-files . | xargs -I{} basename {} | sort
README.md
api.md
guide.md
```

## File discovery: extend-include

```console
$ printf '# MDX\n' > page.mdx && flowmark --list-files --extend-include "*.mdx" . | xargs -I{} basename {} | sort
README.md
api.md
guide.md
page.mdx
```

## File discovery: extend-exclude

```console
$ mkdir -p drafts && printf '# WIP\n' > drafts/wip.md && flowmark --list-files --extend-exclude "drafts/" . | xargs -I{} basename {} | sort
README.md
api.md
guide.md
```

## Auto mode: formats file in place

```console
$ printf '# Test\n\nThis is a paragraph with "straight quotes" and some text... that needs formatting. Another sentence here. And yet another long one.\n' > auto-test.md && flowmark --auto auto-test.md && cat auto-test.md
# Test

This is a paragraph with “straight quotes” and some text … that needs formatting.
Another sentence here.
And yet another long one.
```

## Config file: width from TOML is respected

```console
$ printf '[formatting]\nwidth = 40\n' > .flowmark.toml && printf '# Narrow\n\nThe quick brown fox jumps over the lazy dog again and again.\n' > narrow.md && flowmark narrow.md
# Narrow

The quick brown fox jumps over the lazy
dog again and again.
```

## Flowmarkignore

```console
$ printf 'drafts/\n' > .flowmarkignore
$ flowmark --list-files . | grep -c drafts
? 1
0
```

## Gitignore integration

```console
$ mkdir -p generated && printf '# Gen\n' > generated/output.md
$ printf 'generated/\n' > .gitignore
$ flowmark --list-files . | grep -c generated
? 1
0
```

## Gitignore can be disabled

```console
$ flowmark --list-files --no-respect-gitignore . | grep generated
[..]generated/output.md
```

## Force exclude: explicit file in excluded dir

```console
$ flowmark --list-files --force-exclude node_modules/pkg/README.md | wc -l
0
```

## Error: no arguments

```console
$ flowmark 2>&1
Error: No input specified. Provide files, directories (use '.' for current directory), or '-' for stdin. Use --help for more options.
? 1
```

## Error: --auto with no file arguments

```console
$ flowmark --auto 2>&1
Error: --auto requires at least one file or directory argument (use '.' for current directory, --help for more options)
? 1
```

## Error: --list-files with no file arguments

```console
$ flowmark --list-files 2>&1
Error: --list-files requires at least one file or directory argument (use '.' for current directory, --help for more options)
? 1
```

## Error: --auto --list-files with no file arguments

```console
$ flowmark --auto --list-files 2>&1
Error: --auto requires at least one file or directory argument (use '.' for current directory, --help for more options)
? 1
```

## Stdin: explicit dash still works

```console
$ printf '# Hello\n\nWorld.\n' | flowmark -
# Hello

World.
```

## Stdin: explicit dash with --semantic

```console
$ printf '# Hello\n\nFirst sentence here. Second sentence here.\n' | flowmark --semantic -
# Hello

First sentence here.
Second sentence here.
```

## Error handling: nonexistent file

```console
$ flowmark nonexistent.md 2>&1
Error: [Errno 2] No such file or directory: 'nonexistent.md'
? 2
```
