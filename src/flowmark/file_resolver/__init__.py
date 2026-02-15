"""
Self-contained file discovery module with gitignore-aware globbing
and configurable exclusion patterns.

Designed for future extraction as a standalone PyPI library.
No imports from `flowmark` outside this package.

Usage::

    from flowmark.file_resolver import FileResolver, FileResolverConfig

    config = FileResolverConfig(
        tool_name="flowmark",
        include=["*.md"],
        extend_exclude=["vendor/"],
    )
    resolver = FileResolver(config)
    files = resolver.resolve([".", "extra/doc.md"])
"""

from flowmark.file_resolver.defaults import DEFAULT_EXCLUDES, DEFAULT_INCLUDES
from flowmark.file_resolver.resolver import FileResolver
from flowmark.file_resolver.types import FileResolverConfig

__all__ = [
    "DEFAULT_EXCLUDES",
    "DEFAULT_INCLUDES",
    "FileResolver",
    "FileResolverConfig",
]
