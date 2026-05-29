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
Note: --verbose is Rust-only (not in Python), so this suite focuses on docs/skill
behavior.

## V1: Skill prints SKILL.md content

```console
$ flowmark --skill | sed -n '1,6p'
---
name: flowmark
description: Fast, consistent Markdown auto-formatter for typographic cleanup (smart quotes, ellipses), normalized formatting, and optional clean line wrapping for small, readable git diffs. Use when creating, editing, or normalizing Markdown (.md) files, cleaning up LLM-generated Markdown, or when the user mentions flowmark or formatting Markdown.
allowed-tools: Bash(flowmark:*), Bash(uvx:*), Read, Write
---
# Flowmark - Markdown Auto-Formatter
```

## V2: Docs prints documentation

```console
$ flowmark --docs | grep -Fx "# flowmark"
# flowmark
```

```console
$ flowmark --docs | grep -Fx "## Python and Rust Flowmark"
## Python and Rust Flowmark
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
$ flowmark --skill | grep -F -- "flowmark --docs" | sed 's/^> //'
**Full documentation: run `flowmark --docs` for all options and usage.**
```

## V6: Install skill project-local default writes all three surfaces

```console
$ mkdir v6 && cd v6 && flowmark --install-skill >/dev/null && test -f .agents/skills/flowmark/SKILL.md && test -f .claude/skills/flowmark/SKILL.md && test -f AGENTS.md && echo "all surfaces installed"
all surfaces installed
```

## V7: --surfaces=claude writes only the Claude mirror

```console
$ mkdir v7 && cd v7 && flowmark --install-skill --surfaces=claude >/dev/null && test -f .claude/skills/flowmark/SKILL.md && test ! -e .agents && test ! -e AGENTS.md && echo "claude-only"
claude-only
```

## V8: --surfaces=portable writes only the portable surface

```console
$ mkdir v8 && cd v8 && flowmark --install-skill --surfaces=portable >/dev/null && test -f .agents/skills/flowmark/SKILL.md && test ! -e .claude && test ! -e AGENTS.md && echo "portable-only"
portable-only
```

## V9: --surfaces=agents-md writes only the AGENTS.md block

```console
$ mkdir v9 && cd v9 && flowmark --install-skill --surfaces=agents-md >/dev/null && test -f AGENTS.md && test ! -e .agents && test ! -e .claude && echo "agents-md-only"
agents-md-only
```

## V10: --surfaces=all is an alias for the default

```console
$ mkdir v10 && cd v10 && flowmark --install-skill --surfaces=all >/dev/null && test -f .agents/skills/flowmark/SKILL.md && test -f .claude/skills/flowmark/SKILL.md && test -f AGENTS.md && echo "all surfaces installed"
all surfaces installed
```

## V11: --surfaces=portable,agents-md writes a subset

```console
$ mkdir v11 && cd v11 && flowmark --install-skill --surfaces=portable,agents-md >/dev/null && test -f .agents/skills/flowmark/SKILL.md && test -f AGENTS.md && test ! -e .claude && echo "subset"
subset
```

## V12: --surfaces with an unknown value exits non-zero

```console (exit-code=2)
$ mkdir v12 && cd v12 && flowmark --install-skill --surfaces=cursor 2>&1 1>/dev/null | grep -o "unknown surface"
unknown surface
```
