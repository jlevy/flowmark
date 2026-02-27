---
sandbox: true
env:
  NO_COLOR: "1"
  LC_ALL: C
path:
  - $TRYSCRIPT_GIT_ROOT/.venv/bin
---

# Stdin Tests

Tests for stdin processing with various flags.

## S1: Basic stdin

```console
$ printf '# Title\n\nThis is a long paragraph that should be wrapped at the default width. The quick brown fox jumps over the lazy dog and keeps on running for quite a while.\n' | flowmark -
# Title

This is a long paragraph that should be wrapped at the default width. The quick brown
fox jumps over the lazy dog and keeps on running for quite a while.
```

## S2: Stdin with semantic

```console
$ printf '# Title\n\nFirst sentence here. Second sentence that is long enough to trigger wrapping when used with semantic mode enabled.\n' | flowmark --semantic -
# Title

First sentence here.
Second sentence that is long enough to trigger wrapping when used with semantic mode
enabled.
```

## S3: Stdin with smartquotes

```console
$ printf 'He said "hello" to them.\n' | flowmark --smartquotes -
[..]
```

## S4: Stdin with width

```console
$ printf '# Title\n\nThe quick brown fox jumps over the lazy dog.\n' | flowmark --width 30 -
# Title

The quick brown fox jumps over
the lazy dog.
```
