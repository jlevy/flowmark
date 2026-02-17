"""
Tag handling for Jinja/Markdoc tags and HTML comments.

This module provides detection and handling of template tags used by systems like
Markdoc, Markform, Jinja, Nunjucks, and WordPress Gutenberg.

The main concerns are:
1. Detecting tag boundaries to preserve newlines around them
2. Normalizing and denormalizing adjacent tags for proper tokenization
"""

from __future__ import annotations

import re

from flowmark.linewrapping.atomic_patterns import (
    PAIRED_HTML_COMMENT,
    PAIRED_JINJA_COMMENT,
    PAIRED_JINJA_TAG,
    PAIRED_JINJA_VAR,
    SINGLE_HTML_COMMENT,
    SINGLE_JINJA_COMMENT,
    SINGLE_JINJA_TAG,
    SINGLE_JINJA_VAR,
)
from flowmark.linewrapping.block_heuristics import (
    line_is_block_content,
    line_is_list_item,
    line_is_table_row,
)
from flowmark.linewrapping.protocols import LineWrapper

# Pattern to match complete template tags (for protecting content inside tags).
# Uses the single tag patterns from atomic_patterns.
TEMPLATE_TAG_PATTERN: re.Pattern[str] = re.compile(
    "|".join(
        [
            SINGLE_JINJA_TAG.pattern,
            SINGLE_JINJA_COMMENT.pattern,
            SINGLE_JINJA_VAR.pattern,
            SINGLE_HTML_COMMENT.pattern,
        ]
    ),
    re.DOTALL,
)

# Pattern to match paired tags like {% tag %}{% /tag %} that should stay together.
# Uses paired tag patterns from atomic_patterns.
PAIRED_TAGS_PATTERN: re.Pattern[str] = re.compile(
    "|".join(
        [
            PAIRED_JINJA_TAG.pattern,
            PAIRED_JINJA_COMMENT.pattern,
            PAIRED_JINJA_VAR.pattern,
            PAIRED_HTML_COMMENT.pattern,
        ]
    ),
    re.DOTALL,
)


# Pattern to detect adjacent tags (closing tag immediately followed by opening tag)
# This handles cases like %}{% or --><!-- where there's no space between
_adjacent_tags_re: re.Pattern[str] = re.compile(
    rf"({SINGLE_JINJA_TAG.close_re})({SINGLE_JINJA_TAG.open_re})|"
    rf"({SINGLE_JINJA_COMMENT.close_re})({SINGLE_JINJA_COMMENT.open_re})|"
    rf"({SINGLE_JINJA_VAR.close_re})({SINGLE_JINJA_VAR.open_re})|"
    rf"({SINGLE_HTML_COMMENT.close_re})({SINGLE_HTML_COMMENT.open_re})"
)

# Pattern to remove spaces between adjacent tags that were added during word splitting
_denormalize_tags_re: re.Pattern[str] = re.compile(
    rf"({SINGLE_JINJA_TAG.close_re}) ({SINGLE_JINJA_TAG.open_re})|"
    rf"({SINGLE_JINJA_COMMENT.close_re}) ({SINGLE_JINJA_COMMENT.open_re})|"
    rf"({SINGLE_JINJA_VAR.close_re}) ({SINGLE_JINJA_VAR.open_re})|"
    rf"({SINGLE_HTML_COMMENT.close_re}) ({SINGLE_HTML_COMMENT.open_re})"
)


def normalize_adjacent_tags(text: str) -> str:
    """
    Add a space between adjacent tags so they become separate tokens.
    For example: %}{% becomes %} {%
    """

    def add_space(match: re.Match[str]) -> str:
        groups = match.groups()
        for i in range(0, len(groups), 2):
            if groups[i] is not None:
                return groups[i] + " " + groups[i + 1]
        return match.group(0)

    return _adjacent_tags_re.sub(add_space, text)


