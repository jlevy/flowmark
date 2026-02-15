# Plan Spec: Flowmark Agent Skill and Modern CLI Enhancements

## Purpose

This is a technical design doc for converting Flowmark into a self-installable agent skill
for Claude Code and other coding agents (Codex, Cursor), following the pattern established
in repren v2.0.0. This will make Flowmark easily installable and self-documenting for
agent environments.

## Background

**Reference Project:** The [`jlevy/repren`](https://github.com/jlevy/repren) repository
(cloned to `attic/repren/`) has recently been updated to v2.0.0 with comprehensive agent
skill support. Key commits:

- `33ce345`: Renamed `--install-dir` to `--agent-base` for consistent agent config
  directory handling
- `b32563b`: Added markdown-to-ANSI renderer for enhanced CLI help text
- `af8959c`: v2.0.0 release with full agent skill support

**Repren Agent Skill Components:**

1. **SKILL.md** (`repren/skills/SKILL.md`): Claude Code skill definition with metadata
   header, usage instructions, and examples
2. **claude_skill.py** (`repren/claude_skill.py`): Module for skill installation and
   content retrieval
3. **CLI flags**: `--skill` (print skill content), `--install-skill` (install to agent
   config), `--agent-base` (specify config directory)
4. **markdown_renderer.py**: Optional ANSI renderer for colored CLI help output
5. **AGENTS.md** / **CLAUDE.md**: Top-level files directing agents to docs

**Current Flowmark State:**

Flowmark is a Markdown auto-formatter with:
- CLI: `flowmark` with various formatting options
- Library API: `reformat_text()`, `reformat_file()`, `fill_markdown()`
- Package structure: `src/flowmark/` with `cli.py`, `reformat_api.py`, etc.
- Modern Python setup: uv, pyproject.toml, basedpyright

## Summary of Task

Convert Flowmark into a self-installable agent skill following the repren pattern:

### Phase 1: Agent Skill Infrastructure

1. Create `src/flowmark/skills/SKILL.md` with Claude Code skill definition
2. Create `src/flowmark/skill.py` for skill installation and retrieval
3. Add CLI flags: `--skill`, `--install-skill`, `--agent-base`
4. Add `--docs` flag for full documentation output
5. Update README with "Agent Use" section

### Phase 2: Agent Configuration Files

1. Create `AGENTS.md` pointing to development docs (Speculate pattern)
2. Create `CLAUDE.md` as symlink to `AGENTS.md`
3. Update `.cursor/rules/` symlinks if needed

### Phase 3: Modern Python CLI Enhancements (from repren)

1. Add `src/flowmark/markdown_renderer.py` for ANSI-colored help output
2. Integrate renderer with `--docs` and `--help` output
3. Add `--format=json` option for machine-parseable output (optional)

### Phase 4: Documentation and Polish

1. Update README with agent installation instructions
2. Create `docs/flowmark-docs.md` for embedded documentation
3. Update Makefile with `format` and `gendocs` targets
4. Add golden tests for skill installation

## Backward Compatibility

**Code types, methods, and function signatures**: NO BREAKING CHANGES - new functionality
is purely additive

**CLI behavior**: NO BREAKING CHANGES - new flags are optional additions

**Library APIs**: NO BREAKING CHANGES - new parameters have sensible defaults

**File formats**: NOT APPLICABLE - no file format changes

## Stage 1: Planning Stage

### Minimum Viable Feature (Phase 1 only)

Core agent skill support:
- `--skill` flag to print SKILL.md content
- `--install-skill` flag to install skill for Claude Code
- `--agent-base` to specify agent config directory (default: `~/.claude`)
- SKILL.md with proper metadata and usage instructions
- README update with agent installation section

### Extended Feature (Phases 2-4)

Full parity with repren:
- AGENTS.md and CLAUDE.md files
- Markdown-to-ANSI renderer for colored help
- `--docs` flag for full documentation
- `--format=json` for machine output
- Comprehensive test coverage

### Not In Scope

- MCP (Model Context Protocol) server support
- IDE-specific extensions beyond config files
- Multi-language documentation

### Acceptance Criteria

1. `uvx flowmark@latest --skill` outputs valid SKILL.md content
2. `uvx flowmark@latest --install-skill` installs to `~/.claude/skills/flowmark/`
3. `uvx flowmark@latest --install-skill --agent-base=./.claude` installs to project
4. `uvx flowmark@latest --docs` outputs full usage documentation
5. Claude Code can auto-discover and use the skill after installation
6. `make lint` and `make test` pass
7. Golden tests verify skill installation behavior

## Stage 2: Architecture Stage

### Repren Architecture Analysis

**Key Files in repren:**

| File | Purpose | Map to Flowmark |
|------|---------|-----------------|
| `repren/skills/SKILL.md` | Skill definition | `src/flowmark/skills/SKILL.md` |
| `repren/claude_skill.py` | Install/retrieve skill | `src/flowmark/skill.py` |
| `repren/markdown_renderer.py` | ANSI help rendering | `src/flowmark/markdown_renderer.py` |
| `repren/repren.py` (lines 1330-1410) | CLI skill flags | `src/flowmark/cli.py` |
| `AGENTS.md` | Agent entry point | `AGENTS.md` |
| `CLAUDE.md` | Symlink to AGENTS.md | `CLAUDE.md` |
| `docs/repren-docs.md` | Embedded docs | `docs/flowmark-docs.md` |

**Skill Installation Flow (from repren):**

```
CLI: flowmark --install-skill [--agent-base=DIR]
         │
         ▼
    cli.py: handle_skill_install()
         │
         ▼
    skill.py: install_skill(agent_base)
         │
         ├─► get_skill_content() via importlib.resources
         │
         ├─► mkdir -p {agent_base}/skills/flowmark/
         │
         └─► write SKILL.md to directory
```

**SKILL.md Structure (from repren):**

```yaml
---
name: flowmark
description: Auto-format Markdown with semantic line breaks, smart quotes...
allowed-tools: Bash(flowmark:*), Bash(uvx flowmark@latest:*), Read, Write
---
# Flowmark - Markdown Auto-Formatter
...usage instructions...
```

### Proposed Flowmark Architecture

**New Files:**

1. `src/flowmark/skills/SKILL.md` - Skill definition
2. `src/flowmark/skill.py` - Skill installation module
3. `src/flowmark/markdown_renderer.py` - ANSI help renderer (optional)
4. `docs/flowmark-docs.md` - Full documentation for `--docs`
5. `AGENTS.md` - Agent entry point
6. `CLAUDE.md` - Symlink to AGENTS.md

**Modified Files:**

1. `src/flowmark/cli.py` - Add skill-related CLI flags
2. `pyproject.toml` - Add package data for skills/
3. `Makefile` - Add format and gendocs targets
4. `README.md` - Add Agent Use section

### Skill.py Module Design

```python
"""
Claude Code skill installation for flowmark.
"""

from pathlib import Path
import sys

def get_skill_content() -> str:
    """Read SKILL.md from package data."""
    from importlib.resources import files
    skill_file = files("flowmark").joinpath("skills/SKILL.md")
    return skill_file.read_text(encoding="utf-8")

def install_skill(agent_base: str | None = None) -> None:
    """Install flowmark skill for Claude Code.

    Args:
        agent_base: Agent config directory (default: ~/.claude)
    """
    if agent_base is None:
        base_dir = Path.home() / ".claude"
    else:
        base_dir = Path(agent_base).resolve()

    skill_dir = base_dir / "skills" / "flowmark"
    skill_dir.mkdir(parents=True, exist_ok=True)

    skill_content = get_skill_content()
    (skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")

    print(f"✓ Flowmark skill installed to {skill_dir}")
```

### CLI Changes

Add to `cli.py`:

```python
# Skill-related arguments
parser.add_argument(
    "--install-skill",
    help="install Claude Code skill for flowmark",
    dest="install_skill",
    action="store_true",
)
parser.add_argument(
    "--agent-base",
    help="agent config directory for skills (default: ~/.claude)",
    dest="agent_base",
)
parser.add_argument(
    "--skill",
    help="print skill instructions (SKILL.md content)",
    dest="skill_instructions",
    action="store_true",
)
parser.add_argument(
    "--docs",
    help="print full documentation",
    dest="docs",
    action="store_true",
)

# Early exit handlers (before main processing)
if args.install_skill:
    from .skill import install_skill
    install_skill(agent_base=args.agent_base)
    sys.exit(0)

if args.skill_instructions:
    from .skill import get_skill_content
    print(get_skill_content())
    sys.exit(0)

if args.docs:
    from .skill import get_docs_content
    print(get_docs_content())
    sys.exit(0)
```

## Stage 3: Refine Architecture

### Reusable Components from Flowmark

**Existing infrastructure to leverage:**

1. `cli.py` argument parsing structure - extend, don't replace
2. `pyproject.toml` package data pattern - already supports hatch
3. `docs/` directory structure - add flowmark-docs.md
4. Test infrastructure in `tests/` - add skill tests

### Reusable Components from Repren

**Copy and adapt:**

1. `claude_skill.py` → `skill.py` (minimal changes needed)
2. `markdown_renderer.py` → copy as-is (zero dependencies)
3. `SKILL.md` structure → adapt for flowmark content

### Simplifications

1. Skip `--format=json` in Phase 1 (flowmark output is already text)
2. Use existing docs structure instead of generating from docstring
3. Leverage AGENTS.md pointing to existing docs/development.md

## Stage 4: Implementation Phases

### Phase 1: Core Skill Infrastructure

- [ ] Create `src/flowmark/skills/` directory with `__init__.py`
- [ ] Create `src/flowmark/skills/SKILL.md` with proper metadata and content
- [ ] Create `src/flowmark/skill.py` with `get_skill_content()` and `install_skill()`
- [ ] Add `--skill` and `--install-skill` flags to `cli.py`
- [ ] Add `--agent-base` flag to `cli.py`
- [ ] Update `pyproject.toml` to include skills/ in package data
- [ ] Add tests for skill installation

### Phase 2: Agent Configuration Files

- [ ] Create `AGENTS.md` pointing to docs/development.md
- [ ] Create `CLAUDE.md` as symlink to `AGENTS.md`
- [ ] Verify `.cursor/rules/` symlinks are correct

### Phase 3: Modern CLI Enhancements

- [ ] Add `--docs` flag for full documentation output
- [ ] Create `docs/flowmark-docs.md` with embedded documentation
- [ ] Optionally add `src/flowmark/markdown_renderer.py` for colored help
- [ ] Add `get_docs_content()` to skill.py

### Phase 4: Documentation and Testing

- [ ] Update README.md with "Agent Use" section
- [ ] Update Makefile with format target
- [ ] Add golden tests for `--skill` and `--install-skill`
- [ ] Ensure `make lint` and `make test` pass
- [ ] Manual test: install skill and verify Claude Code discovery

## Stage 5: Validation Stage

### Test Strategy

1. **Unit Tests**: Test skill content loading and installation paths
2. **Integration Tests**: Test CLI flags end-to-end
3. **Golden Tests**: Capture expected `--skill` and `--docs` output
4. **Manual Tests**: Verify Claude Code skill discovery

### Test Cases

```python
def test_get_skill_content():
    """SKILL.md can be loaded from package data."""
    from flowmark.skill import get_skill_content
    content = get_skill_content()
    assert "name: flowmark" in content
    assert "allowed-tools:" in content

def test_install_skill_default(tmp_path, monkeypatch):
    """Skill installs to ~/.claude by default."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    from flowmark.skill import install_skill
    install_skill()
    assert (tmp_path / ".claude/skills/flowmark/SKILL.md").exists()

def test_install_skill_custom_base(tmp_path):
    """Skill installs to custom agent base."""
    from flowmark.skill import install_skill
    install_skill(agent_base=str(tmp_path / ".claude"))
    assert (tmp_path / ".claude/skills/flowmark/SKILL.md").exists()
```

### Success Criteria

- [ ] `uvx flowmark@latest --skill` outputs valid SKILL.md
- [ ] `uvx flowmark@latest --install-skill` installs correctly
- [ ] `uvx flowmark@latest --help` shows new options
- [ ] All existing tests pass
- [ ] New skill tests pass
- [ ] `make lint` passes
- [ ] `make test` passes
- [ ] Claude Code discovers installed skill

## Appendix: SKILL.md Content Draft

```markdown
---
name: flowmark
description: Auto-format Markdown with semantic line breaks, smart quotes, and diff-friendly output. Use for formatting Markdown files, normalizing LLM outputs, or when user mentions flowmark, markdown formatting, or semantic line breaks.
allowed-tools: Bash(flowmark:*), Bash(uvx flowmark@latest:*), Read, Write
---
# Flowmark - Markdown Auto-Formatter

> **Full documentation: Run `uvx flowmark@latest --docs` for all options and usage.**

Auto-format Markdown with semantic line breaks for clean git diffs and consistent output.

## Quick Start

**Format a file in place with all auto-formatting:**
```bash
uvx flowmark@latest --auto README.md
```

**Preview formatted output to stdout:**
```bash
uvx flowmark@latest README.md
```

## When to Use Flowmark

**Use flowmark for:**
- Auto-formatting Markdown on save or in pipelines
- Normalizing LLM-generated Markdown output
- Preparing documents for git with semantic line breaks
- Converting straight quotes to typographic quotes
- Consistent Markdown styling across a project

**Don't use flowmark for:**
- Syntax highlighting or rendering (use a Markdown viewer)
- Converting between formats (use pandoc)
- Linting without auto-fix (use markdownlint)

## Key Options

| Flag | Purpose |
|------|---------|
| `--auto` | Format in-place with all improvements (semantic, smartquotes, ellipses) |
| `--inplace`, `-i` | Edit file in place |
| `--semantic`, `-s` | Use semantic (sentence-based) line breaks |
| `--smartquotes` | Convert straight to curly quotes |
| `--width WIDTH` | Line width (default: 88, use 0 to disable wrapping) |
| `--plaintext`, `-p` | Process as plain text instead of Markdown |

## Common Workflows

### Format for Git

```bash
uvx flowmark@latest --auto *.md
git diff  # Review clean, semantic diffs
```

### Format LLM Output

```bash
echo "$llm_output" | uvx flowmark@latest --semantic
```

### Batch Format

```bash
find . -name "*.md" -exec uvx flowmark@latest --auto {} \;
```
```

## Appendix: Files to Create/Modify Summary

**Create:**
- `src/flowmark/skills/__init__.py`
- `src/flowmark/skills/SKILL.md`
- `src/flowmark/skill.py`
- `src/flowmark/markdown_renderer.py` (optional, Phase 3)
- `docs/flowmark-docs.md`
- `AGENTS.md`
- `CLAUDE.md` (symlink)
- `tests/test_skill.py`

**Modify:**
- `src/flowmark/cli.py` - add skill flags
- `pyproject.toml` - add package data
- `Makefile` - add format target
- `README.md` - add Agent Use section
