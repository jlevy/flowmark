"""
Atomic pattern definitions for constructs that should not be broken during wrapping.

Each AtomicPattern defines a regex for a specific type of construct (code span, link,
template tag, etc.) that should be kept together as a single token during line wrapping.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AtomicPattern:
    """
    Defines a regex pattern for an atomic construct that should not be broken.

    For delimiter-based patterns (tags, comments), `open_delim`/`close_delim` store
    the raw delimiters and `open_re`/`close_re` store regex-escaped versions.
    For non-delimiter patterns, these are empty strings.
    """

    name: str
    pattern: str
    open_delim: str
    close_delim: str
    open_re: str
    close_re: str


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


# Inline code spans with backticks (handles multi-backtick like ``code``)
INLINE_CODE_SPAN = AtomicPattern(
    name="inline_code_span",
    pattern=r"(`+)(?:(?!\1).)+\1",
    open_delim="",
    close_delim="",
    open_re="",
    close_re="",
)

# Markdown links: [text](url) or [text][ref] or [text]
MARKDOWN_LINK = AtomicPattern(
    name="markdown_link",
    pattern=r"\[[^\]]*\](?:\([^)]*\)|\[[^\]]*\])?",
    open_delim="",
    close_delim="",
    open_re="",
    close_re="",
)

# Jinja/Markdoc template tags: {% tag %}, {% /tag %}
SINGLE_JINJA_TAG = AtomicPattern(
    name="single_jinja_tag",
    pattern=r"\{%.*?%\}",
    open_delim="{%",
    close_delim="%}",
    open_re=r"\{%",
    close_re=r"%\}",
)

PAIRED_JINJA_TAG = AtomicPattern(
    name="paired_jinja_tag",
    pattern=_make_paired_pattern(r"\{%", r"%\}", "%"),
    open_delim="{%",
    close_delim="%}",
    open_re=r"\{%",
    close_re=r"%\}",
)

# Jinja comments: {# comment #}
SINGLE_JINJA_COMMENT = AtomicPattern(
    name="single_jinja_comment",
    pattern=r"\{#.*?#\}",
    open_delim="{#",
    close_delim="#}",
    open_re=r"\{#",
    close_re=r"#\}",
)

PAIRED_JINJA_COMMENT = AtomicPattern(
    name="paired_jinja_comment",
    pattern=_make_paired_pattern(r"\{#", r"#\}", "#"),
    open_delim="{#",
    close_delim="#}",
    open_re=r"\{#",
    close_re=r"#\}",
)

# Jinja variables: {{ variable }}
SINGLE_JINJA_VAR = AtomicPattern(
    name="single_jinja_var",
    pattern=r"\{\{.*?\}\}",
    open_delim="{{",
    close_delim="}}",
    open_re=r"\{\{",
    close_re=r"\}\}",
)

PAIRED_JINJA_VAR = AtomicPattern(
    name="paired_jinja_var",
    pattern=_make_paired_pattern(r"\{\{", r"\}\}", "}"),
    open_delim="{{",
    close_delim="}}",
    open_re=r"\{\{",
    close_re=r"\}\}",
)

# HTML comments: <!-- comment -->
SINGLE_HTML_COMMENT = AtomicPattern(
    name="single_html_comment",
    pattern=r"<!--.*?-->",
    open_delim="<!--",
    close_delim="-->",
    open_re=r"<!--",
    close_re=r"-->",
)

PAIRED_HTML_COMMENT = AtomicPattern(
    name="paired_html_comment",
    pattern=(
        r"<!--(?!\s*/)[^-]*(?:-[^-]+)*-->"
        r"\s*"
        r"<!--\s*/[^-]*(?:-[^-]+)*-->"
    ),
    open_delim="<!--",
    close_delim="-->",
    open_re=r"<!--",
    close_re=r"-->",
)

# HTML/XML tags: <tag>, </tag>
HTML_OPEN_TAG = AtomicPattern(
    name="html_open_tag",
    pattern=r"<[a-zA-Z][^>]*>",
    open_delim="",
    close_delim="",
    open_re="",
    close_re="",
)

HTML_CLOSE_TAG = AtomicPattern(
    name="html_close_tag",
    pattern=r"</[a-zA-Z][^>]*>",
    open_delim="",
    close_delim="",
    open_re="",
    close_re="",
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