def denormalize_adjacent_tags(text: str) -> str:
    """
    Remove spaces between adjacent tags that were added during word splitting.
    This restores original adjacency for paired tags like `{% field %}{% /field %}`.
    """

    def remove_space(match: re.Match[str]) -> str:
        groups = match.groups()
        for i in range(0, len(groups), 2):
            if groups[i] is not None:
                return groups[i] + groups[i + 1]
        return match.group(0)

    return _denormalize_tags_re.sub(remove_space, text)


def _is_tag_only_line(line: str) -> bool:
    """
    Check if a line contains only a tag (opening or closing), not inline tags in content.

    A tag-only line starts with a tag delimiter and ends with a tag delimiter,
    with no substantial non-tag content. This distinguishes:
    - `{% field %}` (tag-only line)
    - `- [ ] Item {% #id %}` (content with inline tag - NOT tag-only)
    - `  <!-- #kg-32zz -->` (indented continuation - NOT tag-only)

    Indented lines are never considered "tag-only" because they are continuations
    of previous content (like list items), not standalone tag blocks.
    """
    # Indented lines are continuations, not standalone tag blocks
    if line and line[0].isspace():
        return False

    stripped = line.strip()
    if not stripped:
        return False

    # Check if it starts with a tag
    starts_tag = (
        stripped.startswith(SINGLE_JINJA_TAG.open_delim)
        or stripped.startswith(SINGLE_JINJA_COMMENT.open_delim)
        or stripped.startswith(SINGLE_JINJA_VAR.open_delim)
        or stripped.startswith(SINGLE_HTML_COMMENT.open_delim)
    )

    # Check if it ends with a tag
    ends_tag = (
        stripped.endswith(SINGLE_JINJA_TAG.close_delim)
        or stripped.endswith(SINGLE_JINJA_COMMENT.close_delim)
        or stripped.endswith(SINGLE_JINJA_VAR.close_delim)
        or stripped.endswith(SINGLE_HTML_COMMENT.close_delim)
    )

    return starts_tag and ends_tag


def preprocess_tag_block_spacing(text: str) -> str:
    """
    Preprocess text to ensure proper blank lines around block content within tags.

    When block content (lists, tables) appears directly after an opening tag or
    directly before a closing tag, the CommonMark parser may use lazy continuation
    to merge them incorrectly. This function inserts blank lines to prevent this.

    This preprocessing must happen BEFORE Markdown parsing, as the parser's
    structure cannot be fixed after the fact.

    Example transformation:
        {% field %}
        - item 1
        - item 2
        {% /field %}

    Becomes:
        {% field %}

        - item 1
        - item 2

        {% /field %}
    """
    lines = text.split("\n")
    result_lines: list[str] = []

    # Check if there are any tag-only lines in the text
    has_tag_only_lines = any(_is_tag_only_line(line) for line in lines)
    if not has_tag_only_lines:
        return text

    for i, line in enumerate(lines):
        # Check if we need to add a blank line BEFORE this line
        if i > 0:
            prev_line = lines[i - 1]
            prev_is_empty = prev_line.strip() == ""

            # Case 1: Previous line is a tag-only line, current line is block content
            # (need blank line after opening tag before list/table)
            if not prev_is_empty and _is_tag_only_line(prev_line) and line_is_block_content(line):
                result_lines.append("")

            # Case 2: Previous line is block content, current line is a closing tag-only line
            # (need blank line after list/table before closing tag)
            if not prev_is_empty and line_is_block_content(prev_line) and _is_tag_only_line(line):
                result_lines.append("")

        result_lines.append(line)

    return "\n".join(result_lines)


def line_ends_with_tag(line: str) -> bool:
    """Check if a line ends with a Jinja/Markdoc tag or HTML comment."""
    stripped = line.rstrip()
    if not stripped:
        return False
    # Check for Jinja-style tags
    if (
        stripped.endswith(SINGLE_JINJA_TAG.close_delim)
        or stripped.endswith(SINGLE_JINJA_COMMENT.close_delim)
        or stripped.endswith(SINGLE_JINJA_VAR.close_delim)
    ):
        return True
    # Check for HTML comments
    if stripped.endswith(SINGLE_HTML_COMMENT.close_delim):
        return True
    return False


