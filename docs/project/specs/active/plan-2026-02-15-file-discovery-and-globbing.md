# Plan Spec: File Discovery, Globbing, and Ignore-Aware File Resolution

## Purpose

This is a technical design doc for adding programmatic file discovery, gitignore-aware
globbing, and configurable exclusion patterns to Flowmark.
The implementation will live in a self-contained module designed for future extraction
as a standalone PyPI library.

## Background

Flowmark currently has **zero built-in file discovery**.
The CLI accepts explicit file paths (expanded by the shell), and there is no directory
recursion, no glob expansion, no `.gitignore` integration, and no default exclusion
patterns.
This means `flowmark .` doesn't work, and users must rely on shell globs like
`flowmark docs/*.md`, which don't recurse, don't respect `.gitignore`, and will
happily try to format files inside `node_modules/`.

Research into 8 modern auto-formatters (Ruff, Prettier, Biome, dprint, Black, mdformat,
markdownlint-cli2, taplo) reveals strong consensus on how file discovery should work.
See [research-auto-formatter-file-discovery.md](../research/research-auto-formatter-file-discovery.md)
for the full analysis.

**Key finding**: mdformat (the closest comparable Markdown tool) has no default
exclusions and no `.gitignore` support, which is widely seen as its biggest usability
problem.
This is a clear opportunity for Flowmark to differentiate.

## Summary of Task

Build a **self-contained, reusable file resolution module** (`file_resolver` or similar)
that:

1. Recursively discovers files matching configurable include patterns
2. Respects `.gitignore` (and `.ignore`) by default
3. Applies hardcoded default exclusions for known-problematic directories
4. Supports `exclude` / `extend-exclude` / `force-exclude` patterns
5. Supports a tool-specific ignore file (`.flowmarkignore`)
6. Exposes a clean Python API that could be published as an independent library
7. Integrates with Flowmark's CLI via a small set of new flags

The module should be designed so that extracting it to a separate repository and
publishing it on PyPI requires **minimal changes** — primarily removing the Flowmark
default values and making them configurable.

## Backward Compatibility

**BACKWARD COMPATIBILITY REQUIREMENTS:**

- **Code types, methods, and function signatures**: KEEP DEPRECATED — the existing
  `reformat_files(files=["file1.md", "file2.md"])` interface continues to work
  unchanged.
  The new file resolution layer sits *above* it, resolving directories/globs into
  explicit file lists before passing them to `reformat_files()`.

- **Library APIs**: KEEP DEPRECATED — `reformat_text()` and `reformat_file()` are
  unchanged.
  New public API is additive only (the `FileResolver` class and `resolve_files()`).

- **CLI behavior**: KEEP DEPRECATED for explicit file arguments.
  New behavior only when directories or glob patterns are passed.
  `flowmark README.md` behaves identically to today.
  `flowmark .` is new behavior (currently would fail).

- **File formats**: N/A — no file format changes.

## Stage 1: Planning Stage

### Feature Requirements

#### Core Features (Must Have)

1. **Directory recursion**: `flowmark .` and `flowmark docs/` recursively discover
   Markdown files.

2. **Default include pattern**: `*.md` — only Markdown files by default.

3. **`.gitignore` respect**: On by default.
   Reads `.gitignore`, `.git/info/exclude`, and parent `.gitignore` files.
   Overridable with `--no-respect-gitignore`.

