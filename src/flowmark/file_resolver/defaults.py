"""
Default include and exclude patterns for file discovery.

These patterns use gitignore syntax. Directory patterns end with `/`.
"""

from __future__ import annotations

DEFAULT_INCLUDES: list[str] = ["*.md"]

# Directories and patterns that should almost never contain files worth formatting.
# Applied during directory traversal for performance (prune, don't enter).
DEFAULT_EXCLUDES: list[str] = [
    # Version control
    ".git/",
    ".hg/",
    ".svn/",
    ".bzr/",
    "_darcs/",
    # Python
    ".venv/",
    "venv/",
    "__pycache__/",
    ".tox/",
    ".nox/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".pytest_cache/",
    ".eggs/",
    "*.egg-info/",
    # Build output
    "build/",
    "dist/",
    # JavaScript/Node
    "node_modules/",
    ".next/",
    ".nuxt/",
    ".output/",
    ".cache/",
    ".parcel-cache/",
    ".turbo/",
    # IDE/Editor
    ".idea/",
    ".vscode/",
    ".vs/",
    ".fleet/",
    # Coverage
    "coverage/",
    "htmlcov/",
    ".coverage/",
    # Other
    "vendor/",
    "third_party/",
    "Pods/",
    "target/",
    ".terraform/",
]
