"""
FileResolver — main entry point for file discovery.

Resolves a mix of files, directories, and glob patterns into a deduplicated,
sorted list of concrete file paths, applying all configured filters.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from pathlib import Path

import pathspec

from flowmark.file_resolver.gitignore import load_gitignore, load_tool_ignore
from flowmark.file_resolver.types import FileResolverConfig

# Characters that indicate a path is a glob pattern rather than a literal path.
_GLOB_CHARS = frozenset("*?[")


class FileResolver:
    """
    Discovers files matching configured include patterns while respecting
    gitignore, tool-specific ignore files, and default/custom exclusions.

    Designed for future extraction as a standalone library — no imports
    from `flowmark` outside this `file_resolver` package.
    """

    def __init__(self, config: FileResolverConfig) -> None:
        self._config: FileResolverConfig = config
        self._exclude_spec: pathspec.PathSpec = pathspec.PathSpec.from_lines(
            "gitignore", config.effective_exclude
        )
        self._include_spec: pathspec.PathSpec = pathspec.PathSpec.from_lines(
            "gitignore", config.effective_include
        )
        self._tool_ignore: pathspec.PathSpec | None = None
        self._tool_ignore_loaded: bool = False
        # Cache gitignore specs per directory to avoid re-reading from disk.
        self._gitignore_cache: dict[Path, pathspec.PathSpec | None] = {}

    def resolve(self, paths: Sequence[str | Path]) -> list[Path]:
        """
        Resolve input paths into a sorted, deduplicated list of files.

        Each input is handled as:
        - Existing file → included directly (unless `force_exclude` filters it)
        - Existing directory → recursively walked with all filters applied
        - Contains glob characters → expanded then filtered
        - Otherwise → `FileNotFoundError`
        """
        seen: set[Path] = set()
        result: list[Path] = []

        for raw_path in paths:
            p = Path(raw_path)

            if p.is_file():
                resolved = p.resolve()
                if resolved not in seen and self._should_include_explicit(p):
                    seen.add(resolved)
                    result.append(resolved)
            elif p.is_dir():
                for found in self._walk_directory(p):
                    resolved = found.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        result.append(resolved)
            elif any(c in str(raw_path) for c in _GLOB_CHARS):
                for found in self._expand_glob(str(raw_path)):
                    resolved = found.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        result.append(resolved)
            else:
                raise FileNotFoundError(f"Path not found: {raw_path}")

        result.sort()
        return result

    def _should_include_explicit(self, path: Path) -> bool:
        """Check if an explicitly-named file should be included."""
        if self._config.force_exclude:
            # Check against all exclusion patterns
            rel = path.name
            if self._exclude_spec.match_file(rel):
                return False
            # Also check parent directory components
            for parent in path.parents:
                if self._exclude_spec.match_file(parent.name + "/"):
                    return False
        if self._exceeds_max_size(path):
            return False
        return True

    def _walk_directory(self, root: Path) -> Iterable[Path]:
        """
        Walk a directory tree using `os.walk()`, pruning excluded directories
        in-place for performance.
        """
        tool_ignore = self._get_tool_ignore(root)

        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            rel_to_root = current.relative_to(root)

            # Prune excluded directories in-place (prevents descent)
            dirnames[:] = [
                d
                for d in dirnames
                if not self._is_dir_excluded(d, rel_to_root / d, current, tool_ignore)
            ]

            # Yield files matching include patterns
            for filename in filenames:
                filepath = current / filename
                if self._include_spec.match_file(filename) and not self._exceeds_max_size(filepath):
                    yield filepath

    def _is_dir_excluded(
        self,
        dirname: str,
        rel_path: Path,
        current_dir: Path,
        tool_ignore: pathspec.PathSpec | None,
    ) -> bool:
        """Check if a directory should be pruned during traversal."""
        dir_with_slash = dirname + "/"
        rel_with_slash = str(rel_path) + "/"

        if self._exclude_spec.match_file(dir_with_slash):
            return True
        if self._exclude_spec.match_file(rel_with_slash):
            return True

        if self._config.respect_gitignore:
            gitignore_spec = self._get_gitignore(current_dir)
            if gitignore_spec and gitignore_spec.match_file(dir_with_slash):
                return True

        if tool_ignore and tool_ignore.match_file(dir_with_slash):
            return True
        if tool_ignore and tool_ignore.match_file(rel_with_slash):
            return True

        return False

    def _expand_glob(self, pattern: str) -> Iterable[Path]:
        """Expand a glob pattern, then apply all filters."""
        # Determine the root for globbing
        parts = Path(pattern).parts
        root = Path(".")
        glob_part = pattern
        for i, part in enumerate(parts):
            if any(c in part for c in _GLOB_CHARS):
                root = Path(*parts[:i]) if i > 0 else Path(".")
                glob_part = str(Path(*parts[i:]))
                break

        for path in root.glob(glob_part):
            if path.is_file() and self._include_spec.match_file(path.name):
                if not self._exceeds_max_size(path):
                    yield path

    def _exceeds_max_size(self, path: Path) -> bool:
        """Check if a file exceeds the configured max size. 0 = no limit."""
        if self._config.files_max_size == 0:
            return False
        try:
            return path.stat().st_size > self._config.files_max_size
        except OSError:
            return False

    def _get_gitignore(self, directory: Path) -> pathspec.PathSpec | None:
        """Load and cache gitignore for a directory."""
        if directory not in self._gitignore_cache:
            self._gitignore_cache[directory] = load_gitignore(directory)
        return self._gitignore_cache[directory]

    def _get_tool_ignore(self, start_dir: Path) -> pathspec.PathSpec | None:
        """Lazily load tool-specific ignore file."""
        if not self._tool_ignore_loaded:
            self._tool_ignore = load_tool_ignore(self._config.tool_name, start_dir)
            self._tool_ignore_loaded = True
        return self._tool_ignore
