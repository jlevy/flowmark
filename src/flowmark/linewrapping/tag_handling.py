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
from enum import Enum

from flowmark.linewrapping.block_heuristics import line_is_block_content
from flowmark.linewrapping.protocols import LineWrapper


class TagWrapping(str, Enum):
    """
    Controls how template tags are handled during line wrapping.

    - `atomic`: Tags are never broken across lines (default). Long tags placed
      on their own line if they don't fit.
    - `wrap`: Tags can be wrapped like normal text (legacy behavior).
    """

    atomic = "atomic"
    wrap = "wrap"


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


# Pattern to match complete template tags (for protecting content inside tags).
# These tags can span multiple lines and may contain quotes in attribute values.
# Uses DOTALL so . matches newlines within tags.
# Note: In VERBOSE mode, # starts a comment, so we use [#] for literal hash.
TEMPLATE_TAG_PATTERN: re.Pattern[str] = re.compile(
    r"""
    \{%.*?%\}             # Jinja/Markdoc template tags
    | \{[#].*?[#]\}       # Jinja comments (use [#] to avoid VERBOSE comment)
    | \{\{.*?\}\}         # Jinja variables
    | <!--.*?-->          # HTML comments
    """,
    re.VERBOSE | re.DOTALL,
)

# Placeholder format for atomic tag wrapping. Uses null byte prefix/suffix to
# avoid conflicts with real content.
_PLACEHOLDER_PREFIX = "\x00TAG"
_PLACEHOLDER_SUFFIX = "\x00"

# Pattern to match paired tags like {% tag %}{% /tag %} that should stay together.
# Allows optional whitespace between tags (added by normalize_adjacent_tags).
PAIRED_TAGS_PATTERN: re.Pattern[str] = re.compile(
    r"""
    (\{%[^%]*%\})\s*(\{%\s*/[^%]*%\})       # {% tag %}{% /tag %}
    | (<!--[^-]*-->)\s*(<!--\s*/[^-]*-->)   # <!-- tag --><!-- /tag -->
    | (\{[#][^#]*[#]\})\s*(\{[#]\s*/[^#]*[#]\})  # {# tag #}{# /tag #}
    | (\{\{[^}]*\}\})\s*(\{\{\s*/[^}]*\}\})  # {{ tag }}{{ /tag }}
    """,
    re.VERBOSE | re.DOTALL,
)


def extract_tags_atomic(text: str) -> tuple[dict[int, str], str]:
    """
    Extract all template tags from text, replacing them with placeholders.

    In atomic mode, tags are replaced with short placeholders so the wrapping
    algorithm treats them as single words. Each tag is extracted individually
    (not paired) so that opening and closing tags can be placed on separate
    lines when needed for line width or Markdoc parser compatibility.

    Returns a tuple of (tag_map, text_with_placeholders) where tag_map maps
    placeholder indices to original tag strings.
    """
    tag_map: dict[int, str] = {}
    placeholder_idx = 0

    def make_placeholder(idx: int) -> str:
        return f"{_PLACEHOLDER_PREFIX}{idx}{_PLACEHOLDER_SUFFIX}"

    def replace_tag(match: re.Match[str]) -> str:
        nonlocal placeholder_idx
        tag = match.group(0)
        tag_map[placeholder_idx] = tag
        placeholder = make_placeholder(placeholder_idx)
        placeholder_idx += 1
        return placeholder

    text = TEMPLATE_TAG_PATTERN.sub(replace_tag, text)

    return tag_map, text


def restore_tags_atomic(text: str, tag_map: dict[int, str]) -> str:
    """
    Restore original tags from placeholders.

    This is the inverse of `extract_tags_atomic()`.
    """
    for idx, tag in tag_map.items():
        placeholder = f"{_PLACEHOLDER_PREFIX}{idx}{_PLACEHOLDER_SUFFIX}"
        text = text.replace(placeholder, tag)
    return text


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


def get_tag_coalescing_patterns(max_words: int = MAX_TAG_WORDS) -> list[tuple[str, ...]]:
    """
    Return word coalescing patterns for template tags and HTML comments.

    These patterns are used by the word splitter to keep multi-word tag
    constructs together during line wrapping.

    The `max_words` parameter controls how many words can be coalesced.
    For atomic mode, use a high value (e.g., 128) to prevent tag breaks.
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
            max_words=max_words,
        ),
        # Template tags {% ... %} (Markdoc/Jinja/Nunjucks)
        *generate_coalescing_patterns(
            start=JINJA_TAG_OPEN_RE,
            end=rf".*{JINJA_TAG_CLOSE_RE}",
            middle=r".+",
            max_words=max_words,
        ),
        # Template comments {# ... #} (Jinja/Nunjucks)
        *generate_coalescing_patterns(
            start=JINJA_COMMENT_OPEN_RE,
            end=rf".*{JINJA_COMMENT_CLOSE_RE}",
            middle=r".+",
            max_words=max_words,
        ),
        # Template variables {{ ... }} (Jinja/Nunjucks)
        *generate_coalescing_patterns(
            start=JINJA_VAR_OPEN_RE,
            end=rf".*{JINJA_VAR_CLOSE_RE}",
            middle=r".+",
            max_words=max_words,
        ),
    ]


def _is_tag_only_line(line: str) -> bool:
    """
    Check if a line contains only a tag (opening or closing), not inline tags in content.

    A tag-only line starts with a tag delimiter and ends with a tag delimiter,
    with no substantial non-tag content. This distinguishes:
    - `{% field %}` (tag-only line)
    - `- [ ] Item {% #id %}` (content with inline tag - NOT tag-only)
    """
    stripped = line.strip()
    if not stripped:
        return False

    # Check if it starts with a tag
    starts_tag = (
        stripped.startswith(JINJA_TAG_OPEN)
        or stripped.startswith(JINJA_COMMENT_OPEN)
        or stripped.startswith(JINJA_VAR_OPEN)
        or stripped.startswith(HTML_COMMENT_OPEN)
    )

    # Check if it ends with a tag
    ends_tag = (
        stripped.endswith(JINJA_TAG_CLOSE)
        or stripped.endswith(JINJA_COMMENT_CLOSE)
        or stripped.endswith(JINJA_VAR_CLOSE)
        or stripped.endswith(HTML_COMMENT_CLOSE)
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


def add_tag_newline_handling(
    base_wrapper: LineWrapper,
    tags: TagWrapping = TagWrapping.atomic,  # pyright: ignore[reportUnusedParameter]
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
            result = base_wrapper(text, initial_indent, subsequent_indent)
            result = _fix_multiline_opening_tag_with_closing(result)
            return result

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
    rf"{JINJA_TAG_CLOSE_RE}\s*(?P<closing_tag>{JINJA_TAG_OPEN_RE}\s*/)|"  # %}{% /
    rf"{JINJA_COMMENT_CLOSE_RE}\s*(?P<closing_comment>{JINJA_COMMENT_OPEN_RE}\s*/)|"  # #}{# /
    rf"{JINJA_VAR_CLOSE_RE}\s*(?P<closing_var>{JINJA_VAR_OPEN_RE}\s*/)|"  # }}{{ /
    rf"{HTML_COMMENT_CLOSE_RE}\s*(?P<closing_html>{HTML_COMMENT_OPEN_RE}\s*/)"  # --><!-- /
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
            stripped.startswith(JINJA_TAG_OPEN)
            or stripped.startswith(JINJA_COMMENT_OPEN)
            or stripped.startswith(JINJA_VAR_OPEN)
            or stripped.startswith(HTML_COMMENT_OPEN)
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
