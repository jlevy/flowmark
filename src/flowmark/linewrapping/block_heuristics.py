"""
Block content detection using simple line-based heuristics.

This module detects block-level content (tables, lists) using fast line-based
pattern matching that follows CommonMark specification (Section 5.2-5.3).
This allows proper handling of newlines around block content when processing tags.

See: https://spec.commonmark.org/0.31.2/#list-items

When block content is detected between tags, we ensure proper newlines
(one blank line before and after) to prevent CommonMark lazy continuation
from incorrectly merging tags into block structures.

Note: We use simple heuristics rather than full Marko parsing because:
1. At this point in the pipeline, Marko has already parsed the document
2. Content with Jinja/Markdoc tags is treated as paragraph text by Marko
3. Line-based detection is much faster and sufficient for our needs
4. We only need to detect "looks like a list/table" for newline handling
"""

from __future__ import annotations


def line_is_table_row(line: str) -> bool:
    """
    Check if a line looks like a GFM table row.

    Tables are a GitHub Flavored Markdown extension, not part of CommonMark core.
    See: https://github.github.com/gfm/#tables-extension-

    A table row starts with a pipe character (optionally preceded by whitespace).
    This matches both data rows (`| A | B |`) and separator rows (`|---|---|`).
    """
    return line.lstrip().startswith("|")


def line_is_list_item(line: str) -> bool:
    """
    Check if a line looks like a CommonMark list item.

    Per CommonMark spec (https://spec.commonmark.org/0.31.2/#list-items):
    - Bullet list markers: `-`, `+`, or `*` followed by at least one space/tab
    - Ordered list markers: 1-9 digits followed by `.` or `)` then space/tab

    This correctly rejects cases like:
    - `---` (thematic break, not a list item)
    - `1.0.0` (version number, not a list item)
    - `1.Item` (no space after marker)
    """
    stripped = line.lstrip()
    if not stripped:
        return False

    # Unordered list: -, *, + followed by space or tab
    if stripped[0] in "-*+":
        return len(stripped) > 1 and stripped[1] in " \t"

    # Ordered list: digits followed by . or ) then space or tab
    # CommonMark allows 1-9 digits (up to 999999999)
    if stripped[0].isdigit():
        i = 1
        while i < len(stripped) and i < 9 and stripped[i].isdigit():
            i += 1
        # Must have . or ) followed by space/tab
        if i < len(stripped) and stripped[i] in ".)":
            # Check for space/tab after the marker
            if i + 1 < len(stripped) and stripped[i + 1] in " \t":
                return True

    return False


def line_is_block_content(line: str) -> bool:
    """
    Check if a line is block content (table row or list item).

    Used to detect transitions between tags and block content, which require
    blank lines to prevent CommonMark lazy continuation.
    """
    return line_is_table_row(line) or line_is_list_item(line)


## Tests


def test_line_is_table_row():
    # Valid table rows
    assert line_is_table_row("| A | B |")
    assert line_is_table_row("|---|---|")
    assert line_is_table_row("| Cell |")
    assert line_is_table_row("  | Indented |")
    assert line_is_table_row("\t| Tab indented |")

    # Not table rows
    assert not line_is_table_row("Not a table")
    assert not line_is_table_row("A | B")  # Doesn't start with |
    assert not line_is_table_row("")
    assert not line_is_table_row("   ")


def test_line_is_list_item_unordered():
    # Valid unordered list items
    assert line_is_list_item("- Item")
    assert line_is_list_item("* Item")
    assert line_is_list_item("+ Item")
    assert line_is_list_item("-\tTab after marker")
    assert line_is_list_item("  - Indented item")
    assert line_is_list_item("- ")  # Empty item (just marker and space)

    # Not unordered list items
    assert not line_is_list_item("-")  # No space after
    assert not line_is_list_item("-Item")  # No space after
    assert not line_is_list_item("---")  # Thematic break
    assert not line_is_list_item("***")  # Thematic break

    # Edge case: "- -" IS a valid list item (content is "-")
    assert line_is_list_item("- -")


def test_line_is_list_item_ordered():
    # Valid ordered list items
    assert line_is_list_item("1. Item")
    assert line_is_list_item("1) Item")
    assert line_is_list_item("10. Item")
    assert line_is_list_item("999. Item")
    assert line_is_list_item("1.\tTab after marker")
    assert line_is_list_item("  1. Indented")
    assert line_is_list_item("1. ")  # Empty item

    # Not ordered list items (the key fixes)
    assert not line_is_list_item("1.0 version")  # No space after .
    assert not line_is_list_item("1.0.0")  # Version number
    assert not line_is_list_item("1.Item")  # No space after .
    assert not line_is_list_item("1.")  # No space after (nothing after)
    assert not line_is_list_item("1")  # Just a number
    assert not line_is_list_item("12345678901. Item")  # Too many digits (>9)


def test_line_is_block_content():
    # Table rows
    assert line_is_block_content("| A | B |")
    assert line_is_block_content("|---|---|")

    # List items
    assert line_is_block_content("- Item")
    assert line_is_block_content("1. Item")

    # Neither
    assert not line_is_block_content("Regular text")
    assert not line_is_block_content("1.0.0 version")
    assert not line_is_block_content("")