def line_starts_with_tag(line: str) -> bool:
    """Check if a line starts with a Jinja/Markdoc tag or HTML comment."""
    stripped = line.lstrip()
    if not stripped:
        return False
    # Check for Jinja-style tags
    if (
        stripped.startswith(SINGLE_JINJA_TAG.open_delim)
        or stripped.startswith(SINGLE_JINJA_COMMENT.open_delim)
        or stripped.startswith(SINGLE_JINJA_VAR.open_delim)
    ):
        return True
    # Check for HTML comments
    if stripped.startswith(SINGLE_HTML_COMMENT.open_delim):
        return True
    return False


def _is_unindented_tag_line(line: str) -> bool:
    """
    Check if a line is an unindented line that starts with a tag.

    This distinguishes between:
    - `{% field %}` at the start of a line (returns True)
    - `  <!-- #tag -->` which is indented continuation (returns False)

    Indented tag lines are typically continuations of previous content
    (like list items) and should not trigger segment breaks or blank line
    insertion in tag handling.
    """
    if not line:
        return False
    # Check if the line has leading whitespace
    if line[0].isspace():
        return False
    return line_starts_with_tag(line)


def add_tag_newline_handling(
    base_wrapper: LineWrapper,
) -> LineWrapper:
    """
    Augments a LineWrapper to preserve newlines around Jinja/Markdoc tags
    and HTML comments.

    When a line ends with a tag or the next line starts with a tag,
    the newline between them is preserved rather than being normalized
    away during text wrapping.

    This enables compatibility with Markdoc, Markform, and similar systems
    that use block-level tags like `{% field %}...{% /field %}`.

    The `tags` parameter is retained for API compatibility but currently unused.
    Both atomic and wrap modes apply the multiline tag fix (workaround for
    Markdoc parser bug - see GitHub issue #17).

    IMPORTANT LIMITATION: This operates at the line-wrapping level, AFTER
    Markdown parsing. If the Markdown parser (Marko) has already interpreted
    content as part of a block element (e.g., list item continuation), we
    cannot undo that structure. For example:

        - list item
        {% /tag %}

    The parser may treat `{% /tag %}` as list continuation, causing it to
    be indented. The newline IS preserved, but indentation is added.

    WORKAROUND: Use blank lines around block elements inside tags:

        {% field %}

        - Item 1
        - Item 2

        {% /field %}
    """

    def enhanced_wrapper(text: str, initial_indent: str, subsequent_indent: str) -> str:
        # If no newlines in input, just wrap and apply post-processing fixes.
        # The base_wrapper may produce multi-line output that needs fixing.
        if "\n" not in text:
            result = base_wrapper(text, initial_indent, subsequent_indent)
            # Fix multiline tags: ensure closing tag on own line when opening spans lines.
            # This applies in both atomic and wrap modes to work around Markdoc parser bug.
            result = _fix_multiline_opening_tag_with_closing(result)
            return result

        lines = text.split("\n")

        # If only one line after split, same as above
        if len(lines) <= 1:
            result = base_wrapper(text, initial_indent, subsequent_indent)
            result = _fix_multiline_opening_tag_with_closing(result)
            return result

        # Check if there are any tags in the text - only apply list heuristics
        # when tags are present to avoid changing normal markdown behavior.
        has_tags = any(line_ends_with_tag(line) or line_starts_with_tag(line) for line in lines)

        # Group lines into segments that should be wrapped together
        # A new segment starts when:
        # - The previous line ends with a tag
        # - The current line starts with a tag
        # - The current or previous line is a table row (always — tables are structural)
        # - (Only if tags present) The current or previous line is a list item
        segments: list[str] = []
        current_segment_lines: list[str] = []

        for i, line in enumerate(lines):
            is_first_line = i == 0
            prev_ends_with_tag = not is_first_line and line_ends_with_tag(lines[i - 1])
            # Only treat unindented tag lines as segment boundaries.
            # Indented tag lines are continuations (e.g., list item continuations).
            curr_starts_with_tag = _is_unindented_tag_line(line)

            # Table rows are always segment boundaries — they are structural
            # markdown elements that must never be line-wrapped.
            # List items are only boundaries when tags are present.
            curr_is_table = line_is_table_row(line)
            prev_is_table = not is_first_line and line_is_table_row(lines[i - 1])
            curr_is_block = curr_is_table or (has_tags and line_is_list_item(line))
            prev_is_block = prev_is_table or (
                has_tags and not is_first_line and line_is_list_item(lines[i - 1])
            )

            # Start a new segment if there's a tag or block content boundary
            if prev_ends_with_tag or curr_starts_with_tag or curr_is_block or prev_is_block:
                if current_segment_lines:
                    segments.append("\n".join(current_segment_lines))
                    current_segment_lines = []

            current_segment_lines.append(line)

        # Don't forget the last segment
        if current_segment_lines:
            segments.append("\n".join(current_segment_lines))

        # If we only have one segment, no tag boundaries were found
        if len(segments) == 1:
            result = base_wrapper(text, initial_indent, subsequent_indent)
            result = _fix_multiline_opening_tag_with_closing(result)
            return result

        # Wrap each segment separately.
        # Table row segments are passed through as-is (never wrapped) since
        # pipe-delimited rows are structural markdown that must stay on one line.
        wrapped_segments: list[str] = []
        for i, segment in enumerate(segments):
            is_first = i == 0
            cur_initial_indent = initial_indent if is_first else subsequent_indent
            segment_lines = segment.split("\n")
            if all(line_is_table_row(line) for line in segment_lines if line.strip()):
                # Table rows: preserve verbatim with appropriate indent
                indented_lines = []
                for j, line in enumerate(segment_lines):
                    indent = cur_initial_indent if j == 0 else subsequent_indent
                    indented_lines.append(indent + line if line.strip() else line)
                wrapped = "\n".join(indented_lines)
            else:
                wrapped = base_wrapper(segment, cur_initial_indent, subsequent_indent)
            wrapped_segments.append(wrapped)

        # Rejoin segments, normalizing newlines around block content.
        # When transitioning between a tag and block content (list/table),
        # ensure exactly one blank line to prevent CommonMark lazy continuation.
        result_parts: list[str] = []
        for i, wrapped in enumerate(wrapped_segments):
            if i == 0:
                result_parts.append(wrapped)
                continue

            prev_segment = segments[i - 1]
            curr_segment = segments[i]

            # Check if we're transitioning to/from block content
            prev_is_block = any(line_is_block_content(line) for line in prev_segment.split("\n"))
            curr_is_block = any(line_is_block_content(line) for line in curr_segment.split("\n"))
            prev_is_tag = (
                line_ends_with_tag(prev_segment.split("\n")[-1]) if prev_segment else False
            )
            # Only treat unindented tag lines as "tag" for blank line insertion.
            # Indented tag lines are continuations and shouldn't trigger blank lines.
            curr_is_tag = (
                _is_unindented_tag_line(curr_segment.split("\n")[0]) if curr_segment else False
            )

            # Ensure exactly one blank line between tag and block content
            if (prev_is_tag and curr_is_block) or (prev_is_block and curr_is_tag):
                # Add blank line separator
                result_parts.append("")  # Empty string creates blank line when joined
                result_parts.append(wrapped)
            else:
                result_parts.append(wrapped)

        result = "\n".join(result_parts)

        # Post-process: ensure closing tags have proper spacing and no indentation.
        # The Markdown parser may indent closing tags due to lazy continuation.
        result = _fix_closing_tag_spacing(result)

        # Fix multi-line opening tags that have closing tags on the same line.
        # This works around a Markdoc parser bug (see GitHub issue #17).
        result = _fix_multiline_opening_tag_with_closing(result)

        return result

    return enhanced_wrapper


