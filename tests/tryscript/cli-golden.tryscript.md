---
sandbox: true
env:
  NO_COLOR: "1"
  LC_ALL: C
path:
  - $TRYSCRIPT_GIT_ROOT/.venv/bin
before: |
  mkdir -p project/docs project/node_modules/pkg project/.venv/lib project/drafts
  printf '# Root\n' > project/README.md
  printf '# Guide\n' > project/docs/guide.md
  printf '# API\n' > project/docs/api.md
  printf '# Excluded\n' > project/node_modules/pkg/README.md
  printf '# Also excluded\n' > project/.venv/lib/README.md
  printf 'not markdown\n' > project/code.py
---

# Flowmark CLI Golden Tests

End-to-end tests for the Flowmark CLI, covering formatting, file discovery,
error handling, and agent skills.

## Version

```console
$ flowmark --version
[VERSION]
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

## Error: nonexistent file

```console
$ flowmark nonexistent.md 2>&1
Error: [Errno 2] No such file or directory: 'nonexistent.md'
? 2
```

## File discovery: list files in a directory

```console
$ flowmark --list-files project | xargs -I{} basename {} | sort
README.md
api.md
guide.md
```

## File discovery: skips excluded dirs

```console
$ flowmark --list-files project | grep -c node_modules
? 1
0
```

## File discovery: extend-include

```console
$ printf '# MDX\n' > project/page.mdx && flowmark --list-files --extend-include "*.mdx" project | xargs -I{} basename {} | sort
README.md
api.md
guide.md
page.mdx
```

## File discovery: extend-exclude

```console
$ printf '# WIP\n' > project/drafts/wip.md && flowmark --list-files --extend-exclude "drafts/" project | xargs -I{} basename {} | sort
README.md
api.md
guide.md
```

## File discovery: no-respect-gitignore

```console
$ mkdir -p project/generated && printf '# Gen\n' > project/generated/output.md && printf 'generated/\n' > project/.gitignore && flowmark --list-files --no-respect-gitignore project | grep generated | xargs -I{} basename {}
output.md
```

## File discovery: force-exclude

```console
$ flowmark --list-files --force-exclude project/node_modules/pkg/README.md | wc -l | tr -d ' '
0
```

## File discovery: files-max-size

```console
$ dd if=/dev/zero of=project/big.md bs=1024 count=2048 2>/dev/null && flowmark --list-files --files-max-size 100 project | grep -c big
? 1
0
```

## Flowmarkignore

```console
$ printf 'drafts/\n' > project/.flowmarkignore && flowmark --list-files project | grep -c drafts
? 1
0
```

## Skill: print SKILL.md content

```console
$ flowmark --skill | head -3
---
name: flowmark
description: Auto-format Markdown with semantic line breaks, smart quotes, and diff-friendly output. Use for formatting Markdown files, normalizing LLM outputs, or when user mentions flowmark, markdown formatting, or semantic line breaks.
```

## Docs: print documentation

```console
$ flowmark --docs | grep "^# flowmark$" | head -1
# flowmark
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

## Stdin: width zero (no wrapping)

```console
$ printf '# Title\n\nThe quick brown fox jumps over the lazy dog and keeps running for a very long time without any line breaks at all.\n' | flowmark --width 0 -
# Title

The quick brown fox jumps over the lazy dog and keeps running for a very long time without any line breaks at all.
```

## Plaintext mode

```console
$ printf 'plain text\n\nsome long text that goes on and on and on and on until it absolutely must wrap at the default width.\n' | flowmark --plaintext - && echo ""
plain text

some long text that goes on and on and on and on until it absolutely must wrap at the
default width.
```

## Typography: smart quotes and ellipses

```console
$ printf 'He said "hello." And then... nothing.\n' | flowmark --smartquotes --ellipses -
He said “hello.” And then … nothing.
```

## List spacing: loose

```console
$ printf 'A list:\n\n- item 1\n- item 2\n- item 3\n' | flowmark --list-spacing loose -
A list:

- item 1

- item 2

- item 3
```

## Basic file to stdout

```console
$ printf '# Hello\n\nWorld.\n' > basic.md && flowmark basic.md
# Hello

World.
```

## Inplace with backup

```console
$ printf '# Backup\nsome   text   here\n' > backup.md && flowmark --inplace backup.md && cat backup.md && test -f backup.md.orig && echo "backup exists"
# Backup

some text here
backup exists
```

## Inplace without backup

```console
$ printf '# No Backup\n' > nobackup.md && flowmark --inplace --nobackup nobackup.md && cat nobackup.md && test ! -f nobackup.bak && echo "no backup file"
# No Backup

no backup file
```

## Auto mode: single file

```console
$ printf '# Auto\n\nSome text.\n' > autofile.md && flowmark --auto autofile.md && cat autofile.md
# Auto

Some text.
```

## Auto mode: directory

```console
$ mkdir -p autodir && printf '# Dir\n\nContent.\n' > autodir/test.md && flowmark --auto autodir && cat autodir/test.md
# Dir

Content.
```

## Config file: width from TOML

```console
$ mkdir -p cfgtest && printf 'width = 40\n' > cfgtest/flowmark.toml && printf '# Narrow\n\nThe quick brown fox jumps over the lazy dog again and again.\n' > cfgtest/narrow.md && cd cfgtest && flowmark narrow.md
# Narrow

The quick brown fox jumps over the lazy
dog again and again.
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
