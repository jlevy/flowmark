"""
Block content detection heuristics for preserving newlines.

This module provides heuristics to detect block-level content (tables, lists)
that should have their structure preserved during line wrapping. When such
content is detected between tags, newlines around it are preserved to prevent
the content from being merged onto a single line.

These heuristics are intentionally simple and conservative - they detect
patterns that almost certainly indicate block content where newlines matter.
"""

from __future__ import annotations

import re

# Pattern to detect Markdown table rows: lines starting with |
# This catches both header rows, separator rows (|---|---|), and data rows
_table_row_re = re.compile(r"^\s*\|")

# Pattern to detect Markdown list items
# Matches: -, *, +, or numbered lists like 1. or 1)
_list_item_re = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")


def line_is_table_row(line: str) -> bool:
    """Check if a line appears to be a Markdown table row."""
    return bool(_table_row_re.match(line))


def line_is_list_item(line: str) -> bool:
    """Check if a line appears to be a Markdown list item."""
    return bool(_list_item_re.match(line))


def line_is_block_content(line: str) -> bool:
    """
    Check if a line appears to be block content that needs newline preservation.

    Block content includes table rows and list items - content where the line
    structure is semantically meaningful and should not be merged during wrapping.
    """
    return line_is_table_row(line) or line_is_list_item(line)


def text_contains_block_content(text: str) -> bool:
    """
    Check if text contains block content that needs newline preservation.

    Returns True if the text contains table rows or list items, indicating
    that newlines in this text should be preserved rather than normalized.
    """
    for line in text.split("\n"):
        if line_is_block_content(line):
            return True
    return False
