# Research Brief: Auto-Formatter File Discovery, Globbing, and Exclusion Patterns

**Last Updated**: 2026-02-15

**Status**: Complete

**Related**:

- [Flowmark README](../../../README.md)
- [Ruff Documentation](https://docs.astral.sh/ruff/configuration/)
- [Prettier Documentation](https://prettier.io/docs/cli)
- [Biome Documentation](https://biomejs.dev/guides/configure-biome/)
- [dprint Documentation](https://dprint.dev/config/)
- [Black Documentation](https://black.readthedocs.io/en/stable/)
- [mdformat Documentation](https://mdformat.readthedocs.io/en/stable/)

* * *

## Executive Summary

This research examines how eight modern auto-formatters handle file discovery, globbing,
and exclusion patterns: **Ruff**, **Prettier**, **Biome**, **dprint**, **Black**,
**mdformat**, **markdownlint-cli2**, **taplo**, and **shfmt**.
The goal is to identify best practices for building a file discovery system for
Flowmark (a Markdown formatter) that is fast, safe by default, and flexible enough for
any build system.

Currently, Flowmark has **zero built-in file discovery** — it relies entirely on shell
glob expansion, processing only explicitly named files.
Adding programmatic file discovery with sensible defaults and powerful overrides would
make Flowmark significantly more practical for real-world use.

The key finding is a strong industry consensus on several patterns: respect `.gitignore`
by default, hardcode exclusions for known-problematic directories (like `node_modules`),
provide an `extend-exclude` mechanism that adds to defaults without replacing them, and
always allow overrides.
The principle is: **simple should be simple; complex should be possible.**

**Research Questions**:

1. How do modern formatters discover files when given a directory path?

2. What default exclusion patterns are standard, and why?

3. How do formatters integrate with `.gitignore` and other VCS ignore files?

4. What CLI and config patterns allow flexible customization without complexity?

5. What recommendations apply to Flowmark specifically?

* * *

## Research Methodology

### Approach

We examined the official documentation, CLI help text, configuration references, and
(where available) source code of eight formatters across four language ecosystems
(Python, JavaScript/TypeScript, TOML, shell).
We focused on file discovery algorithms, default behaviors, configuration patterns, and
integration with build systems.

### Sources

- Official documentation for Ruff, Prettier, Biome, dprint, Black, mdformat,
  markdownlint-cli2, taplo, shfmt
- GitHub repositories and source code
- Rust `globset` crate documentation
- Node.js `fast-glob` / `micromatch` documentation

* * *

## Research Findings

### 1. Ruff (Python — Astral/uv Ecosystem)

**Status**: ✅ Complete

Ruff is the gold standard for modern formatter file discovery.
It is written in Rust and is extremely fast, making it a particularly relevant model.

**CLI interface**:

```bash
ruff format .                    # Format current directory (default)
ruff format src/                 # Format specific directory
ruff format foo.py bar.py        # Format specific files
echo "x=1" | ruff format -      # Format stdin
```

**Default exclusions** (the `exclude` setting):
`.bzr`, `.direnv`, `.eggs`, `.git`, `.git-rewrite`, `.hg`, `.ipynb_checkpoints`,
`.mypy_cache`, `.nox`, `.pants.d`, `.pyenv`, `.pytest_cache`, `.pytype`,
`.ruff_cache`, `.svn`, `.tox`, `.venv`, `.vscode`, `__pypackages__`, `_build`,
`buck-out`, `build`, `dist`, `node_modules`, `site-packages`, `venv`

**Key design decisions**:

- **`.gitignore` is respected by default** (`respect-gitignore = true`).
  Also reads `.ignore`, `.git/info/exclude`, and global gitignore.

- **`exclude` replaces defaults; `extend-exclude` adds to them.**
  This is a critical UX pattern — users who want to add one exclusion don't lose the
  26 default exclusions.

- **Explicitly-named files bypass exclusions** unless `force-exclude = true`.
  This is important for pre-commit hooks and editor integrations that pass explicit
  file paths.

- **Hierarchical configuration** — each file uses the closest config file
  (`.ruff.toml` > `ruff.toml` > `pyproject.toml`).
  Settings are NOT merged; closest wins.

- **Glob syntax**: Uses the Rust `globset` crate — `**` for recursive, `*` for
  single-level, `{a,b}` for alternation, `[!ab]` for negation.

- **Linter vs formatter can have separate exclusions**:
  `[tool.ruff.format].exclude` and `[tool.ruff.lint].exclude` are independent.

**Assessment**: Ruff's approach is the most comprehensive and well-designed.
The `exclude` / `extend-exclude` / `force-exclude` trio is elegant.
Automatic `.gitignore` respect with override capability is the right default.

* * *

### 2. Prettier (JavaScript/TypeScript)

**Status**: ✅ Complete

Prettier is the most widely used code formatter.
Its approach evolved significantly in v3.0.

**CLI interface**:

```bash
prettier --write .               # Format current directory
prettier --write "**/*.md"       # Glob pattern (must be quoted!)
prettier --check src/            # Check without modifying
```

**File discovery algorithm** (3-step):

1. If path is a literal file → process it directly
2. If path is a directory → recursively find supported files by extension
3. Otherwise → treat as a glob pattern (using `fast-glob`/`micromatch`)

**Default exclusions**:

- **Hardcoded**: `.git`, `.svn`, `.hg`, `.jj`, `.sl` (VCS dirs)
- **Hardcoded**: `node_modules` (overridable with `--with-node-modules`)
- **Since v3.0**: `.gitignore` is read by default

**Ignore system**:

- `.prettierignore` — uses gitignore syntax
- `.gitignore` — read by default since v3.0
- `--ignore-path` — customize which ignore files are read
  (default: `./.gitignore` and `./.prettierignore`)
- No `--no-ignore` flag exists; workaround: `--ignore-path ''`

**Key design decisions**:

- Glob quoting is critical — `prettier "**/*.md"` (not `prettier **/*.md`) to prevent
  shell expansion.

- Inline negation patterns: `prettier . "!**/*.js" --write`

- `overrides` array in config allows per-file-pattern options, but controls
  **formatting options**, not whether files are included.

**Assessment**: Prettier's approach is mature but shows some legacy complexity.
The v3.0 change to auto-read `.gitignore` was a major improvement.
The lack of `--no-ignore` is a notable gap (workaround exists).

* * *

### 3. Biome (JavaScript/TypeScript — Rust-based)

**Status**: ✅ Complete

Biome is the modern Rust-based alternative to Prettier + ESLint.

**CLI interface**:

```bash
biome format ./                  # Format all known files
biome format ./src               # Format specific directory
biome format --write ./          # Write changes
```

Biome does **not** expand globs itself — relies on shell expansion.
The team explicitly discourages CLI globs.

**Configuration** (`biome.json`):

```json
{
  "files": {
    "includes": ["src/**/*.js", "!**/*.test.js"]
  },
  "formatter": {
    "includes": ["src/**/*.js"]
  },
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true
  }
}
```

**Layered include/exclude system**:

- `files.includes` — global filter; files not matching are excluded from ALL tools
- `formatter.includes` / `linter.includes` — tool-specific refinements
- Single `!` prefix — excludes from processing but keeps indexed
- Double `!!` prefix — completely excludes from everything (recommended for `dist/`,
  `build/`)

**Default exclusions**:

- `node_modules/` — hardcoded, always ignored
- Lock files: `composer.lock`, `npm-shrinkwrap.json`, `package-lock.json`, `yarn.lock`

**`.gitignore`**: **Opt-in** — requires `vcs.useIgnoreFile: true`

**Assessment**: Biome's layered system is powerful but more complex than necessary for
most use cases.
The `!` vs `!!` distinction is unique and handles the import-graph-analysis use case.
The `.gitignore` opt-in default is surprising — most other tools default to respecting
it.

* * *

### 4. dprint (Rust-based Multi-language Formatter)

**Status**: ✅ Complete

dprint is a plugin-based formatter written in Rust.

**Configuration** (`dprint.json`):

```json
{
  "includes": ["**/*.{ts,tsx,js,jsx,json,md}"],
  "excludes": ["**/*-lock.json", "**/dist/**"],
  "plugins": [
    "https://plugins.dprint.dev/typescript-0.93.3.wasm",
    "https://plugins.dprint.dev/markdown-0.17.8.wasm"
  ]
}
```

**Key design decisions**:

- **Gitignored files are excluded by default** (requires `git` to be installed)
- `node_modules` is excluded via built-in `!**/node_modules` pattern
- `includes` is usually not needed — plugins declare their own file extensions
- `excludes` uses gitignore extended glob syntax
- Negation with `!` un-excludes files: `"excludes": ["!dist.js"]`
- No separate ignore file — all config in `dprint.json`

**CLI overrides**:

```bash
dprint fmt --includes-override "**/*.js" --excludes-override "**/data"
dprint fmt --staged              # Only git-staged files
dprint output-file-paths         # Debug: show resolved files
```

**Assessment**: dprint's approach is clean and config-driven.
The `output-file-paths` debug command is an excellent UX feature.
Relying on `.gitignore` integration for defaults keeps the config minimal.

* * *

### 5. Black (Python Formatter)

**Status**: ✅ Complete

Black is the most popular Python formatter.

**CLI interface**:

```bash
black .                          # Format current directory
black src/ tests/                # Specific directories
black --extend-exclude='/(migrations|generated)/' .
```

**Unique: uses regular expressions, not globs**:

- `--include` (default: `(\.pyi?|\.ipynb)$`)
- `--exclude` (replaces defaults — 20 directories)
- `--extend-exclude` (adds to defaults — recommended)
- `--force-exclude` (applies even to explicitly-named files)

**Default exclusions** (as regex): `.direnv`, `.eggs`, `.git`, `.hg`,
`.ipynb_checkpoints`, `.mypy_cache`, `.nox`, `.pytest_cache`, `.ruff_cache`, `.tox`,
`.svn`, `.venv`, `.vscode`, `__pypackages__`, `_build`, `buck-out`, `build`, `dist`,
`venv`

**`.gitignore`**: Automatic **unless** `--exclude` is overridden.
This is a subtle gotcha — using `--extend-exclude` preserves `.gitignore` behavior.

**Assessment**: Black pioneered the `extend-exclude` pattern that Ruff adopted.
The regex-based filtering is powerful but harder to use than globs.
The `.gitignore` behavior change when `--exclude` is set is a footgun.

* * *

### 6. mdformat (Markdown Formatter)

**Status**: ✅ Complete

mdformat is the primary Markdown-specific formatter, pure Python.

**CLI interface**:

```bash
mdformat .                       # Recursive directory
mdformat README.md CHANGELOG.md  # Specific files
mdformat -                       # Stdin
mdformat --exclude "node_modules/**" .  # Python 3.13+ only
```

**Key findings**:

- Directory recursion uses `pathlib.Path.glob("**/*.md")` — only `.md` files
- `--exclude PATTERN` exists but **requires Python 3.13+**
  (uses `Path.full_match()`)
- **No default exclusions** — `mdformat .` walks into `node_modules/`, `.git/`, etc.
- **No `.gitignore` support**
- Config via `.mdformat.toml` (hierarchical search), but `exclude` key also needs
  Python 3.13+
- Pre-commit integration sidesteps the problem — pre-commit handles file discovery

**Assessment**: mdformat's file discovery is minimal and has significant gaps.
No default exclusions is a real usability problem — running `mdformat .` in a project
with `node_modules/` is painfully slow and formats files you don't want touched.
This is a key area where Flowmark can differentiate.

* * *

### 7. markdownlint-cli2 (Markdown Linter)

**Status**: ✅ Complete

markdownlint-cli2 is the standard Markdown linter.

**CLI interface** (accepts globs directly):

```bash
markdownlint-cli2 "**/*.md"
markdownlint-cli2 "**/*.md" "#node_modules"  # '#' negates
```

**Configuration** (`.markdownlint-cli2.jsonc`):

```json
{
  "globs": ["**/*.md"],
  "ignores": ["node_modules/"],
  "gitignore": true
}
```

**Key decisions**:

- `.gitignore` integration is **opt-in** (`"gitignore": true`)
- No default exclusions — must configure `ignores`
- Settings cascade from parent to child directories
- Uses `globby` library (Node.js) for glob expansion

**Assessment**: Rich configuration with cascading config files, but no sensible
defaults out of the box.

* * *

### 8. taplo (TOML Formatter) and shfmt (Shell Formatter)

**Status**: ✅ Complete

**taplo** (Rust-based):

- Config file: `.taplo.toml` with `include` and `exclude` arrays (glob-based)
- No default exclusions, no `.gitignore` support
- Simple and explicit

**shfmt** (Go-based):

- Walks directories, detects shell files by extension and shebang
- Hardcoded exclusions: `.git`, `.svn`, `.hg`, hidden files
- No `--exclude` flag — delegates to EditorConfig `ignore = true`
- Explicitly minimalist philosophy

* * *

## Comparative Analysis

| Feature | Ruff | Prettier | Biome | dprint | Black | mdformat |
| --- | --- | --- | --- | --- | --- | --- |
| **Language** | Rust | JS | Rust | Rust | Python | Python |
| **Pattern syntax** | Glob (globset) | Glob (fast-glob) | Glob | Glob (gitignore) | Regex | Glob (pathlib) |
| **Default exclusions** | 26 dirs | VCS + node_modules | node_modules + locks | node_modules | 20 dirs | None |
| **`.gitignore` default** | ✅ On | ✅ On (v3+) | ❌ Off (opt-in) | ✅ On | ✅ On | ❌ None |
| **`extend-exclude`** | ✅ | ❌ (use .prettierignore) | Via `!` prefix | Via `excludes` | ✅ | ❌ |
| **`force-exclude`** | ✅ | ❌ | `!!` prefix | N/A | ✅ | ❌ |
| **Config file** | ruff.toml / pyproject.toml | .prettierrc | biome.json | dprint.json | pyproject.toml | .mdformat.toml |
| **Ignore file** | .gitignore | .prettierignore + .gitignore | .gitignore (opt-in) | .gitignore | .gitignore | None |
| **Debug file list** | ❌ | ❌ | ❌ | ✅ output-file-paths | ❌ | ❌ |
| **Staged-only** | ❌ | ❌ (use lint-staged) | ✅ --staged | ✅ --staged | ❌ | ❌ |

### Key Takeaways from the Comparison

1. **All mature formatters have substantial default exclusions.**
   mdformat is the outlier with zero defaults, and this is widely seen as a usability
   problem.

2. **`.gitignore` respect is the modern default.**
   Ruff, Prettier (v3+), dprint, and Black all respect `.gitignore` by default.
   Biome's opt-in approach is the exception and is less convenient.

3. **The `extend-exclude` pattern is essential.**
   Without it, users must duplicate the entire default exclusion list to add one entry.
   Ruff and Black both offer this; Prettier works around it with `.prettierignore`.

4. **`force-exclude` solves the pre-commit/editor problem.**
   When tools pass explicit file paths, exclusion patterns are normally bypassed.
   `force-exclude` provides a safety net.

5. **Glob syntax is strongly preferred over regex.**
   Only Black uses regex; all newer tools use glob patterns.
   Globs are more intuitive for file matching and align with `.gitignore` syntax.

* * *

## Best Practices

Based on this research, these are the established best practices for auto-formatter
file discovery:

1. **Respect `.gitignore` by default.**
   This is the single most important default.
   It automatically excludes `node_modules/`, `dist/`, `build/`, `.venv/`, and any
   other project-specific generated/vendored content without configuration.
   Provide a flag like `--no-respect-gitignore` to override.

2. **Hardcode a sensible set of always-excluded directories.**
   Even outside of git repos (or for files not in `.gitignore`), certain directories
   should essentially never be auto-formatted: `.git`, `.hg`, `.svn`, `node_modules`,
   `.venv`, `__pycache__`, etc.
   These should be excluded by default regardless of `.gitignore` status.

3. **Provide `exclude` AND `extend-exclude`.**
   `exclude` replaces defaults (for full control); `extend-exclude` adds to defaults
   (for the common case of adding one or two patterns).
   This distinction prevents the most common footgun.

4. **Provide `force-exclude` for tool integrations.**
   Explicitly-named files should normally bypass exclusions (principle of least
   surprise when a user names a specific file).
   But integrations (pre-commit, editors, CI) need a way to enforce exclusions even
   for explicit paths.

5. **Use glob syntax, not regex.**
   Globs are more intuitive, align with `.gitignore` syntax, and are sufficient for
   file matching. Use the `globset` crate (Rust) or `pathspec` library (Python).

6. **Support a tool-specific ignore file.**
   A `.flowmarkignore` file using gitignore syntax provides a familiar, composable
   exclusion mechanism.
   It can be used alongside `.gitignore` for formatter-specific exclusions.

7. **Provide a "dry run" or "list files" command.**
   dprint's `output-file-paths` is excellent — it shows exactly which files would be
   processed without formatting them.
   This is invaluable for debugging unexpected behavior.

8. **Support stdin with filename context.**
   `--stdin-filename` enables editor integrations that pipe content via stdin while
   still applying per-file configuration and exclusion rules.

* * *

## Recommendations for Flowmark

### Summary

Flowmark should adopt a file discovery system modeled primarily on **Ruff's approach**
(the most complete and well-designed), adapted for Markdown files.
The guiding principle: **defaults are clean and unsurprising; overrides are possible.**

### Recommended Approach

#### 1. CLI Interface

```bash
# Basic: format specific files (current behavior, preserved)
flowmark README.md docs/guide.md

# New: format all Markdown in a directory recursively
flowmark .
flowmark docs/

# New: glob patterns (tool-expanded, not shell-expanded)
flowmark "docs/**/*.md"

# Existing: stdin
flowmark -

# New: stdin with filename context
flowmark --stdin-filename docs/guide.md -
```

When given a directory, Flowmark recursively discovers all files matching the
**include** pattern (default: `*.md`).

#### 2. Default Exclusions

Flowmark should hardcode sensible default exclusions that are always applied during
directory traversal:

```
# VCS directories
.git
.hg
.svn

# Package manager / dependency directories
node_modules
.venv
venv
__pycache__
site-packages
__pypackages__
vendor
bower_components

# Build output directories
_build
build
dist
out
target

# Tool caches
.ruff_cache
.mypy_cache
.pytest_cache
.tox
.nox
.eggs

# IDE / editor directories
.vscode
.idea

# Other common exclusions
.direnv
buck-out
.pants.d
```

#### 3. `.gitignore` Respect (On by Default)

```bash
# Default: respects .gitignore
flowmark .

# Override: ignore .gitignore patterns
flowmark --no-respect-gitignore .
```

This is the single highest-value default.
In practice, it means Flowmark automatically skips everything a project has already
declared as non-source content.

#### 4. Exclude / Extend-Exclude

**Config file** (`.flowmark.toml` or `pyproject.toml` under `[tool.flowmark]`):

```toml
# Replace ALL default exclusions (rarely needed)
exclude = ["custom_dir/"]

# Add to default exclusions (common case)
extend-exclude = ["vendor/", "generated/"]
```

**CLI flags**:

```bash
# Add to exclusions
flowmark --extend-exclude "vendor/" --extend-exclude "generated/" .

# Replace exclusions entirely
flowmark --exclude "custom_dir/" .
```

#### 5. Include / Extend-Include

Default include pattern: `["*.md"]`

```toml
# Also process .markdown files
extend-include = ["*.markdown", "*.mdx"]
```

```bash
flowmark --extend-include "*.markdown" .
```

#### 6. Force-Exclude

```toml
# In config (important for pre-commit)
force-exclude = true
```

```bash
# CLI flag
flowmark --force-exclude generated/api-docs.md
```

When `force-exclude = true`, exclusion patterns apply even to files passed directly
on the command line.

#### 7. `.flowmarkignore` File

A `.flowmarkignore` file using gitignore syntax, searched in the current directory
and parent directories:

```gitignore
# .flowmarkignore
vendor/
generated-docs/
*.auto.md
```

#### 8. List Files (Dry Run)

```bash
# Show which files would be formatted, without formatting
flowmark --list-files .

# Or as a dedicated subcommand
flowmark list .
```

#### 9. Configuration Layering (Order of Precedence)

From highest to lowest priority:

1. CLI flags (`--exclude`, `--extend-exclude`, etc.)
2. `.flowmarkignore` file
3. Config file (`[tool.flowmark]` in `pyproject.toml` or `.flowmark.toml`)
4. `.gitignore` (when `respect-gitignore` is enabled)
5. Hardcoded default exclusions

#### 10. Sensible Defaults Summary

| Aspect | Default | Override |
| --- | --- | --- |
| Include pattern | `*.md` | `--extend-include`, config `extend-include` |
| Hardcoded exclusions | ~25 common dirs | `--exclude` replaces, `--extend-exclude` adds |
| `.gitignore` respect | On | `--no-respect-gitignore` |
| `.flowmarkignore` | Read if present | `--no-ignore` |
| Explicit files bypass exclusions | Yes | `--force-exclude` or `force-exclude = true` |
| Max file size | None (consider adding) | `--max-file-size` |

### Implementation Notes (Python)

For a Python implementation, the recommended libraries are:

- **`pathspec`** — Python library for gitignore-style pattern matching
  (`pip install pathspec`).
  Reads `.gitignore` files and matches paths against them.

- **`pathlib`** — Standard library for path manipulation and `glob()`.

- **`os.walk()`** or `pathlib.Path.rglob()`** — For directory traversal with
  early pruning of excluded directories (important for performance).

The key performance optimization is **early directory pruning**: when walking a
directory tree, skip excluded directories entirely rather than entering them and
checking each file.
This is what makes the difference between "instant" and "painfully slow" when
`node_modules/` with thousands of files exists.

### Alternative Approaches

1. **Shell-only approach** (current): Continue relying on shell glob expansion.
   Pros: zero implementation effort.
   Cons: no `.gitignore` respect, no default exclusions, poor UX for directory
   formatting.

2. **Minimal approach**: Only add directory recursion with `.gitignore` respect
   and hardcoded exclusions.
   No config file support.
   Suitable as a first step.

3. **Full approach** (recommended): Complete file discovery with all the features
   described above.
   Provides the best user experience and tool integration.

* * *

## Open Research Questions

1. **Should Flowmark support nested configuration files?**
   Ruff supports hierarchical configs (closest-wins), which is useful for monorepos.
   This adds complexity and may not be needed for a Markdown formatter.

2. **Should there be a maximum file size limit?**
   Biome has `--files-max-size`.
   Very large Markdown files (e.g., generated API docs) might cause performance issues.

3. **Should Flowmark support `--staged` for git-staged files?**
   dprint and Biome offer this.
   It's valuable for pre-commit workflows but adds a git dependency.

* * *

## References

- [Ruff Configuration — File Discovery](https://docs.astral.sh/ruff/configuration/)
- [Ruff Settings Reference](https://docs.astral.sh/ruff/settings/)
- [Prettier CLI Documentation](https://prettier.io/docs/cli)
- [Prettier Ignoring Code](https://prettier.io/docs/ignore)
- [Prettier 3.0 Release Notes](https://prettier.io/blog/2023/07/05/3.0.0)
- [Biome Configuration Guide](https://biomejs.dev/guides/configure-biome/)
- [Biome Configuration Reference](https://biomejs.dev/reference/configuration/)
- [dprint Configuration](https://dprint.dev/config/)
- [dprint CLI](https://dprint.dev/cli/)
- [Black — File Collection and Discovery](https://black.readthedocs.io/en/stable/usage_and_configuration/file_collection_and_discovery.html)
- [mdformat GitHub Repository](https://github.com/hukkin/mdformat)
- [markdownlint-cli2 GitHub Repository](https://github.com/DavidAnson/markdownlint-cli2)
- [Rust globset Crate](https://docs.rs/globset/latest/globset/)
- [Python pathspec Library](https://pypi.org/project/pathspec/)
- [taplo Documentation](https://taplo.tamasfe.dev/)
- [shfmt GitHub Repository](https://github.com/mvdan/sh)

* * *

## Appendices

### Appendix A: Default Exclusion Lists by Tool

**Ruff** (26 patterns):
`.bzr`, `.direnv`, `.eggs`, `.git`, `.git-rewrite`, `.hg`, `.ipynb_checkpoints`,
`.mypy_cache`, `.nox`, `.pants.d`, `.pyenv`, `.pytest_cache`, `.pytype`,
`.ruff_cache`, `.svn`, `.tox`, `.venv`, `.vscode`, `__pypackages__`, `_build`,
`buck-out`, `build`, `dist`, `node_modules`, `site-packages`, `venv`

**Black** (20 patterns):
`.direnv`, `.eggs`, `.git`, `.hg`, `.ipynb_checkpoints`, `.mypy_cache`, `.nox`,
`.pytest_cache`, `.ruff_cache`, `.tox`, `.svn`, `.venv`, `.vscode`,
`__pypackages__`, `_build`, `buck-out`, `build`, `dist`, `venv`

**Prettier** (hardcoded):
`.git`, `.svn`, `.hg`, `.jj`, `.sl`, `node_modules`

**Biome** (hardcoded):
`node_modules`, `composer.lock`, `npm-shrinkwrap.json`, `package-lock.json`,
`yarn.lock`

**shfmt** (hardcoded): `.git`, `.svn`, `.hg`, hidden files

**mdformat, markdownlint-cli2, taplo, dprint**: No hardcoded defaults
(dprint auto-excludes `node_modules` and gitignored files)

### Appendix B: Recommended Flowmark Default Exclusion List

These directories should be excluded by default during Flowmark's directory traversal.
They are ordered by category.

```python
DEFAULT_EXCLUDES = [
    # Version control
    ".git",
    ".hg",
    ".svn",
    ".bzr",
    ".jj",

    # JavaScript/Node.js
    "node_modules",
    "bower_components",
    ".next",
    ".nuxt",

    # Python
    ".venv",
    "venv",
    ".tox",
    ".nox",
    ".eggs",
    "__pycache__",
    "__pypackages__",
    "site-packages",
    ".mypy_cache",
    ".pytest_cache",
    ".pytype",
    ".ruff_cache",
    ".pyenv",

    # Build outputs
    "_build",
    "build",
    "dist",
    "out",
    "target",
    "buck-out",

    # IDE/editor
    ".vscode",
    ".idea",

    # Other
    ".direnv",
    ".pants.d",
    ".git-rewrite",
    ".ipynb_checkpoints",
]
```

This list covers the union of Ruff's and Black's defaults plus common
JavaScript/TypeScript build directories, ensuring Flowmark never accidentally
formats content in dependency or build directories.
