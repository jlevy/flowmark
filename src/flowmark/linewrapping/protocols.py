"""
Protocol definitions for the linewrapping module.
"""

from __future__ import annotations

from typing import Protocol


class LineWrapper(Protocol):
    """
    Takes a text string and any indents to use, and returns the wrapped text.
    """

    def __call__(self, text: str, initial_indent: str, subsequent_indent: str) -> str: ...