4. **Hardcoded default exclusions**: ~35 directories that should almost never be
   formatted (`.git`, `node_modules`, `.venv`, `build`, `dist`, etc.).
   Applied during directory traversal for performance (prune, don't enter).

5. **`--exclude` flag**: Replaces all default exclusions (full control).

6. **`--extend-exclude` flag**: Adds to default exclusions (common case).

7. **`--force-exclude`**: When enabled, exclusion patterns apply even to files passed
   directly on the command line.
   Default: off (explicit files bypass exclusions, matching Ruff/Black behavior).

8. **`.flowmarkignore` file**: gitignore-syntax file for tool-specific exclusions.
   Searched in the current directory and parent directories.

9. **`--list-files` flag**: Print resolved file paths without formatting.
   Invaluable for debugging.

10. **`--extend-include` flag**: Add file patterns beyond `*.md`
    (e.g., `*.markdown`, `*.mdx`).

#### Promoted from Deferred to Planned

These were originally deferred but are now planned based on config system design work.
See [research-configuration-format-and-settings.md](../research/research-configuration-format-and-settings.md).

- **Max file size limit** (`--files-max-size`): Default 1 MiB, CLI flag + config.
- **Config file support**: TOML-based config (`flowmark.toml` / `.flowmark.toml` /
  `pyproject.toml [tool.flowmark]`) for all formatting AND file discovery settings.

#### Nice to Have (Deferred)

- `--staged` flag for git-staged files only
- Nested/hierarchical configuration files
- Parallel file processing
- Config inheritance (`extend` field, like Ruff)

#### Explicitly Out of Scope

- Watch mode / file system monitoring

### Acceptance Criteria

1. `flowmark --auto .` formats all `.md` files recursively, skipping gitignored and
   default-excluded directories, and completes in under 1 second for a typical project
   (not counting actual formatting time).

2. `flowmark --auto .` in a project with `node_modules/` containing thousands of `.md`
   files completes as fast as a project without `node_modules/` (directory is pruned,
   never entered).

3. `flowmark --list-files .` outputs the exact set of files that would be formatted.

4. All existing CLI usage (explicit file paths) works identically to today.

5. The file resolution module has no imports from `flowmark.*` (other than possibly
   shared types), making it extractable.

### Design Principles

- **Simple should be simple**: `flowmark --auto .` just works with no configuration.
- **Complex should be possible**: Any build system can customize includes/excludes.
- **Defaults are unsurprising**: Never format inside `node_modules`, `.venv`, etc.
- **Overrides are explicit**: `--exclude` replaces; `--extend-exclude` adds.
- **Library-first**: The module is a pure Python API; the CLI is a thin wrapper.

## Stage 2: Architecture Stage

### Current Source Layout (Post-Merge)

The codebase now includes a skill system (`skill.py`, `skills/SKILL.md`) and additional
CLI flags (`--skill`, `--install-skill`, `--agent-base`, `--docs`).
The CLI already handles "early exit" options (version, skill, docs) before formatting.
The file resolver integration follows the same pattern: resolve files early, then pass
to the existing formatting pipeline.

### Module Structure

```
src/flowmark/
  file_resolver/              # Self-contained module (future library)
    __init__.py               # Public API exports
    resolver.py               # FileResolver class — main entry point
    gitignore.py              # .gitignore / .ignore file parsing and matching
    defaults.py               # Default exclusion patterns, default includes
    types.py                  # Shared types (FileResolverConfig, etc.)
  cli.py                      # Updated — adds new flags, calls resolver
  reformat_api.py             # Unchanged — receives resolved file lists
  skill.py                    # Unchanged — skill installation (already merged)
  skills/SKILL.md             # Unchanged — skill definition (already merged)
  ...
```

The `file_resolver/` module has **no imports from `flowmark`** outside of itself.
It depends only on:

- Python standard library (`pathlib`, `os`, `fnmatch`)
- `pathspec` — well-maintained library for gitignore-style pattern matching
  (MIT license, pure Python, 2.7M monthly downloads)

### Core API Design

The module exposes a single main class, `FileResolver`, that encapsulates all file
discovery logic.
It is configured once, then used to resolve paths.

```python
from flowmark.file_resolver import FileResolver, FileResolverConfig

# Configuration — typically constructed from CLI args
config = FileResolverConfig(
    tool_name="flowmark",               # Determines ignore file name (.flowmarkignore)
    include=["*.md"],                    # File patterns to include
    extend_include=["*.markdown"],       # Additional include patterns
    exclude=None,                        # None = use defaults; list = replace defaults
    extend_exclude=["vendor/"],          # Additional exclude patterns
    respect_gitignore=True,              # Whether to read .gitignore
    force_exclude=False,                 # Whether exclusions apply to explicit paths
)

resolver = FileResolver(config)

# Resolve a mix of files, directories, and globs into concrete file paths
files: list[Path] = resolver.resolve([".", "extra/doc.md", "other/**/*.md"])

# Or just list what would be resolved
for path in resolver.resolve(["."]):
    print(path)
```

The `resolve()` method handles three kinds of input (following Prettier's model):

1. **Existing file path** → included directly (unless `force_exclude` filters it)
2. **Existing directory** → recursively walked, applying all filters
3. **Glob pattern** → expanded by the resolver (not the shell), applying all filters

### Filter Pipeline

During directory traversal, files pass through these filters in order:

```
Input paths
  ↓
1. Hardcoded default exclusions (prune directories early)
  ↓
2. User exclude / extend-exclude patterns (prune directories early)
  ↓
3. .gitignore patterns (prune directories early)
  ↓
4. .{tool_name}ignore patterns (prune directories early)
  ↓
5. Include pattern matching (only yield files matching *.md etc.)
  ↓
Output: list[Path]
```

**Key performance point**: Steps 1-4 are applied at the **directory level** during
traversal.
When a directory matches an exclusion, it is pruned entirely — `os.walk()` does not
descend into it.
This is what makes the difference between instant and painfully slow.

### Ignore File Resolution

The resolver searches for ignore files by walking up from the working directory:

- `.gitignore` — standard git behavior (read at every directory level during traversal)
- `.{tool_name}ignore` (e.g., `.flowmarkignore`) — searched from CWD upward, first
  found wins

Ignore files use **gitignore syntax**, parsed by the `pathspec` library.

### CLI Integration

New flags added to `flowmark` CLI (all optional, sensible defaults):

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--extend-include` | `str` (repeatable) | (none) | Additional file patterns to include |
| `--exclude` | `str` (repeatable) | (default list) | Replace default exclusion patterns |
| `--extend-exclude` | `str` (repeatable) | (none) | Add to default exclusion patterns |
| `--no-respect-gitignore` | `bool` | `False` | Disable `.gitignore` integration |
| `--force-exclude` | `bool` | `False` | Apply exclusions to explicitly-named files |
| `--list-files` | `bool` | `False` | Print resolved files, don't format |

The CLI constructs a `FileResolverConfig`, creates a `FileResolver`, calls
`resolver.resolve(args.files)`, and passes the result to `reformat_files()`.

### Dependency: `pathspec`

[`pathspec`](https://pypi.org/project/pathspec/) is the standard Python library for
gitignore-style pattern matching.
It is pure Python, MIT-licensed, has 2.7M+ monthly downloads, and is used by Black,
pre-commit, and many other tools.

It will be added to `dependencies` in `pyproject.toml`.

### Future Library Extraction Plan

To extract `file_resolver/` as a standalone library:

1. Create new repository (e.g., `gitglob` or `pathglob` or similar name)
2. Copy `src/flowmark/file_resolver/` → `src/{new_name}/`
3. Move `DEFAULT_EXCLUDES` to be a parameter rather than a constant (or provide
   sensible cross-language defaults)
4. Remove `tool_name` default of `"flowmark"`
5. Add `pyproject.toml`, tests, CI
6. Publish to PyPI
7. In flowmark: replace `file_resolver/` module with a dependency on the new package
8. Flowmark passes its tool-specific config (`tool_name="flowmark"`,
   `include=["*.md"]`, `DEFAULT_EXCLUDES`) when constructing the resolver

The interface between flowmark and the library would be:

```python
# After extraction, flowmark's integration would look like:
from pathglob import FileResolver, FileResolverConfig  # or whatever the library name is

config = FileResolverConfig(
    tool_name="flowmark",
    include=["*.md"],
    default_exclude=FLOWMARK_DEFAULT_EXCLUDES,  # flowmark-specific defaults
    ...cli_overrides,
)
resolver = FileResolver(config)
files = resolver.resolve(input_paths)
```

The changes needed are minimal:

- Default exclusion list moves from library constant to caller-provided parameter
- `tool_name` has no default (caller must specify)
- Everything else remains identical

## Stage 3: Refine Architecture

### Reusable Components

**From the standard library:**

- `pathlib.Path` — path manipulation
- `os.walk()` — directory traversal with pruning support (modify `dirs` in-place
  to prevent descent)
- `fnmatch` — basic glob matching (used as fallback, but `pathspec` is primary)

**From existing dependencies:**

- `strif.atomic_output_file` — already used in `reformat_api.py` for safe file writing;
  not needed in the resolver module itself

**New dependency:**

- `pathspec` — gitignore pattern matching.
  Specifically `pathspec.PathSpec.from_lines("gitwildmatch", patterns)`.

### No Existing Code to Reuse

There is currently **no** file discovery, globbing, or ignore logic anywhere in the
Flowmark codebase.
This is entirely new functionality.

### Simplification Notes

- The resolver module does NOT need to handle formatting, stdin, output, or any
  Flowmark-specific logic.
  Its only job: paths in → resolved file paths out.

- The CLI integration is a thin layer: parse flags → build config → resolve → pass to
  existing `reformat_files()`.

- No database, no network, no async — pure filesystem operations.

## Implementation Plan

### Phase 1: Core File Resolver Module

Build the self-contained `file_resolver/` module with all core functionality.
This module has **no imports from `flowmark`** and depends only on stdlib + `pathspec`.

#### New files

**`src/flowmark/file_resolver/__init__.py`** — Public API exports:
- Exports: `FileResolver`, `FileResolverConfig`, `DEFAULT_EXCLUDES`,
  `DEFAULT_INCLUDES`
- Module-level docstring explaining purpose, API, and future extraction plan

**`src/flowmark/file_resolver/types.py`** — Configuration dataclass:
- `FileResolverConfig` dataclass with fields:
  - `tool_name: str = "flowmark"` — determines ignore file name
    (`.flowmarkignore`)
  - `include: list[str] = ["*.md"]` — file patterns to include
  - `extend_include: list[str] = []` — additional include patterns
  - `exclude: list[str] | None = None` — `None` = use defaults; list = replace
    defaults
  - `extend_exclude: list[str] = []` — additional exclude patterns
  - `respect_gitignore: bool = True` — whether to read `.gitignore`
  - `force_exclude: bool = False` — whether exclusions apply to explicit paths
  - `files_max_size: int = 1_048_576` — max file size in bytes (0 = no limit)
- Property `effective_include` → combines `include + extend_include`
- Property `effective_exclude` → combines defaults (or `exclude`) +
  `extend_exclude`

**`src/flowmark/file_resolver/defaults.py`** — Constants:
- `DEFAULT_INCLUDES = ["*.md"]`
- `DEFAULT_EXCLUDES` — ~35 directory/file patterns that should never be
  formatted:
  `.git`, `node_modules`, `.venv`, `venv`, `__pycache__`, `build`, `dist`,
  `.tox`, `.nox`, `.mypy_cache`, `.ruff_cache`, `.pytest_cache`, `.eggs`,
  `*.egg-info`, `.hg`, `.svn`, `.bzr`, `_darcs`, `.idea`, `.vscode`,
  `.vs`, `.fleet`, `.next`, `.nuxt`, `.output`, `.cache`, `.parcel-cache`,
  `.turbo`, `coverage`, `htmlcov`, `.coverage`, `vendor`, `third_party`,
  `Pods`, `target`, `.terraform`
- Each entry is a gitignore-syntax pattern (directories end with `/`)

**`src/flowmark/file_resolver/gitignore.py`** — Ignore file handling:
- `load_gitignore(directory: Path) -> pathspec.PathSpec | None` — reads
  `.gitignore` in the given directory, returns compiled `PathSpec` or `None`
- `load_tool_ignore(tool_name: str, start_dir: Path) -> pathspec.PathSpec | None`
  — walks up from `start_dir` looking for `.{tool_name}ignore`, reads and
  compiles first found
- `collect_gitignore_specs(root: Path) -> dict[Path, pathspec.PathSpec]` —
  during traversal, lazily loads `.gitignore` files per directory for
  hierarchical matching
- Internal: uses `pathspec.PathSpec.from_lines("gitwildmatch", lines)` for all
  pattern compilation

**`src/flowmark/file_resolver/resolver.py`** — Main resolver class:
- `FileResolver` class:
  - `__init__(self, config: FileResolverConfig)` — stores config, compiles
    exclude patterns into a `pathspec.PathSpec`, loads tool-specific ignore file
  - `resolve(self, paths: list[str | Path]) -> list[Path]` — main entry point:
    - For each input path:
      - If it's an existing file → include directly (unless `force_exclude`
        filters it, or exceeds `files_max_size`)
      - If it's an existing directory → `_walk_directory()`
      - If it contains glob characters (`*`, `?`, `[`) → `_expand_glob()`
      - Otherwise → raise `FileNotFoundError`
    - Returns sorted, deduplicated list of `Path` objects
  - `_walk_directory(self, root: Path) -> Iterable[Path]` — uses `os.walk()`
    with in-place `dirs[:]` modification to prune excluded directories.
    At each level:
    1. Remove dirs matching hardcoded defaults
    2. Remove dirs matching user exclude patterns
    3. Remove dirs matching `.gitignore` patterns (loaded per-directory)
    4. Remove dirs matching tool-specific ignore patterns
    5. Yield files matching include patterns that don't exceed
       `files_max_size`
  - `_expand_glob(self, pattern: str) -> Iterable[Path]` — uses
    `Path.glob()` or `pathlib.Path('.').glob(pattern)`, then applies
    all filters
  - `_is_excluded(self, path: Path, relative_to: Path) -> bool` — checks a
    file/dir against all exclusion sources
  - `_exceeds_max_size(self, path: Path) -> bool` — checks file size against
    `files_max_size` (0 = no limit)

#### Modified files

**`pyproject.toml`** — Add dependency:
- Add `"pathspec>=0.12.1"` to `[project] dependencies` (line 39-44)
- Add `"tomli>=2.0.0; python_version < '3.11'"` for Python 3.10 TOML support
  (needed in Phase 3 but best to add now)

#### New test files

**`tests/test_file_resolver.py`** — Unit and integration tests:
- Uses `tmp_path` fixture to create realistic directory trees
- `conftest.py` or local fixture: `sample_tree` fixture that creates:
  ```
  project/
    README.md
    docs/
      guide.md
      api.md
    src/
      code.py
    node_modules/
      pkg/
        README.md (should be excluded)
    .venv/
      lib/
        README.md (should be excluded)
    .git/
      HEAD
    .gitignore (contains: "build/")
    build/
      output.md (should be excluded by .gitignore)
    vendor/
      dep.md (should be excluded by defaults)
    large_file.md (> 1 MiB, should be excluded by max-size)
  ```
- Test groups:
  - `FileResolverConfig` construction and defaults
  - `DEFAULT_EXCLUDES` — verify all ~35 entries match expected dirs
  - `load_gitignore` — parse valid/empty/missing `.gitignore`
  - `load_tool_ignore` — find `.flowmarkignore` walking upward
  - `resolve()` with single file → returns that file
  - `resolve()` with directory → recursive discovery, correct exclusions
  - `resolve()` with glob pattern → expansion + filtering
  - `resolve()` with mixed inputs → dedup and sort
  - `force_exclude=True` → explicit files also filtered
  - `force_exclude=False` (default) → explicit files bypass exclusions
  - `respect_gitignore=False` → `.gitignore` patterns ignored
  - `files_max_size` → large files skipped, 0 means no limit
  - `exclude` (non-None) → replaces defaults entirely
  - `extend_exclude` → adds to defaults
  - `extend_include` → additional patterns beyond `*.md`
  - Integration: realistic project tree with all exclusion sources

### Phase 2: CLI Integration and `.flowmarkignore`

Wire the resolver into Flowmark's CLI. After this phase, `flowmark --auto .`
works.

#### Modified files

**`src/flowmark/cli.py`** — Major changes:

1. **Expand `Options` dataclass** (line 57-77): Add fields:
   - `extend_include: list[str]`
   - `exclude: list[str] | None` (None = use defaults)
   - `extend_exclude: list[str]`
   - `respect_gitignore: bool`
   - `force_exclude: bool`
   - `list_files: bool`
   - `files_max_size: int`

2. **Add new argparse arguments** (after line 167, before `--version`):
   - `--extend-include` — `action="append"`, `default=[]`
   - `--exclude` — `action="append"`, `default=None`
   - `--extend-exclude` — `action="append"`, `default=[]`
   - `--no-respect-gitignore` — `action="store_true"`, sets
     `respect_gitignore=False`
   - `--force-exclude` — `action="store_true"`
   - `--list-files` — `action="store_true"`
   - `--files-max-size` — `type=int`, `default=1048576`

3. **Update `main()` flow** (line 229-293): After early-exit options
   (version/skill/docs) and before `reformat_files()`:
   - Import `FileResolver`, `FileResolverConfig`
   - Check if any input paths are directories or globs (vs. stdin/explicit
     files)
   - If so: construct `FileResolverConfig` from `Options`, create
     `FileResolver`, call `resolve()` to get file list
   - If `--list-files`: print resolved paths (one per line) and `return 0`
   - Pass resolved file list to `reformat_files()`
   - If all inputs are explicit files and no `--list-files`, skip resolver
     (backward compat — behaves identically to today)

4. **Require explicit file arguments for `--auto` and `--list-files`**: When
   either flag is used with no file args, print a clear error message and exit
   with code 1. Do NOT default to `.` silently. (See Phase 5 for the broader
   change making bare `flowmark` also require arguments.)

5. **Update help text** for `files` positional arg (line 93-98): Change from
   `"Input files (use '-' for stdin, multiple files supported)"` to
   `"Input files or directories (use '-' for stdin, '.' for current directory)"`

6. **Update module docstring** (line 1-44): Add directory/glob examples:
   ```
   # Format all Markdown files in current directory recursively
   flowmark --auto .

   # List files that would be formatted (without formatting)
   flowmark --list-files .

   # Format with additional file patterns
   flowmark --auto --extend-include "*.mdx" .

   # Format but skip a specific directory
   flowmark --auto --extend-exclude "drafts/" .
   ```

#### New test files

**`tests/test_cli_file_discovery.py`** — CLI integration tests:
- Uses `tmp_path` to create directory trees, then calls `main()` with args
- Test groups:
  - `flowmark --auto .` on a directory with `.md` files → formats all
  - `flowmark --auto .` skips `node_modules/`, `.venv/`, etc.
  - `flowmark --list-files .` → prints file paths, no formatting
  - `flowmark --list-files --extend-include "*.mdx" .` → includes `.mdx` files
  - `flowmark --extend-exclude "drafts/" --list-files .` → skips `drafts/`
  - `flowmark --exclude "custom/" --list-files .` → replaces all defaults
  - `flowmark --no-respect-gitignore --list-files .` → ignores `.gitignore`
  - `flowmark --force-exclude --list-files .` → filters explicit files too
  - `flowmark --auto` (no file args) → error with helpful message
  - `flowmark --list-files` (no file args) → error with helpful message
  - `flowmark --auto .` → formats current directory
  - `flowmark README.md` (explicit file) → works identically to today
  - `flowmark --list-files .` with `.flowmarkignore` → respects ignore file
  - `flowmark --files-max-size 100 --list-files .` → skips large files
  - Backward compat: `flowmark --auto README.md` → still works
  - Backward compat: `flowmark -` → stdin (explicit `-` required)

### Phase 3: Config File Loading

Add TOML-based config file support. After this phase, `flowmark .` (without
`--auto`) reads formatting settings from `flowmark.toml` or `pyproject.toml`.

See [research-configuration-format-and-settings.md](../research/research-configuration-format-and-settings.md)
for the full config schema and settings resolution design.

#### New files

**`src/flowmark/config.py`** — Config loading module:

- `FlowmarkConfig` dataclass with all settings:
  - Formatting: `width`, `semantic`, `cleanups`, `smartquotes`, `ellipses`,
    `list_spacing`
  - File discovery: `include`, `extend_include`, `exclude`, `extend_exclude`,
    `files_max_size`, `respect_gitignore`, `force_exclude`
  - Defaults match current CLI defaults (all formatting features off,
    `width=88`)

- `find_config_file(start_dir: Path) -> Path | None` — walks up from
  `start_dir` looking for `.flowmark.toml` > `flowmark.toml` >
  `pyproject.toml` (only if `[tool.flowmark]` section exists)

- `load_config(config_path: Path) -> FlowmarkConfig` — reads TOML file,
  extracts `[tool.flowmark]` section if pyproject.toml, maps TOML keys
  (kebab-case like `list-spacing`) to Python fields (snake_case like
  `list_spacing`), returns populated `FlowmarkConfig`
  - Uses `tomllib` (Python 3.11+) or `tomli` (Python 3.10 backport)

- `merge_cli_with_config(cli_opts: Options, config: FlowmarkConfig | None, is_auto: bool) -> Options`
  — implements settings resolution:
  - If `is_auto`: formatting settings come from `--auto` preset (fixed),
    file discovery settings come from config, `width` from config if present
  - If not `is_auto`: explicit CLI flags override config, config overrides
    defaults
  - Handles the three-way precedence: CLI flags > config > built-in defaults
  - Needs to distinguish "user passed `--semantic`" from "default `False`" —
    use `argparse` default sentinel or track which flags were explicitly set

#### Modified files

**`src/flowmark/cli.py`** — Config integration:

1. **In `_parse_args()` or `main()`**: After parsing args but before
   constructing `Options`:
   - Call `find_config_file(Path.cwd())`
   - If found, call `load_config(config_path)` to get `FlowmarkConfig`
   - Call `merge_cli_with_config()` to produce final `Options`
   - The `--auto` flag determines which merge strategy to use

2. **Track explicitly-set CLI flags**: Change `argparse` defaults for boolean
   formatting flags from `False` to `None` (sentinel). This lets
   `merge_cli_with_config` distinguish "user didn't pass `--semantic`"
   (should use config value) from "user passed `--semantic`" (should
   override config).
   The `--auto` expansion in `_parse_args()` sets all formatting flags to
   `True` explicitly, so `--auto` always overrides config.

**`pyproject.toml`** — already added `tomli` in Phase 1.

#### New test files

**`tests/test_config.py`** — Config loading tests:
- Uses `tmp_path` to create config files
- Test groups:
  - `find_config_file` — finds `.flowmark.toml`, `flowmark.toml`,
    `pyproject.toml` in correct precedence order
  - `find_config_file` — walks up to parent directories
  - `find_config_file` — skips `pyproject.toml` without `[tool.flowmark]`
  - `load_config` from `flowmark.toml` — all fields correctly mapped
  - `load_config` from `pyproject.toml` — extracts `[tool.flowmark]`
  - `load_config` — partial config (missing fields use defaults)
  - `load_config` — kebab-case keys map to snake_case fields
  - `merge_cli_with_config` — explicit CLI flags override config
  - `merge_cli_with_config` — unset CLI flags fall through to config
  - `merge_cli_with_config` with `--auto` — formatting settings from preset,
    file discovery from config, `width` from config
  - `merge_cli_with_config` — no config file → pure defaults
  - Integration: create `flowmark.toml` in `tmp_path`, run CLI with
    directory arg, verify config settings are applied

### Phase 4: Documentation Updates

All documentation changes needed to reflect new features. No new Python code.

#### Modified files

**`README.md`** — Multiple sections:

1. **Update "Usage" section** (around line 178): Change CLI syntax from
   `[file]` to `[files/dirs...]`. Add new flags to the help output block.

2. **Replace "Batch Format" section** (around line 66-69): Replace the `find`
   command recommendation with `flowmark --auto .`. Keep `find` as a
   legacy note.

3. **Add "File Discovery" section** (after "Usage", before "Use in
   VSCode/Cursor"): New section covering:
   - Directory recursion (`flowmark --auto .`)
   - Default include patterns (`*.md`)
   - Default exclusions (summarize key ones: `node_modules`, `.venv`, `.git`,
     `build`, `dist`, etc.)
   - `.gitignore` integration (on by default)
   - `.flowmarkignore` for tool-specific exclusions
   - `--list-files` for debugging
   - Customizing includes/excludes

4. **Add "Configuration" section** (after "File Discovery"): New section
   covering:
   - Config file locations (`.flowmark.toml`, `flowmark.toml`,
     `pyproject.toml`)
   - Example config
   - `--auto` vs config interaction (link to or summarize the settings
     resolution semantics)
   - `width`, formatting options, file discovery options

5. **Update "Use in VSCode/Cursor" section** (around line 249-264): Note
   that `flowmark --auto .` can be used for batch formatting alongside
   per-file-on-save.

**`src/flowmark/skills/SKILL.md`** — Agent instructions:

1. **Replace "Batch Format" workflow** (around line 66-69): Replace `find`
   command with `uvx flowmark@latest --auto .`

2. **Update key options table** (around line 40-49): Add rows for
   `--list-files`, `--extend-include`, `--extend-exclude`,
   `--files-max-size`

**`src/flowmark/cli.py`** — Docstring only:
- Already updated in Phase 2 with directory/glob examples

#### Verification (all phases)

- [x] `file_resolver/` module has no imports from `flowmark.*`
- [x] Full test suite passes (`uv run pytest`)
- [x] Lint passes (`uv run ruff check src/ tests/`)
- [x] Type check passes (`uv run basedpyright`)
- [x] `flowmark --help` shows new flags correctly
- [x] `flowmark --list-files .` in the flowmark repo lists all `.md` files,
      skipping `.venv/`, `.git/`, `node_modules/` etc.
- [x] `flowmark --auto .` in the flowmark repo formats all `.md` files
- [x] `flowmark --auto README.md` still works (backward compat)
- [ ] `flowmark` (no args) → error (Phase 5)
- [ ] `flowmark -` → stdin still works (explicit `-` required, Phase 5)
- [x] `flowmark --auto` (no file args) → error
- [x] `flowmark --list-files` (no file args) → error
- [x] `flowmark --docs` output is consistent (reads README.md)
- [x] Config file loading works with `flowmark.toml` and `pyproject.toml`

### Outstanding Questions

- [ ] **Library name for future extraction**: `pathglob`? `gitglob`? `file-resolver`?
  `ignore-glob`? Should be researched for PyPI availability when the time comes.

### Resolved Questions

- [x] **Config file support**: Include/exclude settings and all formatting options
  will be configurable via `flowmark.toml`, `.flowmark.toml`, or
  `pyproject.toml [tool.flowmark]` using TOML format.
  See [research-configuration-format-and-settings.md](../research/research-configuration-format-and-settings.md)
  for the full analysis.
  The `FileResolverConfig` dataclass will be absorbed into a broader `FlowmarkConfig`
  that covers all settings.

- [x] **`--auto` vs config interaction**: `--auto` is a fixed formatting preset that
  ignores config formatting settings (always enables semantic, cleanups, smartquotes,
  ellipses).
  Without `--auto`, formatting settings come from the config file.
  File discovery settings (exclude, max-size, etc.) always apply regardless of
  `--auto`.
  See the "Settings Resolution" section in the config research doc.

- [x] **Max file size limit**: Will be implemented as `files-max-size` with a default
  of 1 MiB (1,048,576 bytes), matching Biome's approach.
  Available as both a CLI flag and config setting.
  `0` disables the limit.

- [x] **Explicit argument requirement (no implicit defaults)**: All modes require
  explicit file/directory arguments. There is no implicit default-to-`.` or
  implicit stdin behavior. This avoids error-prone silent defaults.

  | Invocation | Behavior |
  |---|---|
  | `flowmark` (no args) | **Error**: "No input specified. Provide files, directories, or '-' for stdin." |
  | `flowmark --auto` (no file args) | **Error**: "--auto requires at least one file or directory argument (use '.' for current directory)" |
  | `flowmark --list-files` (no file args) | **Error**: "--list-files requires at least one file or directory argument (use '.' for current directory)" |
  | `flowmark --auto .` | Formats all `.md` files in current directory recursively |
  | `flowmark --auto README.md` | Formats a single file |
  | `flowmark --list-files .` | Lists files that would be formatted |
  | `flowmark README.md` | Formats file to stdout |
  | `flowmark -` | Reads from stdin, formats to stdout |

  **Rationale**: The previous behavior of defaulting to `.` when `--auto` was used
  without arguments was considered error-prone. Requiring explicit `.` as the argument
  makes the user conscious of what will be formatted. Similarly, bare `flowmark` with
  no arguments previously read from stdin silently, which is surprising for a tool
  whose primary use case is file formatting.

  **Implementation status**: Error for `--auto` and `--list-files` with no args is
  implemented. Error for bare `flowmark` (no args at all) is planned.

- [x] **Glob patterns must be quoted**: Shell-expanded `**` globs may not work as
  expected because bash does not expand `**` recursively unless `globstar` is enabled
  (off by default). Users should always quote glob patterns
  (e.g., `'docs/**/*.md'`) to let Flowmark handle expansion internally via
  Python's `pathlib.Path.glob()`, which always supports `**` for recursive matching.

  Note: `--extend-include` and `--extend-exclude` use gitignore-style patterns
  (e.g., `*.mdx`, `drafts/`), not shell globs. These do not need quoting.

- [x] **Symlink behavior**: During recursive directory traversal (`os.walk()`),
  symlinks are **not followed**. This prevents infinite loops from circular symlinks
  and avoids formatting files outside the project tree. However, explicitly named
  symlinks passed as arguments are resolved and processed normally (since
  `Path.is_file()` follows symlinks by default).

## Phase 5: CLI Argument Strictness and Documentation Updates

This phase makes all CLI modes require explicit arguments and updates all
documentation to reflect the final behavior.

### CLI Changes

1. **Change `files` positional argument default from `["-"]` to `[]`**: This means
   bare `flowmark` with no args results in `options.files == []` instead of silently
   reading from stdin.

2. **Add early error check in `main()`**: When `options.files` is empty, print a
   clear error message and return exit code 1. Provide different messages depending
   on which flags are active:
   - `--auto`: "Error: --auto requires at least one file or directory argument
     (use '.' for current directory)"
   - `--list-files`: "Error: --list-files requires at least one file or directory
     argument (use '.' for current directory)"
   - Neither: "Error: No input specified. Provide files, directories, or '-' for
     stdin."

3. **Update help text** for the `files` positional argument to clarify that at least
   one file, directory, or `-` is required.

4. **Remove all `opts.files == ["-"]` checks** that previously detected "no args
   given" — replace with `not options.files` checks.

### Documentation Changes

All documentation updates for the file discovery and globbing feature, organized by
file:

#### `README.md`

| Section | Change | Status |
|---|---|---|
| CLI Reference table → `--auto` row | Changed "With no file args, defaults to `.`" → "Requires file/directory args (use `.` for current directory)" | Done |
| New subsection: "Glob Patterns" (under File Discovery) | Added: always quote `**` patterns, explanation of shell vs Flowmark expansion, note that `--extend-include`/`--extend-exclude` use gitignore-style patterns | Done |
| New subsection: "Symlinks" (under File Discovery) | Added: symlinks not followed during recursion, resolved when explicit | Done |
| Quick Start examples | Verify all examples use explicit args (already do) | Done |
| Batch Formatting section | Verify examples use explicit `.` (already do) | Done |

#### `src/flowmark/skills/SKILL.md`

| Section | Change | Status |
|---|---|---|
| Key Options table → `--auto` row | Changed "With no file args, defaults to `.`" → "Requires file/directory args (use `.` for current directory)" | Done |
| Common Workflows examples | Verify all use explicit args (already do) | Done |

#### `src/flowmark/cli.py`

| Section | Change | Status |
|---|---|---|
| `--auto` help text | Changed to "Requires at least one file or directory argument (use '.' for current directory)" | Done |
| `--list-files` help text | Changed to "Requires at least one file or directory argument (use '.' for current directory)" | Done |
| `files` positional arg help text | Needs update: clarify that at least one arg is required | Planned |
| `files` default | Needs change: `["-"]` → `[]` | Planned |
| `main()` error check | Needs update: check for `not options.files` | Planned |
| Module docstring examples | All already use explicit args | Done |

#### `tests/test_cli_file_discovery.py`

| Test | Change | Status |
|---|---|---|
| `test_auto_no_args_errors` | New test: `main(["--auto"])` returns 1 with error message | Done |
| `test_list_files_no_args_errors` | New test: `main(["--list-files"])` returns 1 with error message | Done |
| `test_auto_with_dot_formats_cwd` | New test: `main(["--auto", "."])` succeeds | Done |
| `test_no_args_errors` | Planned: bare `main([])` returns 1 with error message | Planned |
| `test_stdin_explicit_dash` | Planned: verify `main(["-"])` still works for stdin | Planned |
