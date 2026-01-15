"""
Atomic pattern definitions for constructs that should not be broken during wrapping.

Each AtomicPattern defines a regex for a specific type of construct (code span, link,
template tag, etc.) that should be kept together as a single token during line wrapping.

This module also defines the canonical delimiter constants for all supported tag formats.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Delimiter constants for template tags and comments.
# Raw delimiters
JINJA_TAG_OPEN = "{%"
JINJA_TAG_CLOSE = "%}"
JINJA_COMMENT_OPEN = "{#"
JINJA_COMMENT_CLOSE = "#}"
JINJA_VAR_OPEN = "{{"
JINJA_VAR_CLOSE = "}}"
HTML_COMMENT_OPEN = "<!--"
HTML_COMMENT_CLOSE = "-->"

# Regex-escaped delimiters
JINJA_TAG_OPEN_RE = r"\{%"
JINJA_TAG_CLOSE_RE = r"%\}"
JINJA_COMMENT_OPEN_RE = r"\{#"
JINJA_COMMENT_CLOSE_RE = r"#\}"
JINJA_VAR_OPEN_RE = r"\{\{"
JINJA_VAR_CLOSE_RE = r"\}\}"
HTML_COMMENT_OPEN_RE = r"<!--"
HTML_COMMENT_CLOSE_RE = r"-->"


@dataclass(frozen=True)
class AtomicPattern:
    """
    Defines a regex pattern for an atomic construct that should not be broken.
    """

    name: str
    pattern: str


def _make_paired_pattern(open_re: str, close_re: str, middle_char: str) -> str:
    """
    Generate a paired tag pattern: opening + closing kept together.

    Uses `(?!\\s*/)` lookahead to ensure first tag is opening (not closing).
    The middle_char is the character to exclude from middle content.
    """
    return (
        rf"{open_re}(?!\s*/)[^{middle_char}]*{close_re}"
        rf"\s*"
        rf"{open_re}\s*/[^{middle_char}]*{close_re}"
    )


def _make_single_tag_pattern(open_re: str, close_re: str) -> str:
    """Generate a single tag pattern: opening...closing."""
    return rf"{open_re}.*?{close_re}"


# Inline code spans with backticks (handles multi-backtick like ``code``)
INLINE_CODE_SPAN = AtomicPattern(
    name="inline_code_span",
    pattern=r"(`+)(?:(?!\1).)+\1",
)

# Markdown links: [text](url) or [text][ref] or [text]
MARKDOWN_LINK = AtomicPattern(
    name="markdown_link",
    pattern=r"\[[^\]]*\](?:\([^)]*\)|\[[^\]]*\])?",
)

# Jinja/Markdoc template tags: {% tag %}, {% /tag %}
SINGLE_JINJA_TAG = AtomicPattern(
    name="single_jinja_tag",
    pattern=_make_single_tag_pattern(JINJA_TAG_OPEN_RE, JINJA_TAG_CLOSE_RE),
)

PAIRED_JINJA_TAG = AtomicPattern(
    name="paired_jinja_tag",
    pattern=_make_paired_pattern(JINJA_TAG_OPEN_RE, JINJA_TAG_CLOSE_RE, "%"),
)

# Jinja comments: {# comment #}
SINGLE_JINJA_COMMENT = AtomicPattern(
    name="single_jinja_comment",
    pattern=_make_single_tag_pattern(JINJA_COMMENT_OPEN_RE, JINJA_COMMENT_CLOSE_RE),
)

PAIRED_JINJA_COMMENT = AtomicPattern(
    name="paired_jinja_comment",
    pattern=_make_paired_pattern(JINJA_COMMENT_OPEN_RE, JINJA_COMMENT_CLOSE_RE, "#"),
)

# Jinja variables: {{ variable }}
SINGLE_JINJA_VAR = AtomicPattern(
    name="single_jinja_var",
    pattern=_make_single_tag_pattern(JINJA_VAR_OPEN_RE, JINJA_VAR_CLOSE_RE),
)

PAIRED_JINJA_VAR = AtomicPattern(
    name="paired_jinja_var",
    pattern=_make_paired_pattern(JINJA_VAR_OPEN_RE, JINJA_VAR_CLOSE_RE, "}"),
)

# HTML comments: <!-- comment -->
SINGLE_HTML_COMMENT = AtomicPattern(
    name="single_html_comment",
    pattern=_make_single_tag_pattern(HTML_COMMENT_OPEN_RE, HTML_COMMENT_CLOSE_RE),
)

PAIRED_HTML_COMMENT = AtomicPattern(
    name="paired_html_comment",
    pattern=(
        r"<!--(?!\s*/)[^-]*(?:-[^-]+)*-->"
        r"\s*"
        r"<!--\s*/[^-]*(?:-[^-]+)*-->"
    ),
)

# HTML/XML tags: <tag>, </tag>
HTML_OPEN_TAG = AtomicPattern(
    name="html_open_tag",
    pattern=r"<[a-zA-Z][^>]*>",
)

HTML_CLOSE_TAG = AtomicPattern(
    name="html_close_tag",
    pattern=r"</[a-zA-Z][^>]*>",
)

# All patterns in priority order (more specific patterns first).
# Paired tag patterns must come before single tag patterns to match correctly.
ATOMIC_PATTERNS: tuple[AtomicPattern, ...] = (
    INLINE_CODE_SPAN,
    MARKDOWN_LINK,
    # Paired tags must come before single tags
    PAIRED_JINJA_TAG,
    PAIRED_JINJA_COMMENT,
    PAIRED_JINJA_VAR,
    PAIRED_HTML_COMMENT,
    # Single tags
    SINGLE_JINJA_TAG,
    SINGLE_JINJA_COMMENT,
    SINGLE_JINJA_VAR,
    SINGLE_HTML_COMMENT,
    # HTML tags
    HTML_OPEN_TAG,
    HTML_CLOSE_TAG,
)

# Compiled regex combining all patterns with alternation
ATOMIC_CONSTRUCT_PATTERN: re.Pattern[str] = re.compile(
    "|".join(p.pattern for p in ATOMIC_PATTERNS),
    re.DOTALL,
)
