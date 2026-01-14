"""
Block content detection using Markdown parsing.

This module detects block-level content (tables, lists) by parsing the content
with Marko rather than using regex heuristics. This gives accurate detection
and allows proper normalization of newlines around block content.

When block content is detected between tags, we ensure proper newlines
(one blank line before and after) to prevent CommonMark lazy continuation
from incorrectly merging tags into block structures.
"""

from __future__ import annotations

import marko


def content_starts_with_block(text: str) -> bool:
    """
    Check if text starts with block-level content (list or table).

    Parses the text with Marko and checks if the first non-paragraph element
    is a list or table. This is more accurate than regex line matching.
    """
    text = text.strip()
    if not text:
        return False

    try:
        doc = marko.parse(text)
    except Exception:
        return False

    if not doc.children:
        return False

    # Check the first child element
    first = doc.children[0]
    element_type = type(first).__name__

    # List types in Marko
    if element_type in ("List", "OrderedList", "UnorderedList"):
        return True

    # Table (if using GFM extension)
    if element_type == "Table":
        return True

    # Check if it looks like a table (pipe-delimited lines)
    # Marko without GFM may parse tables as paragraphs
    if element_type == "Paragraph":
        # Get raw text and check if it looks like a table
        raw = getattr(first, "children", [])
        if raw and hasattr(raw[0], "children"):
            first_text = str(raw[0].children) if raw[0].children else ""
            if first_text.strip().startswith("|"):
                return True

    return False


def content_is_block_element(text: str) -> bool:
    """
    Check if text is primarily block-level content (list or table).

    Returns True if the text parses to a list or table at the top level.
    """
    text = text.strip()
    if not text:
        return False

    try:
        doc = marko.parse(text)
    except Exception:
        return False

    if not doc.children:
        return False

    # Check all top-level children
    for child in doc.children:
        element_type = type(child).__name__
        if element_type in ("List", "OrderedList", "UnorderedList", "Table"):
            return True

    return False


def normalize_block_content_in_tags(text: str) -> str:
    """
    Normalize block content between tags to have proper newlines.

    When we detect that content between tags is primarily a list or table,
    ensure there's a blank line after the opening tag and before the closing
    tag. This prevents CommonMark lazy continuation from merging tags into
    the block structure.

    For example:
        {% field %}
        - Item 1
        {% /field %}

    Becomes:
        {% field %}

        - Item 1

        {% /field %}
    """
    # This function is a placeholder for future enhancement.
    # The actual normalization should happen at a higher level where we
    # have access to the full tag structure.
    return text


# Keep simple line-based detection for cases where we just need a quick check
# without full parsing (e.g., in the line wrapper where we process segments)


def line_is_table_row(line: str) -> bool:
    """Quick check if a line looks like a table row (starts with |)."""
    return line.lstrip().startswith("|")


def line_is_list_item(line: str) -> bool:
    """Quick check if a line looks like a list item."""
    stripped = line.lstrip()
    # Unordered: -, *, +
    if stripped and stripped[0] in "-*+" and len(stripped) > 1 and stripped[1] in " \t":
        return True
    # Ordered: 1. or 1)
    if stripped and stripped[0].isdigit():
        i = 1
        while i < len(stripped) and stripped[i].isdigit():
            i += 1
        if i < len(stripped) and stripped[i] in ".)" and i + 1 < len(stripped):
            return True
    return False


def line_is_block_content(line: str) -> bool:
    """Quick check if a line is block content (table row or list item)."""
    return line_is_table_row(line) or line_is_list_item(line)
