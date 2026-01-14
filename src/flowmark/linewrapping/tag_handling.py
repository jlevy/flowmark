"""
Tag handling for Jinja/Markdoc tags and HTML comments.

This module provides detection and handling of template tags used by systems like
Markdoc, Markform, Jinja, Nunjucks, and WordPress Gutenberg.

The main concerns are:
1. Detecting tag boundaries to preserve newlines around them
2. Providing constants for tag delimiters used in word splitting patterns
"""

from __future__ import annotations

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

        # Group lines into segments that should be wrapped together
        # A new segment starts when:
        # - The previous line ends with a tag
        # - The current line starts with a tag
        segments: list[str] = []
        current_segment_lines: list[str] = []

        for i, line in enumerate(lines):
            is_first_line = i == 0
            prev_ends_with_tag = not is_first_line and line_ends_with_tag(lines[i - 1])
            curr_starts_with_tag = line_starts_with_tag(line)

            # Start a new segment if there's a tag boundary
            if prev_ends_with_tag or curr_starts_with_tag:
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

        # Wrap each segment separately and rejoin with newlines
        wrapped_segments: list[str] = []
        for i, segment in enumerate(segments):
            is_first = i == 0
            cur_initial_indent = initial_indent if is_first else subsequent_indent
            wrapped = base_wrapper(segment, cur_initial_indent, subsequent_indent)
            wrapped_segments.append(wrapped)

        return "\n".join(wrapped_segments)

    return enhanced_wrapper
