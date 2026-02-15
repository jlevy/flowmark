# Research Brief: Configuration Format and Settings System for Flowmark

**Last Updated**: 2026-02-15

**Status**: Complete

**Related**:

- [File Discovery and Globbing Plan Spec](../specs/active/plan-2026-02-15-file-discovery-and-globbing.md)
- [Auto-Formatter File Discovery Research](research-auto-formatter-file-discovery.md)
- [Ruff Configuration Docs](https://docs.astral.sh/ruff/configuration/)
- [Biome Configuration Docs](https://biomejs.dev/reference/configuration/)

* * *

## Executive Summary

Flowmark currently has **no configuration file support** — every option must be passed
via CLI arguments.
As we add file discovery (exclude/include patterns, `.gitignore` integration) and
potentially `--files-max-size`, the number of settings is growing to the point where a
configuration file is essential for practical use.

This research examines what config format to use, how to structure the config system,
and how to ensure it works well across Python, TypeScript/JavaScript, and Rust ecosystems
(since Flowmark is used on projects in all these languages and may itself be ported to
Rust).

**Key recommendations:**

1. **TOML** as the configuration format, following the Ruff model
2. Support both `flowmark.toml` (standalone) and `pyproject.toml` `[tool.flowmark]`
3. Add `files-max-size` as both a CLI flag and config setting (default: 1 MiB)
4. Systematically expose all existing CLI options as config settings
5. CLI flags always override config file values

* * *

## Research Questions

1. What format should Flowmark's configuration file use?
2. How should Ruff's configuration model (the current gold standard) inform Flowmark's
   design?
3. How does Biome's `files.maxSize` work and what should Flowmark adopt?
4. What settings should be configurable and what should the config schema look like?
5. How should CLI flags and config file settings interact?

* * *

## Format Analysis: TOML vs YAML vs JSON

### Cross-Ecosystem Format Usage

| Ecosystem | Dominant Config Format | Examples |
| --- | --- | --- |
| **Rust** | TOML (universal) | `Cargo.toml`, `rustfmt.toml`, `clippy.toml`, `.taplo.toml` |
| **Python** | TOML (modern standard) | `pyproject.toml`, `ruff.toml`, `uv.toml` |
| **JavaScript/TypeScript** | JSON / JSONC | `package.json`, `tsconfig.json`, `biome.json`, `deno.json` |

### Parsing Library Quality

| Language | TOML | YAML | JSON |
| --- | --- | --- | --- |
| **Python** | `tomllib` (stdlib 3.11+), `tomli` (backport), `tomlkit` (round-trip) | `PyYAML` (YAML 1.1 only, implicit type coercion footguns), `ruamel.yaml` (YAML 1.2, round-trip) | `json` (stdlib) |
| **Rust** | `toml` v0.9 (excellent, serde-native) | `serde_yaml` (**deprecated** March 2024, fragmented forks) | `serde_json` (excellent) |
| **JavaScript** | `smol-toml`, `js-toml` (adequate, not native) | `js-yaml`, `yaml` (good) | Native (`JSON.parse`) |

### Decision Matrix

| Criterion | TOML | YAML | JSON |
| --- | --- | --- | --- |
| Rust ecosystem fit | **Native** | Deprecated main lib | Not used for config |
| Python ecosystem fit | **Standard** (stdlib) | Good | Not used for config |
| JS/TS ecosystem fit | Marginal | Marginal | **Native** |
| Human readability | High | High (with footguns) | Low (no comments) |
| Comment support | Yes (`#`) | Yes (`#`) | No (JSONC variant only) |
| Implicit type coercion | None | **Dangerous** (Norway problem: `NO` → `false`, `3.10` → `3.1`) | None |
| Spec complexity | Simple | Very complex | Very simple |
| Rust portability | Excellent | **Risky** (deprecated libs) | Excellent |

### Why Not YAML?

YAML has two critical problems for this use case:

1. **Implicit type coercion** makes it dangerous for config files.
   In YAML 1.1 (what PyYAML implements), `NO` is parsed as `false`, `3.10` is parsed
   as `3.1`, and certain strings are silently interpreted as dates or numbers.
   Modern tools (Biome, Deno, ESLint v9) are all moving away from YAML.

2. **The Rust YAML story is fragmented and risky.**
   `serde_yaml` — the standard Rust YAML library with 200M+ downloads — was deprecated
   in March 2024 with no clear successor.
   Community forks (`serde-yaml-ng`, `serde_yml`) have quality and maintenance concerns.
   Choosing YAML now would create a dependency risk for a future Rust port.

### Why Not JSON?

1. **No comments** in standard JSON.
   JSONC helps but is non-standard and has uneven tooling.
2. **Not the convention** for Python or Rust tools.
   Users of Python projects expect `pyproject.toml`; Rust users expect `*.toml`.
3. **Verbose for config** — requires quoting all keys and no trailing commas.

### Why TOML

1. **Native in the two target ecosystems** — `tomllib` is in Python's stdlib since 3.11;
   the `toml` crate is Rust's native config format.
2. **`pyproject.toml` integration** is idiomatic for Python projects.
   Ruff, Black, Mypy, Pytest, uv all support `[tool.X]` sections.
3. **Clean Rust port path** — the `toml` crate (v0.9) is excellent and actively
   maintained.
4. **Human-readable with comments** — critical for config files that humans maintain.
5. **No implicit type coercion** — what you write is what you get.
6. **JS/TS is the weakest link, but acceptable.**
   `smol-toml` and `js-toml` are adequate.
   JS/TS developers already encounter TOML in polyglot repos (`pyproject.toml`,
   `Cargo.toml`).
   Prettier already supports `.prettierrc.toml`, establishing precedent.

* * *

## Ruff's Configuration Model

Ruff (by Astral) is the current gold standard for developer tool configuration.
Its model is particularly relevant because Ruff is written in Rust, configured in TOML,
and serves the Python ecosystem — exactly the trajectory Flowmark may follow.

### Config File Discovery

Ruff supports three equivalent config file locations:

| File | Notes |
| --- | --- |
| `pyproject.toml` | Under `[tool.ruff]`. Ignored if no such section exists. |
| `ruff.toml` | Standalone. Same schema, no `tool.ruff` prefix. |
| `.ruff.toml` | Dotfile variant. Takes precedence over `ruff.toml`. |

**Same-directory precedence**: `.ruff.toml` > `ruff.toml` > `pyproject.toml`

**Discovery algorithm**: Walk up from the file being processed.
Use the closest config file found.
No implicit merging across directories (unlike ESLint).
Explicit inheritance via the `extend` field.

### CLI vs Config Precedence

From highest to lowest:

1. Dedicated CLI flags (e.g., `--line-length=90`)
2. `--config` key-value overrides (e.g., `--config "line-length=100"`)
3. `--config` pointing to a specific file
4. Closest discovered config file
5. Inherited config files (via `extend`)
6. Built-in defaults

**CLI always wins over config.**
This is the universal convention across all formatters studied.

### Config Structure

```toml
# Top-level settings (apply to all tools)
line-length = 88
target-version = "py312"
exclude = [".venv"]
extend-exclude = ["generated/"]

# Tool-specific sections
[lint]
select = ["E4", "E7", "E9", "F"]

[format]
quote-style = "double"
```

### Key Takeaways for Flowmark

- Support both `pyproject.toml` and standalone TOML file
- Same schema in both (just different prefix)
- CLI always overrides config
- `extend-*` fields for additive overrides (don't replace defaults)
- Keep config flat where possible (Flowmark is simpler than Ruff)

* * *

## Biome's `files.maxSize`

Biome sets a maximum file size to silently skip oversized files during formatting.

- **Config key**: `files.maxSize`
- **CLI flag**: `--files-max-size=<bytes>`
- **Default**: `1048576` bytes (1 MiB)
- **Type**: integer (bytes)
- **Behavior**: Files exceeding the limit are skipped with a diagnostic message

```json
{
  "files": {
    "maxSize": 2097152
  }
}
```

### Why This Matters for Flowmark

Large Markdown files exist in practice — generated API docs, concatenated changelogs,
data files with `.md` extensions.
Formatting a 10 MB Markdown file is slow and usually unintentional.
A sensible default protects users from accidentally formatting generated content.

### Recommendation

Add `files-max-size` with a default of **1048576 bytes (1 MiB)**.
This matches Biome's default and is generous enough for any hand-written Markdown file
while protecting against generated content.

* * *

## Recommended Configuration Schema for Flowmark

### Config File Locations (Following Ruff Model)

| File | Notes |
| --- | --- |
| `pyproject.toml` | Under `[tool.flowmark]`. For Python projects. |
| `flowmark.toml` | Standalone. Same schema, no prefix. For any project. |
| `.flowmark.toml` | Dotfile variant. Takes precedence over `flowmark.toml`. |

**Same-directory precedence**: `.flowmark.toml` > `flowmark.toml` > `pyproject.toml`

**Discovery**: Walk up from current working directory until a config is found.

### Full Config Schema

```toml
# flowmark.toml (or [tool.flowmark] in pyproject.toml)

# ─── Formatting Options ───

# Line width to wrap to (0 to disable wrapping)
width = 88

# Enable semantic (sentence-based) line breaks
semantic = false

# Enable safe cleanups (e.g., unbolding section headers)
cleanups = false

# Convert straight quotes to typographic/curly quotes
smartquotes = false

# Convert ... to ellipsis character
ellipses = false

# List spacing behavior: "preserve", "loose", or "tight"
list-spacing = "preserve"

# ─── File Discovery ───

# File patterns to include (default: ["*.md"])
include = ["*.md"]

# Additional file patterns to include
extend-include = []

# Replace default exclusion patterns (overrides all defaults)
# exclude = ["custom/"]

# Additional exclusion patterns (adds to defaults)
extend-exclude = []

# Maximum file size in bytes (0 to disable)
files-max-size = 1048576

# Whether to respect .gitignore files
respect-gitignore = true

# Whether exclusions apply to explicitly-named files
force-exclude = false
```

### Mapping: Config Keys to CLI Flags

Every config setting has a corresponding CLI flag.
CLI flags always override config values.

| Config Key | CLI Flag | Type | Default |
| --- | --- | --- | --- |
| `width` | `-w` / `--width` | int | `88` |
| `semantic` | `-s` / `--semantic` | bool | `false` |
| `cleanups` | `-c` / `--cleanups` | bool | `false` |
| `smartquotes` | `--smartquotes` | bool | `false` |
| `ellipses` | `--ellipses` | bool | `false` |
| `list-spacing` | `--list-spacing` | str | `"preserve"` |
| `include` | (via `--extend-include` only) | list | `["*.md"]` |
| `extend-include` | `--extend-include` | list | `[]` |
| `exclude` | `--exclude` | list | (default list) |
| `extend-exclude` | `--extend-exclude` | list | `[]` |
| `files-max-size` | `--files-max-size` | int | `1048576` |
| `respect-gitignore` | `--no-respect-gitignore` | bool | `true` |
| `force-exclude` | `--force-exclude` | bool | `false` |

### Settings That Are CLI-Only (Not in Config)

These are operational flags that don't belong in a project config:

| CLI Flag | Reason |
| --- | --- |
| `-o` / `--output` | Per-invocation output target |
| `-i` / `--inplace` | Per-invocation mode |
| `--nobackup` | Per-invocation mode |
| `--auto` | Fixed formatting preset (see below) |
| `--list-files` | Diagnostic command |
| `--version` | Informational |
| `--skill` / `--install-skill` | Agent integration |
| `--docs` | Informational |
| `-p` / `--plaintext` | Rarely used, per-invocation mode |

### `--auto` vs Config: Settings Resolution

This is the most important semantic to get right.
`--auto` and config files serve different purposes and interact in a specific way.

**`--auto` is a fixed, complete formatting preset.**
It always means the same thing: `semantic + cleanups + smartquotes + ellipses +
inplace + nobackup`.
It does NOT read formatting settings from the config file and it does NOT change
behavior based on what's in `flowmark.toml`.
This makes `--auto` predictable and portable — `flowmark --auto .` produces the same
formatting result regardless of project config.

**Without `--auto`, the config file provides formatting settings.**
Running `flowmark .` (or `flowmark README.md`) reads formatting preferences from
the config file.
This lets projects configure their preferred formatting style once and have it apply
to all team members and CI runs.

**File discovery settings always apply**, regardless of `--auto`.
Exclude patterns, `files-max-size`, `.gitignore` integration, and include patterns
are read from the config file even when `--auto` is used.
`--auto` only overrides *formatting behavior*, not *which files to process*.

**Resolution order by invocation style:**

| Invocation | Formatting settings | File discovery settings |
| --- | --- | --- |
| `flowmark --auto .` | Fixed preset (ignores config) | Config file, then defaults |
| `flowmark .` | Config file, then built-in defaults | Config file, then defaults |
| `flowmark --semantic .` | CLI flag overrides config; rest from config/defaults | Config file, then defaults |
| `flowmark README.md` | Config file, then built-in defaults | N/A (explicit file) |
| `flowmark --auto README.md` | Fixed preset (ignores config) | N/A (explicit file) |

**Detailed precedence for `flowmark .` (no `--auto`):**

1. Explicit CLI flags (`--semantic`, `--width=80`, etc.) — highest priority
2. Config file (`flowmark.toml` / `pyproject.toml [tool.flowmark]`)
3. Built-in defaults (`width=88`, `semantic=false`, etc.) — lowest priority

**Detailed precedence for `flowmark --auto .`:**

1. `--auto` forces: `semantic=true`, `cleanups=true`, `smartquotes=true`,
   `ellipses=true`, `inplace=true`, `nobackup=true`
2. Non-formatting settings (file discovery): config file, then defaults
3. `width` is NOT set by `--auto` — uses config file value if present,
   otherwise built-in default (88)

**Why this design:**

- `--auto` is the "just format everything nicely" command.
  It should always do the same thing so users and agents can rely on it.
- Config files are for projects that want a specific, possibly different, formatting
  style (e.g., `width = 72`, `smartquotes = false` for a project that uses ASCII-only).
- Keeping `--auto` independent of config prevents surprising interactions where
  `--auto` behaves differently in different repos.
- File discovery config (excludes, max-size, etc.) always applies because that's
  about *which files exist in this project*, not *how to format them*.

**Example: a project that uses config WITHOUT `--auto`:**

```toml
# flowmark.toml
width = 72
semantic = true
cleanups = true
smartquotes = false   # ASCII-only project
ellipses = false
extend-exclude = ["vendor/"]
files-max-size = 2097152
```

```bash
# Team members / CI run:
flowmark --inplace .
# Uses: width=72, semantic=true, cleanups=true, smartquotes=false, ellipses=false
# Skips: vendor/, files > 2 MiB

# Quick one-off with full formatting:
flowmark --auto .
# Uses: width=72 (from config, --auto doesn't set width),
#   semantic=true, cleanups=true, smartquotes=true, ellipses=true (from --auto)
# Skips: vendor/, files > 2 MiB (file discovery from config)
```

### `pyproject.toml` Example

```toml
[tool.flowmark]
width = 80
semantic = true
cleanups = true
smartquotes = true
ellipses = true
extend-exclude = ["vendor/", "generated-docs/"]
files-max-size = 2097152  # 2 MiB
```

### Standalone `flowmark.toml` Example

```toml
# Same schema, no [tool.flowmark] prefix
width = 80
semantic = true
cleanups = true
smartquotes = true
ellipses = true
extend-exclude = ["vendor/", "generated-docs/"]
files-max-size = 2097152
```

* * *

## Cross-Language Compatibility Considerations

### The `pyproject.toml` Question for Non-Python Projects

`pyproject.toml` is the right location for Python projects, but a TypeScript project
won't have one.
The standalone `flowmark.toml` serves these projects.

Notable precedent: **Pyright** (written in TypeScript) reads from both
`pyrightconfig.json` and `[tool.pyright]` in `pyproject.toml`.
This dual-file approach is well-established.

### Rust Port Considerations

If Flowmark is ported to Rust:

1. **TOML parsing is native** — the `toml` crate with serde derives is the standard
   approach.
   The config struct maps directly to Rust:
   ```rust
   #[derive(Deserialize)]
   struct Config {
       width: Option<u32>,
       semantic: Option<bool>,
       // ...
   }
   ```

2. **Same config files work** — `flowmark.toml` and `pyproject.toml` `[tool.flowmark]`
   are format-identical.
   Zero migration needed for users.

3. **YAML would be problematic** — `serde_yaml` is deprecated, forks are immature.
   TOML avoids this entirely.

### Why Not Also Support JSON?

Biome, Deno, and `tsconfig.json` demonstrate that JSON/JSONC is natural for JS/TS
tools.
However, adding a second format increases maintenance burden for limited benefit:

- JS/TS users working on polyglot repos already encounter TOML
- `flowmark.toml` is a small, simple file — TOML syntax is trivial to learn
- Prettier supports `.prettierrc.toml`, showing the JS ecosystem accepts TOML for
  formatters
- If demand arises, JSON support can be added later without breaking changes

**Recommendation**: Start with TOML only.
Add JSONC support later if there's clear demand from JS/TS-only projects.

* * *

## Implementation Strategy

### Config Loading Precedence

From highest to lowest priority:

1. CLI flags
2. Closest config file (`.flowmark.toml` > `flowmark.toml` > `pyproject.toml`)
3. Built-in defaults

### Config Loading Implementation

```python
import tomllib  # Python 3.11+ (or tomli for 3.10)
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class FlowmarkConfig:
    """All Flowmark settings, loadable from config file or CLI."""

    # Formatting
    width: int = 88
    semantic: bool = False
    cleanups: bool = False
    smartquotes: bool = False
    ellipses: bool = False
    list_spacing: str = "preserve"

    # File discovery
    include: list[str] = field(default_factory=lambda: ["*.md"])
    extend_include: list[str] = field(default_factory=list)
    exclude: list[str] | None = None  # None = use defaults
    extend_exclude: list[str] = field(default_factory=list)
    files_max_size: int = 1_048_576  # 1 MiB
    respect_gitignore: bool = True
    force_exclude: bool = False


def find_config_file(start_dir: Path) -> Path | None:
    """Walk up from start_dir looking for a config file."""
    current = start_dir.resolve()
    while True:
        for name in [".flowmark.toml", "flowmark.toml", "pyproject.toml"]:
            candidate = current / name
            if candidate.is_file():
                if name == "pyproject.toml":
                    # Only use if it has [tool.flowmark]
                    with open(candidate, "rb") as f:
                        data = tomllib.load(f)
                    if "tool" in data and "flowmark" in data["tool"]:
                        return candidate
                else:
                    return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent
```

### Dependency Notes

- **Python 3.11+**: `tomllib` is in stdlib (zero dependencies)
- **Python 3.10**: Use `tomli` backport (already standard practice; Flowmark requires
  `>=3.10`)
- **Writing TOML**: Not needed — Flowmark only reads config.
  If a `--init` command is added later, use `tomli_w` or template strings.

### Phasing

This config system should be implemented **after** the file discovery module (which is
already spec'd) but can share a phase:

1. **Phase 1**: File discovery module (already planned)
2. **Phase 2**: Config file loading + `files-max-size` + systematic config for all
   options
3. **Phase 3**: Documentation and `flowmark --init` convenience command

The `FileResolverConfig` dataclass from the file discovery spec can be absorbed into
the broader `FlowmarkConfig` — one config object for the whole tool.

* * *

## Comparison: How Other Markdown Tools Handle Config

| Tool | Config Format | Config File | `max-size` | Notes |
| --- | --- | --- | --- | --- |
| **mdformat** | TOML | `.mdformat.toml` | No | Hierarchical search, minimal settings |
| **markdownlint-cli2** | JSON/JSONC/YAML | `.markdownlint-cli2.jsonc` | No | Rich cascading config |
| **Prettier** | JSON/YAML/TOML/JS | `.prettierrc` (multi-format) | No | Most permissive format support |
| **dprint** | JSON | `dprint.json` | No | Plugin-based, simple config |
| **Biome** | JSON/JSONC | `biome.json` | Yes (1 MiB default) | Only tool with max-size |

Flowmark with TOML config and `files-max-size` would be the first Markdown formatter
to have both a proper config file system and file size limits.

* * *

## Resolved Questions

1. **Should `--auto` be representable in config?**
   **No.** `--auto` is a fixed formatting preset that ignores config formatting
   settings.
   Projects that want specific formatting configure individual settings in the config
   file and run `flowmark --inplace .` (or just `flowmark .` to stdout).
   See "Settings Resolution" section above for full details.

2. **Should `files-max-size = 0` mean "no limit" or "skip all files"?**
   **0 = no limit** (disable the check).
   This matches developer intuition (0 = off/disabled).
   Biome's interpretation (0 = skip all) is technically valid but surprising.

## Open Questions

1. **Nested config files for monorepos?**
   Ruff supports hierarchical configs.
   For a Markdown formatter this is less critical — most monorepos want the same
   Markdown formatting everywhere.
   Defer to a later version.

2. **`extend` field for config inheritance?**
   Ruff supports `extend = "../base-ruff.toml"`.
   Useful for monorepos and shared configs.
   Nice to have but not essential for v1.

* * *

## References

- [Ruff Configuration](https://docs.astral.sh/ruff/configuration/)
- [Ruff Settings Reference](https://docs.astral.sh/ruff/settings/)
- [Biome Configuration](https://biomejs.dev/reference/configuration/)
- [Biome `files.maxSize`](https://biomejs.dev/reference/configuration/#filesmaxsize)
- [Python `tomllib` (PEP 680)](https://peps.python.org/pep-0680/)
- [pyproject.toml Specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [Rust `toml` Crate](https://docs.rs/toml)
- [`smol-toml` (npm)](https://www.npmjs.com/package/smol-toml)
- [`serde_yaml` Deprecation Discussion](https://users.rust-lang.org/t/serde-yaml-deprecation-alternatives/108868)
- [Prettier Configuration](https://prettier.io/docs/configuration)
- [mdformat Configuration](https://mdformat.readthedocs.io/en/stable/)
