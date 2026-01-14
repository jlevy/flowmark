"""
Tag handling for Jinja/Markdoc tags and HTML comments.

This module provides detection and handling of template tags used by systems like
Markdoc, Markform, Jinja, Nunjucks, and WordPress Gutenberg.

The main concerns are:
1. Detecting tag boundaries to preserve newlines around them
2. Providing constants for tag delimiters used in word splitting patterns
3. Normalizing and denormalizing adjacent tags for proper tokenization
"""

from __future__ import annotations

import re

from flowmark.linewrapping.block_heuristics import line_is_block_content
from flowmark.linewrapping.protocols import LineWrapper

# Tag delimiters - all tag syntax defined in one place for consistency.
#
# Supported tag formats:
# - Jinja/Markdoc: {% tag %}, {% /tag %}, {# comment #}, {{ variable }}
# - HTML comments: <!-- tag -->, <!-- /tag -->

# Jinja/Markdoc template tags
JINJA_TAG_OPEN = "{%"
JINJA_TAG_CLOSE = "%}"
# Jinja comments
JINJA_COMMENT_OPEN = "{#"
JINJA_COMMENT_CLOSE = "#}"
# Jinja variables
JINJA_VAR_OPEN = "{{"
JINJA_VAR_CLOSE = "}}"
# HTML comments
HTML_COMMENT_OPEN = "<!--"
HTML_COMMENT_CLOSE = "-->"

# Regex-escaped versions of delimiters (for use in regex patterns)
JINJA_TAG_OPEN_RE = r"\{%"
JINJA_TAG_CLOSE_RE = r"%\}"
JINJA_COMMENT_OPEN_RE = r"\{#"
JINJA_COMMENT_CLOSE_RE = r"#\}"
JINJA_VAR_OPEN_RE = r"\{\{"
JINJA_VAR_CLOSE_RE = r"\}\}"
HTML_COMMENT_OPEN_RE = r"<!--"
HTML_COMMENT_CLOSE_RE = r"-->"


# Pattern to detect adjacent tags (closing tag immediately followed by opening tag)
# This handles cases like %}{% or --><!-- where there's no space between
_adjacent_tags_re: re.Pattern[str] = re.compile(
    rf"({JINJA_TAG_CLOSE_RE})({JINJA_TAG_OPEN_RE})|"
    rf"({JINJA_COMMENT_CLOSE_RE})({JINJA_COMMENT_OPEN_RE})|"
    rf"({JINJA_VAR_CLOSE_RE})({JINJA_VAR_OPEN_RE})|"
    rf"({HTML_COMMENT_CLOSE_RE})({HTML_COMMENT_OPEN_RE})"
)

