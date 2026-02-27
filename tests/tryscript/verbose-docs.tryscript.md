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

# Verbose, Docs, and Skill Tests

Tests for --skill, --install-skill, and --docs output.
Note: --verbose is Rust-only (not in Python), so verbose tests are kept minimal
with [..] patterns.

## V1: Skill prints SKILL.md content

```console
$ flowmark --skill | head -3
---
name: flowmark
description: Auto-format Markdown with semantic line breaks, smart quotes, and diff-friendly output. Use for formatting Markdown files, normalizing LLM outputs, or when user mentions flowmark, markdown formatting, or semantic line breaks.
```

## V2: Docs prints documentation

```console
$ flowmark --docs | head -1
[..]
```

## V3: Install skill creates skill file

```console
$ flowmark --install-skill --agent-base tmpagent >/dev/null && test -f tmpagent/skills/flowmark/SKILL.md && echo "skill installed"
skill installed
```

## V4: Install skill creates nested directories

```console
$ flowmark --install-skill --agent-base deep/nested/path >/dev/null && test -f deep/nested/path/skills/flowmark/SKILL.md && echo "nested dirs created"
nested dirs created
```

## V5: Skill output contains required frontmatter

```console
$ flowmark --skill | grep "^name:"
name: flowmark
```
