"""
TOML-based config file loading for Flowmark.

Searches for `.flowmark.toml`, `flowmark.toml`, or `pyproject.toml [tool.flowmark]`
walking up from the current directory. Config values are merged with CLI flags
using three-way precedence: explicit CLI flags > config file > built-in defaults.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, TypeVar, cast

if sys.version_info >= (3, 11):
    import tomllib  # pyright: ignore[reportUnreachable]
else:
    import tomli as tomllib  # type: ignore[no-redef]  # pyright: ignore[reportUnreachable]


@dataclass
class FlowmarkConfig:
    """
    Parsed config from a TOML file. Fields are `None` when not set in the config,
    allowing the merge logic to distinguish "not configured" from "explicitly set
    to default value".
    """

    # Formatting
    width: int | None = None
    semantic: bool | None = None
    cleanups: bool | None = None
    smartquotes: bool | None = None
    ellipses: bool | None = None
    list_spacing: str | None = None
    # File discovery
    include: list[str] | None = None
    extend_include: list[str] | None = None
    exclude: list[str] | None = None
    extend_exclude: list[str] | None = None
    files_max_size: int | None = None
    respect_gitignore: bool | None = None
    force_exclude: bool | None = None


# Config file search order (first match wins within each directory level)
_CONFIG_FILENAMES = [".flowmark.toml", "flowmark.toml", "pyproject.toml"]

# Mapping from TOML kebab-case keys to Python snake_case field names
_KEBAB_TO_SNAKE: dict[str, str] = {
    "list-spacing": "list_spacing",
    "extend-include": "extend_include",
    "extend-exclude": "extend_exclude",
    "files-max-size": "files_max_size",
    "respect-gitignore": "respect_gitignore",
    "force-exclude": "force_exclude",
}

_VALID_FIELDS = {f.name for f in fields(FlowmarkConfig)}


def find_config_file(start_dir: Path) -> Path | None:
    """
    Walk up from `start_dir` looking for a config file. Returns the first
    found, or `None`. Search order per directory: `.flowmark.toml` >
    `flowmark.toml` > `pyproject.toml` (only if it has `[tool.flowmark]`).
    """
    current = start_dir.resolve()
    while True:
        for filename in _CONFIG_FILENAMES:
            candidate = current / filename
            if candidate.is_file():
                if filename == "pyproject.toml":
                    # Only use pyproject.toml if it has [tool.flowmark]
                    if _pyproject_has_flowmark_section(candidate):
                        return candidate
                else:
                    return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def _pyproject_has_flowmark_section(path: Path) -> bool:
    """Check if a pyproject.toml has a [tool.flowmark] section."""
    try:
        data = tomllib.loads(path.read_text())
        return "flowmark" in data.get("tool", {})
    except (tomllib.TOMLDecodeError, OSError):
        return False


def load_config(config_path: Path) -> FlowmarkConfig:
    """
    Load a `FlowmarkConfig` from a TOML file. Supports both standalone
    `flowmark.toml` / `.flowmark.toml` and `pyproject.toml` (extracts
    `[tool.flowmark]`). TOML kebab-case keys are mapped to Python snake_case.
    """
    data = tomllib.loads(config_path.read_text())

    if config_path.name == "pyproject.toml":
        data = data.get("tool", {}).get("flowmark", {})

    return _parse_config_data(data)


def _parse_config_data(data: dict[str, Any]) -> FlowmarkConfig:
    """Parse a flat or sectioned TOML dict into FlowmarkConfig."""
    # Flatten sections: [formatting] and [file-discovery] merge into top level
    flat: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in cast(dict[str, Any], value).items():
                flat[sub_key] = sub_value
        else:
            flat[key] = value

    # Map kebab-case to snake_case
    mapped: dict[str, Any] = {}
    for key, value in flat.items():
        snake_key = _KEBAB_TO_SNAKE.get(key, key.replace("-", "_"))
        if snake_key in _VALID_FIELDS:
            mapped[snake_key] = value

    return FlowmarkConfig(**mapped)


_T = TypeVar("_T")


def merge_cli_with_config(
    cli_opts: _T,
    config: FlowmarkConfig | None,
    is_auto: bool,
    explicit_flags: set[str],
) -> _T:
    """
    Merge CLI options with config file settings.

    Precedence: explicit CLI flags > config file > built-in defaults.
    In `--auto` mode, formatting settings are fixed by the preset;
    only `width` and file discovery settings come from config.
    """
    if config is None:
        return cli_opts

    # Fields that --auto locks (these come from the preset, not config)
    auto_locked = {"semantic", "cleanups", "smartquotes", "ellipses", "inplace", "nobackup"}

    for cfg_field in fields(FlowmarkConfig):
        cfg_value = getattr(config, cfg_field.name)
        if cfg_value is None:
            continue  # Not set in config

        # Skip if CLI explicitly set this flag
        if cfg_field.name in explicit_flags:
            continue

        # In auto mode, don't override formatting preset
        if is_auto and cfg_field.name in auto_locked:
            continue

        # Apply config value to CLI options
        if hasattr(cli_opts, cfg_field.name):
            setattr(cli_opts, cfg_field.name, cfg_value)

    return cli_opts