def _is_closing_tag(line: str) -> bool:
    """Check if a line is a closing tag."""
    stripped = line.lstrip()
    return (
        stripped.startswith("{% /")
        or stripped.startswith("{# /")
        or stripped.startswith("{{ /")
        or stripped.startswith("<!-- /")
    )


def _fix_closing_tag_spacing(text: str) -> str:
    """
    Fix closing tag spacing for block content only.

    When a closing tag follows block content (like a list item or table row),
    the Markdown parser may indent it as list continuation. This function:
    1. Adds a blank line before closing tags that follow block content
    2. Strips any incorrect indentation from closing tags

    Regular paragraph text before closing tags is NOT modified - no blank line
    is added. The blank line is only needed to prevent CommonMark lazy
    continuation for block elements.
    """
    lines = text.split("\n")
    fixed_lines: list[str] = []

    for i, line in enumerate(lines):
        if _is_closing_tag(line):
            stripped = line.lstrip()
            # Only add blank line before closing tag if previous line is block content
            if i > 0 and fixed_lines:
                prev_line = fixed_lines[-1]
                prev_is_empty = prev_line.strip() == ""
                prev_is_block = line_is_block_content(prev_line)
                if not prev_is_empty and prev_is_block:
                    # Add blank line before closing tag to prevent lazy continuation
                    fixed_lines.append("")
            # Add the closing tag without indentation
            fixed_lines.append(stripped)
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)


