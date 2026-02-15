"""Configuration types for file resolution."""

from __future__ import annotations

from dataclasses import dataclass, field

from flowmark.file_resolver.defaults import DEFAULT_EXCLUDES, DEFAULT_INCLUDES


@dataclass
class FileResolverConfig:
    """
    Configuration for file discovery and filtering.

    `tool_name` determines the ignore file name (e.g., `.flowmarkignore`).
    `exclude=None` means use `DEFAULT_EXCLUDES`; providing a list replaces them entirely.
    `files_max_size=0` disables the size limit.
    """

    tool_name: str = "flowmark"
    include: list[str] = field(default_factory=lambda: list(DEFAULT_INCLUDES))
    extend_include: list[str] = field(default_factory=list)
    exclude: list[str] | None = None
    extend_exclude: list[str] = field(default_factory=list)
    respect_gitignore: bool = True
    force_exclude: bool = False
    files_max_size: int = 1_048_576  # 1 MiB

    @property
    def effective_include(self) -> list[str]:
        """Combined include patterns: `include + extend_include`."""
        return self.include + self.extend_include

    @property
    def effective_exclude(self) -> list[str]:
        """Combined exclude patterns: defaults (or `exclude`) + `extend_exclude`."""
        base = self.exclude if self.exclude is not None else list(DEFAULT_EXCLUDES)
        return base + self.extend_exclude
