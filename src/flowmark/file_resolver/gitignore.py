"""Gitignore and tool-specific ignore file handling using pathspec."""

from __future__ import annotations

from pathlib import Path

import pathspec


def load_gitignore(directory: Path) -> pathspec.PathSpec | None:
    """
    Read `.gitignore` in the given directory and return a compiled `PathSpec`,
    or `None` if the file doesn't exist or is empty.
    """
    gitignore = directory / ".gitignore"
    if not gitignore.is_file():
        return None
    lines = gitignore.read_text().splitlines()
    lines = [line for line in lines if line.strip() and not line.strip().startswith("#")]
    if not lines:
        return None
    return pathspec.PathSpec.from_lines("gitignore", lines)


def load_tool_ignore(tool_name: str, start_dir: Path) -> pathspec.PathSpec | None:
    """
    Walk up from `start_dir` looking for `.{tool_name}ignore` (e.g., `.flowmarkignore`).
    Returns compiled `PathSpec` from first found, or `None`.
    """
    ignore_name = f".{tool_name}ignore"
    current = start_dir.resolve()
    while True:
        candidate = current / ignore_name
        if candidate.is_file():
            lines = candidate.read_text().splitlines()
            lines = [line for line in lines if line.strip() and not line.strip().startswith("#")]
            if lines:
                return pathspec.PathSpec.from_lines("gitignore", lines)
            return None
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None