# Pattern to detect closing delimiter of opening tag followed by a closing tag.
# This handles cases like:  %}{% /tag %}  or  --><!-- /tag -->
# where a multi-line opening tag ends and a closing tag follows on the same line.
# Uses named group "closing_tag" to capture the start of the closing tag.
_multiline_closing_pattern: re.Pattern[str] = re.compile(
    rf"{SINGLE_JINJA_TAG.close_re}\s*(?P<closing_tag>{SINGLE_JINJA_TAG.open_re}\s*/)|"
    rf"{SINGLE_JINJA_COMMENT.close_re}\s*(?P<closing_comment>{SINGLE_JINJA_COMMENT.open_re}\s*/)|"
    rf"{SINGLE_JINJA_VAR.close_re}\s*(?P<closing_var>{SINGLE_JINJA_VAR.open_re}\s*/)|"
    rf"{SINGLE_HTML_COMMENT.close_re}\s*(?P<closing_html>{SINGLE_HTML_COMMENT.open_re}\s*/)"
)


def _fix_multiline_opening_tag_with_closing(text: str) -> str:
    """
    Ensure closing tags are on their own line when the opening tag spans multiple lines.

    This works around a Markdoc parser bug where multi-line opening tags with
    closing tags on the same line cause incorrect AST parsing.

    Problem pattern (triggers Markdoc bug):
        {% tag attr1=value1
        attr2=value2 %}{% /tag %}

    Fixed pattern:
        {% tag attr1=value1
        attr2=value2 %}
        {% /tag %}

    Single-line paired tags like `{% field %}{% /field %}` are NOT affected.
    Tags in the middle of prose like `Before {% field %}{% /field %} after` are
    also NOT affected because the line contains content before the tag.
    """
    # Only apply fix if there are multiple lines - single line input means
    # no multi-line tags to fix
    if "\n" not in text:
        return text

    lines = text.split("\n")
    result_lines: list[str] = []

    for i, line in enumerate(lines):
        # Skip the first line - it can't be a continuation of a multi-line tag
        if i == 0:
            result_lines.append(line)
            continue

        stripped = line.lstrip()

        # Only process lines that are continuations (don't start with a tag opener).
        # If a line starts with a tag opener, the tag began on that line, not a continuation.
        is_tag_start = (
            stripped.startswith(SINGLE_JINJA_TAG.open_delim)
            or stripped.startswith(SINGLE_JINJA_COMMENT.open_delim)
            or stripped.startswith(SINGLE_JINJA_VAR.open_delim)
            or stripped.startswith(SINGLE_HTML_COMMENT.open_delim)
        )

        if not is_tag_start:
            match = _multiline_closing_pattern.search(line)
            if match:
                # Find which named group matched and split at the closing tag
                for group_name in ["closing_tag", "closing_comment", "closing_var", "closing_html"]:
                    if match.group(group_name) is not None:
                        split_pos = match.start(group_name)
                        before = line[:split_pos].rstrip()
                        closing = line[split_pos:].lstrip()
                        result_lines.append(before)
                        result_lines.append(closing)
                        break
                continue

        result_lines.append(line)

    return "\n".join(result_lines)