# Pattern to remove spaces between adjacent tags that were added during word splitting
_denormalize_tags_re: re.Pattern[str] = re.compile(
    rf"({JINJA_TAG_CLOSE_RE}) ({JINJA_TAG_OPEN_RE})|"
    rf"({JINJA_COMMENT_CLOSE_RE}) ({JINJA_COMMENT_OPEN_RE})|"
    rf"({JINJA_VAR_CLOSE_RE}) ({JINJA_VAR_OPEN_RE})|"
    rf"({HTML_COMMENT_CLOSE_RE}) ({HTML_COMMENT_OPEN_RE})"
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


# Maximum number of whitespace-separated words to coalesce into a single token.
MAX_TAG_WORDS = 12


def generate_coalescing_patterns(
    start: str, end: str, middle: str = r".+", max_words: int = MAX_TAG_WORDS
) -> list[tuple[str, ...]]:
    """
    Generate coalescing patterns for tags with a given start/end delimiter.

    For example, for template tags {% ... %}:
        start=r"\\{%", end=r".*%\\}", middle=r".+"

    This generates patterns for 2, 3, 4, ... max_words word spans.
    """
    patterns: list[tuple[str, ...]] = []
    for num_words in range(2, max_words + 1):
        # Pattern: start, (middle repeated n-2 times), end
        middle_count = num_words - 2
        pattern = (start,) + (middle,) * middle_count + (end,)
        patterns.append(pattern)
    return patterns


def get_tag_coalescing_patterns() -> list[tuple[str, ...]]:
    """
    Return word coalescing patterns for template tags and HTML comments.

    These patterns are used by the word splitter to keep multi-word tag
    constructs together during line wrapping.
    """
    return [
        # Paired Jinja/Markdoc tags: {% tag %}{% /tag %} (with optional space between)
        # This handles empty fields like {% field %}{% /field %}
        # Must come before single tag patterns so it matches first
        (
            rf".*{JINJA_TAG_CLOSE_RE}",
            rf"{JINJA_TAG_OPEN_RE}\s*/.*{JINJA_TAG_CLOSE_RE}",
        ),
        # Paired HTML comment tags: <!-- tag --><!-- /tag -->
        (
            rf".*{HTML_COMMENT_CLOSE_RE}",
            rf"{HTML_COMMENT_OPEN_RE}\s*/.*{HTML_COMMENT_CLOSE_RE}",
        ),
        # HTML comments: <!-- comment text -->
        # Keep inline comments together, don't force to separate lines
        *generate_coalescing_patterns(
            start=rf"{HTML_COMMENT_OPEN_RE}.*",
            end=rf".*{HTML_COMMENT_CLOSE_RE}",
            middle=r".+",
        ),
        # Template tags {% ... %} (Markdoc/Jinja/Nunjucks)
        *generate_coalescing_patterns(
            start=JINJA_TAG_OPEN_RE,
            end=rf".*{JINJA_TAG_CLOSE_RE}",
            middle=r".+",
        ),
        # Template comments {# ... #} (Jinja/Nunjucks)
        *generate_coalescing_patterns(
            start=JINJA_COMMENT_OPEN_RE,
            end=rf".*{JINJA_COMMENT_CLOSE_RE}",
            middle=r".+",
        ),
        # Template variables {{ ... }} (Jinja/Nunjucks)
        *generate_coalescing_patterns(
            start=JINJA_VAR_OPEN_RE,
            end=rf".*{JINJA_VAR_CLOSE_RE}",
            middle=r".+",
        ),
    ]


def line_ends_with_tag(line: str) -> bool:
    """Check if a line ends with a Jinja/Markdoc tag or HTML comment."""
    stripped = line.rstrip()
    if not stripped:
        return False
    # Check for Jinja-style tags
    if (
        stripped.endswith(JINJA_TAG_CLOSE)
        or stripped.endswith(JINJA_COMMENT_CLOSE)
        or stripped.endswith(JINJA_VAR_CLOSE)
    ):
        return True
    # Check for HTML comments
    if stripped.endswith(HTML_COMMENT_CLOSE):
        return True
    return False


def line_starts_with_tag(line: str) -> bool:
    """Check if a line starts with a Jinja/Markdoc tag or HTML comment."""
    stripped = line.lstrip()
    if not stripped:
        return False
    # Check for Jinja-style tags
    if (
        stripped.startswith(JINJA_TAG_OPEN)
        or stripped.startswith(JINJA_COMMENT_OPEN)
        or stripped.startswith(JINJA_VAR_OPEN)
    ):
        return True
    # Check for HTML comments
    if stripped.startswith(HTML_COMMENT_OPEN):
        return True
    return False


def add_tag_newline_handling(base_wrapper: LineWrapper) -> LineWrapper:
    """
    Augments a LineWrapper to preserve newlines around Jinja/Markdoc tags
    and HTML comments.

    When a line ends with a tag or the next line starts with a tag,
    the newline between them is preserved rather than being normalized
    away during text wrapping.

    This enables compatibility with Markdoc, Markform, and similar systems
    that use block-level tags like `{% field %}...{% /field %}`.

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
        # If no newlines, nothing to preserve
        if "\n" not in text:
            return base_wrapper(text, initial_indent, subsequent_indent)

        lines = text.split("\n")

        # If only one line after split, nothing to preserve
        if len(lines) <= 1:
            return base_wrapper(text, initial_indent, subsequent_indent)

        # Check if there are any tags in the text - only apply block content
        # heuristics when tags are present to avoid changing normal markdown behavior
        has_tags = any(line_ends_with_tag(line) or line_starts_with_tag(line) for line in lines)

        # Group lines into segments that should be wrapped together
        # A new segment starts when:
        # - The previous line ends with a tag
        # - The current line starts with a tag
        # - (Only if tags present) The current line is block content (table/list)
        # - (Only if tags present) The previous line is block content
        segments: list[str] = []
        current_segment_lines: list[str] = []

        for i, line in enumerate(lines):
            is_first_line = i == 0
            prev_ends_with_tag = not is_first_line and line_ends_with_tag(lines[i - 1])
            curr_starts_with_tag = line_starts_with_tag(line)

            # Block content heuristics only apply when tags are present
            curr_is_block = has_tags and line_is_block_content(line)
            prev_is_block = has_tags and not is_first_line and line_is_block_content(lines[i - 1])

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
            return base_wrapper(text, initial_indent, subsequent_indent)

        # Wrap each segment separately
        wrapped_segments: list[str] = []
        for i, segment in enumerate(segments):
            is_first = i == 0
            cur_initial_indent = initial_indent if is_first else subsequent_indent
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
            curr_is_tag = (
                line_starts_with_tag(curr_segment.split("\n")[0]) if curr_segment else False
            )

            # Ensure exactly one blank line between tag and block content
            if (prev_is_tag and curr_is_block) or (prev_is_block and curr_is_tag):
                # Add blank line separator
                result_parts.append("")  # Empty string creates blank line when joined
                result_parts.append(wrapped)
            else:
                result_parts.append(wrapped)

        result = "\n".join(result_parts)

        # Post-process: remove incorrect indentation from closing tags.
        # The Markdown parser may indent closing tags due to lazy continuation.
        result = _fix_tag_indentation(result)

        return result

    return enhanced_wrapper


def _fix_tag_indentation(text: str) -> str:
    """
    Remove incorrect indentation from closing tags.

    When a closing tag follows a list item, the Markdown parser may indent it
    as list continuation. This function strips leading whitespace from lines
    that are closing tags (start with {% /, {# /, {{ /, or <!-- /).
    """
    lines = text.split("\n")
    fixed_lines: list[str] = []

    for line in lines:
        stripped = line.lstrip()
        # Check if this is a closing tag that got incorrectly indented
        if (
            stripped.startswith("{% /")
            or stripped.startswith("{# /")
            or stripped.startswith("{{ /")
            or stripped.startswith("<!-- /")
        ):
            # Strip the indentation
            fixed_lines.append(stripped)
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)
