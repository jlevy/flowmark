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

#### Nice to Have (Deferred)

- `--staged` flag for git-staged files only
- Nested/hierarchical configuration files
- Max file size limit
- Parallel file processing
- Config file support for include/exclude (`.flowmark.toml` or `pyproject.toml`
  `[tool.flowmark]`)

#### Explicitly Out of Scope

- Changing Flowmark's formatting behavior (this is purely about file discovery)
- Config file support for formatting options (separate feature)
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

**Tasks:**

- [ ] Create `src/flowmark/file_resolver/` package structure
- [ ] Implement `types.py` — `FileResolverConfig` dataclass
- [ ] Implement `defaults.py` — `DEFAULT_EXCLUDES` list, `DEFAULT_INCLUDES`
- [ ] Implement `gitignore.py` — gitignore file discovery and `pathspec`-based matching
- [ ] Implement `resolver.py` — `FileResolver` class with `resolve()` method
- [ ] Implement `__init__.py` — clean public API exports
- [ ] Add `pathspec` to `pyproject.toml` dependencies
- [ ] Write unit tests for `FileResolverConfig` construction
- [ ] Write unit tests for default exclusion matching
- [ ] Write unit tests for gitignore parsing and matching
- [ ] Write unit tests for directory recursion with exclusion pruning
- [ ] Write unit tests for glob pattern expansion
- [ ] Write unit tests for mixed input (files + directories + globs)
- [ ] Write unit tests for `force_exclude` behavior
- [ ] Write integration test with a realistic directory tree fixture

### Phase 2: CLI Integration and `.flowmarkignore`

Wire the resolver into Flowmark's CLI and add the ignore file.

**Tasks:**

- [ ] Add CLI flags to `cli.py`: `--extend-include`, `--exclude`, `--extend-exclude`,
      `--no-respect-gitignore`, `--force-exclude`, `--list-files`
- [ ] Update `main()` to construct `FileResolverConfig` from CLI args
- [ ] Update `main()` to call `FileResolver.resolve()` before `reformat_files()`
- [ ] Implement `--list-files` mode (print and exit, no formatting)
- [ ] Implement `.flowmarkignore` file discovery and loading in `gitignore.py`
- [ ] Update `--auto` shortcut to work with directory arguments
- [ ] Write CLI integration tests for directory formatting
- [ ] Write CLI integration tests for `--list-files`
- [ ] Write CLI integration tests for exclude/extend-exclude flags
- [ ] Write CLI integration tests for `.flowmarkignore`
- [ ] Verify all existing CLI tests still pass unchanged
- [ ] Update CLI help text and docstring examples

### Phase 3: Documentation Updates

All documentation changes needed to reflect the new file discovery features.

#### README.md Updates

The README currently has these relevant sections that need updating:

- [ ] **Update "Usage" section** (`README.md:178`): The usage block currently shows
      single-file CLI syntax (`[file]`). Update to show `[files/dirs...]` and add the
      new flags (`--extend-include`, `--exclude`, `--extend-exclude`,
      `--no-respect-gitignore`, `--force-exclude`, `--list-files`) to the help output
      block.

- [ ] **Update CLI docstring** (`cli.py:1-44`): Add directory and glob examples to the
      module docstring, which is used as CLI epilog text. Add examples like:
      ```
      # Format all Markdown files in current directory recursively
      flowmark --auto .

      # Format all Markdown files in a specific directory
      flowmark --auto docs/

      # List files that would be formatted (without formatting)
      flowmark --list-files .

      # Format with additional file patterns
      flowmark --auto --extend-include "*.mdx" .

      # Format but skip a specific directory
      flowmark --auto --extend-exclude "drafts/" .
      ```

- [ ] **Replace "Batch Format" section** (`README.md:66-69`): The current
      recommendation is `find . -name "*.md" -exec uvx flowmark@latest --auto {} \;`
      which is exactly the pain point this feature solves. Replace with the new
      `flowmark --auto .` approach, keeping the `find` command as a legacy alternative.

- [ ] **Add "File Discovery" section** to README: New section (after "Usage", before
      "Use in VSCode/Cursor") covering:
      - How directory recursion works (`flowmark --auto .`)
      - Default include patterns (`*.md`)
      - Default exclusions (link to full list or summarize key ones)
      - `.gitignore` integration (on by default)
      - `.flowmarkignore` for tool-specific exclusions
      - `--list-files` for debugging
      - Customizing includes/excludes

- [ ] **Update "Use in VSCode/Cursor" section** (`README.md:249-264`): Consider noting
      that the Run on Save extension is still needed for per-file formatting on save,
      but `flowmark --auto .` can be used for batch formatting.

#### SKILL.md Updates

- [ ] **Update SKILL.md** (`src/flowmark/skills/SKILL.md:66-69`): The "Batch Format"
      workflow currently shows `find . -name "*.md" -exec uvx flowmark@latest --auto {} \;`.
      Replace with `uvx flowmark@latest --auto .` and add `--list-files` to the
      key options table.

- [ ] **Update SKILL.md key options table** (`src/flowmark/skills/SKILL.md:40-49`):
      Add rows for `--extend-include`, `--exclude`, `--extend-exclude`,
      `--no-respect-gitignore`, `--force-exclude`, and `--list-files`.

#### AGENTS.md Updates

- [ ] **No changes needed** to AGENTS.md — it covers tbd workflow, not Flowmark
      formatting features. The skill integration handles Flowmark-specific agent
      instructions via SKILL.md.

#### pyproject.toml Updates

- [ ] **Add `pathspec` dependency** to `[project] dependencies` list.

#### Internal Documentation

- [ ] **Add module-level docstring** to `file_resolver/__init__.py` explaining the
      module's purpose, public API, and that it is designed for future extraction as a
      standalone library.

- [ ] **Add docstrings** to `FileResolver` class and `resolve()` method with usage
      examples (these serve as the library API docs).

#### Verification

- [ ] Review that the `file_resolver/` module has no imports from `flowmark.*`
- [ ] Run full test suite and verify no regressions
- [ ] Run `flowmark --help` and verify the new flags appear correctly
- [ ] Run `flowmark --list-files .` in the flowmark repo itself and verify output
      is sensible (should list all `.md` files, skipping `.venv/`, `.git/`, etc.)
- [ ] Verify `flowmark --docs` output is consistent (it reads README.md)

### Outstanding Questions

- [ ] **Library name for future extraction**: `pathglob`? `gitglob`? `file-resolver`?
  `ignore-glob`? Should be researched for PyPI availability when the time comes.

- [ ] **Should `--auto` imply directory recursion?** Currently `--auto` means
  `--inplace --nobackup --semantic --cleanups --smartquotes --ellipses`.
  Should `flowmark --auto` (no file args) default to `.`?
  Probably yes, but this is a UX decision.

- [ ] **Config file support**: Should include/exclude settings be configurable via
  `pyproject.toml` `[tool.flowmark]` or `.flowmark.toml`?
  Deferred to a future spec, but the `FileResolverConfig` dataclass is designed to
  accept these values from any source.
