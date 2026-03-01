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

# Config Interaction Tests

Tests for TOML config file loading, precedence, pyproject.toml, kebab-case keys,
nested sections, auto-mode locking, and CLI overrides.

## C1: .flowmark.toml takes precedence over flowmark.toml

The dot-flowmark/ directory has `.flowmark.toml` with width=50 and `flowmark.toml`
with width=60. The `.flowmark.toml` should win.

```console
$ cd fixtures/config-tests/dot-flowmark && flowmark test.md
# Config Test

This is a paragraph that needs to be long enough
to show different wrapping at different widths
clearly.
```

## C2: flowmark.toml with width and semantic

```console
$ cd fixtures/config-tests/flowmark-toml && flowmark test.md
# Config Test

This is a sentence. This is another sentence that follows.

A long paragraph that should wrap at width sixty because the
config file sets that width value for testing.
```

## C3: pyproject.toml with [tool.flowmark] section

```console
$ cd fixtures/config-tests/pyproject && flowmark test.md
# Pyproject Test

This is a paragraph that needs to be long enough to show wrapping at
width seventy which is the value set in pyproject.toml.
```

## C4: pyproject.toml without [tool.flowmark] uses defaults

```console
$ cd fixtures/config-tests/pyproject-no-section && flowmark test.md
# No Section Test

This is a paragraph that will use default width since pyproject.toml has no flowmark
section configured for this test case.
```

## C5: Kebab-case config keys (list-spacing)

```console
$ cd fixtures/config-tests/kebab-case && flowmark test.md
# Kebab Case Config

A list to test:

- Item one

- Item two

- Item three
```

## C6: Nested [formatting] and [file-discovery] sections

```console
$ cd fixtures/config-tests/sections && flowmark test.md
# Sections Config Test

This is the first sentence of the paragraph.
This is the second sentence that follows it closely.

A paragraph long enough to show wrapping at the configured
width of sixty characters for testing.
```

## C7: CLI flags override config (--width 80 beats config width=50)

```console
$ cd fixtures/config-tests/cli-overrides-config && flowmark --width 80 test.md
# CLI Override Test

This is a paragraph long enough to show different wrapping when CLI width
overrides the config width value.
```

## C8: Auto mode overrides config semantic=false

```console
$ cd fixtures/config-tests/auto-lock && flowmark --auto test.md && cat test.md
# Auto Lock Test

First sentence here.
Second sentence follows it.

A paragraph to test whether auto mode overrides the config semantic=false setting.
```

## C9: Config from TOML applies to file formatting

```console
$ mkdir -p cfg-width && printf 'width = 40\n' > cfg-width/flowmark.toml && printf '# Narrow\n\nThe quick brown fox jumps over the lazy dog again and again.\n' > cfg-width/narrow.md && cd cfg-width && flowmark narrow.md
# Narrow

The quick brown fox jumps over the lazy
dog again and again.
```
