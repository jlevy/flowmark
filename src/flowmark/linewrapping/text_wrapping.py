from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from typing import Protocol

from flowmark.linewrapping.tag_handling import (
    TagWrapping,
    denormalize_adjacent_tags,
    normalize_adjacent_tags,
)

DEFAULT_LEN_FUNCTION = len
"""
Default length function to use for wrapping.
By default this is just character length, but this can be overridden, for example
to use a smarter function that does not count ANSI escape codes.
"""


class WordSplitter(Protocol):
    def __call__(self, text: str) -> list[str]: ...


def simple_word_splitter(text: str) -> list[str]:
    """
    Split words on whitespace. This is like Python's normal `textwrap`.
    """
    return text.split()


# Placeholder format for atomic construct extraction. Uses null byte prefix/suffix
# to avoid conflicts with real content.
_PLACEHOLDER_PREFIX = "\x00AC"
_PLACEHOLDER_SUFFIX = "\x00"


@dataclass(frozen=True)
class AtomicPattern:
    """
    Defines a regex pattern for an atomic construct that should not be broken.

    Each pattern matches a specific type of construct (code span, link, tag, etc.)
    that should be kept together as a single token during line wrapping.
    """

    name: str
    pattern: str


# Atomic construct patterns. Order matters: more specific patterns come first.
# Paired tag patterns must come before single tag patterns to match correctly.

INLINE_CODE_SPAN = AtomicPattern(
    name="inline_code_span",
    pattern=r"(`+)(?:(?!\1).)+\1",  # Handles multi-backtick like ``code``
)

MARKDOWN_LINK = AtomicPattern(
    name="markdown_link",
    pattern=r"\[[^\]]*\](?:\([^)]*\)|\[[^\]]*\])?",  # [text](url) or [text][ref]
)

# Paired template tags: opening + closing kept together (e.g., {% field %}{% /field %})
# Uses (?!\s*/) lookahead to ensure first tag is not a closing tag
PAIRED_JINJA_TAG = AtomicPattern(
    name="paired_jinja_tag",
    pattern=r"\{%(?!\s*/)[^%]*%\}\s*\{%\s*/[^%]*%\}",
)

PAIRED_JINJA_COMMENT = AtomicPattern(
    name="paired_jinja_comment",
    pattern=r"\{[#](?!\s*/)[^#]*[#]\}\s*\{[#]\s*/[^#]*[#]\}",
)

PAIRED_JINJA_VAR = AtomicPattern(
    name="paired_jinja_var",
    pattern=r"\{\{(?!\s*/)[^}]*\}\}\s*\{\{\s*/[^}]*\}\}",
)

PAIRED_HTML_COMMENT = AtomicPattern(
    name="paired_html_comment",
    pattern=r"<!--(?!\s*/)[^-]*(?:-[^-]+)*-->\s*<!--\s*/[^-]*(?:-[^-]+)*-->",
)

# Single template tags
SINGLE_JINJA_TAG = AtomicPattern(
    name="single_jinja_tag",
    pattern=r"\{%.*?%\}",
)

SINGLE_JINJA_COMMENT = AtomicPattern(
    name="single_jinja_comment",
    pattern=r"\{[#].*?[#]\}",
)

SINGLE_JINJA_VAR = AtomicPattern(
    name="single_jinja_var",
    pattern=r"\{\{.*?\}\}",
)

SINGLE_HTML_COMMENT = AtomicPattern(
    name="single_html_comment",
    pattern=r"<!--.*?-->",
)

# HTML/XML tags
HTML_OPEN_TAG = AtomicPattern(
    name="html_open_tag",
    pattern=r"<[a-zA-Z][^>]*>",
)

HTML_CLOSE_TAG = AtomicPattern(
    name="html_close_tag",
    pattern=r"</[a-zA-Z][^>]*>",
)

# All patterns in priority order (more specific patterns first)
_ATOMIC_PATTERNS: tuple[AtomicPattern, ...] = (
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
_ATOMIC_CONSTRUCT_PATTERN: re.Pattern[str] = re.compile(
    "|".join(p.pattern for p in _ATOMIC_PATTERNS),
    re.DOTALL,
)


def _extract_atomic_constructs(text: str) -> tuple[dict[int, str], str]:
    """
    Extract all atomic constructs from text, replacing them with placeholders.

    This uses a single regex pass to find all constructs that should be treated
    as indivisible tokens (template tags, code spans, markdown links, HTML tags).

    Returns (construct_map, text_with_placeholders) where construct_map maps
    placeholder indices to original strings.
    """
    construct_map: dict[int, str] = {}
    placeholder_idx = 0

    def replace_construct(match: re.Match[str]) -> str:
        nonlocal placeholder_idx
        construct = match.group(0)
        construct_map[placeholder_idx] = construct
        placeholder = f"{_PLACEHOLDER_PREFIX}{placeholder_idx}{_PLACEHOLDER_SUFFIX}"
        placeholder_idx += 1
        return placeholder

    text_with_placeholders = _ATOMIC_CONSTRUCT_PATTERN.sub(replace_construct, text)
    return construct_map, text_with_placeholders


def _restore_atomic_constructs(tokens: list[str], construct_map: dict[int, str]) -> list[str]:
    """
    Restore original constructs from placeholders in token list.
    """
    result: list[str] = []
    for token in tokens:
        for idx, construct in construct_map.items():
            placeholder = f"{_PLACEHOLDER_PREFIX}{idx}{_PLACEHOLDER_SUFFIX}"
            token = token.replace(placeholder, construct)
        result.append(token)
    return result


class _HtmlMdWordSplitter:
    """
    Word splitter for Markdown/HTML that keeps certain constructs together.

    This handles LINE WRAPPING, not Markdown parsing. The distinction matters:
    - Markdown parsing (handled by Marko): Interprets code spans, applies escaping
      rules, converts line breaks to spaces per CommonMark spec
    - Line wrapping (this code): Decides where to break lines in source text

    Uses a single-pass regex extraction approach:
    1. Extract all atomic constructs (tags, code spans, links) with placeholders
    2. Split on whitespace (placeholders become single "words")
    3. Restore original constructs

    When `atomic_tags=True`, all constructs are treated as indivisible tokens.
    When `atomic_tags=False`, only basic constructs are kept together.
    """

    atomic_tags: bool

    def __init__(self, atomic_tags: bool = False):
        self.atomic_tags = atomic_tags

    def __call__(self, text: str) -> list[str]:
        # Normalize adjacent tags to ensure proper tokenization
        text = normalize_adjacent_tags(text)

        if self.atomic_tags:
            return self._split_with_extraction(text)
        else:
            return self._split_with_extraction(text)

    def _split_with_extraction(self, text: str) -> list[str]:
        """
        Split using single-pass regex extraction.

        1. Extract all atomic constructs and replace with placeholders
        2. Split on whitespace (placeholders are single tokens)
        3. Restore original constructs
        """
        construct_map, text_with_placeholders = _extract_atomic_constructs(text)
        tokens = text_with_placeholders.split()
        return _restore_atomic_constructs(tokens, construct_map)


@cache
def get_html_md_word_splitter(atomic_tags: bool) -> WordSplitter:
    """
    Get cached word splitter instance. Thread-safe via @cache decorator.
    Avoids re-compiling regex patterns on every call.
    """
    return _HtmlMdWordSplitter(atomic_tags=atomic_tags)


# Pattern to identify words that need escaping if they start a wrapped markdown line.
# Matches list markers (*, +, -) bare or before a space (but not before a letter for
# example), blockquotes (> ), headings (#, ##, etc.).
_md_specials_pat = re.compile(r"^([-*+>]|#+)$")

# Separate pattern to specifically find the numbered list cases for targeted escaping
_md_numeral_pat = re.compile(r"^[0-9]+[.)]$")


def markdown_escape_word(word: str) -> str:
    """
    Prepends a backslash to a word if it matches markdown patterns
    that need escaping at the start of a wrapped line.
    For numbered lists (e.g., "1.", "1)"), inserts the backslash before the dot/paren.
    """
    if _md_numeral_pat.match(word):
        # Insert backslash before the `.` or `)`
        return word[:-1] + "\\" + word[-1]
    elif _md_specials_pat.match(word):
        return "\\" + word
    return word


def wrap_paragraph_lines(
    text: str,
    width: int,
    initial_column: int = 0,
    subsequent_offset: int = 0,
    replace_whitespace: bool = True,
    drop_whitespace: bool = True,
    splitter: WordSplitter | None = None,
    len_fn: Callable[[str], int] = DEFAULT_LEN_FUNCTION,
    is_markdown: bool = False,
    tags: TagWrapping = TagWrapping.atomic,
) -> list[str]:
    r"""
    Wrap a single paragraph of text, returning a list of wrapped lines.
    Rewritten to simplify and generalize Python's textwrap.py.

    Set `is_markdown` to True when wrapping markdown text to enable Markdown mode.

    This automatically escapes special markdown characters at the start of wrapped
    lines. It also will then correctly preserve explicit hard Markdown line breaks, i.e.
    "\\\n" (backslash-newline) or "  \n" (two spaces followed by newline) at the
    end of the line. Hard line breaks are normalized to always use "\\\n" as the line
    break.

    The `tags` parameter controls template tag handling:
    - `atomic`: Tags are treated as indivisible tokens (never broken across lines)
    - `wrap`: Tags can wrap like normal text (legacy behavior with coalescing limits)
    """
    lines: list[str] = []

    # Handle width <= 0 as "no wrapping".
    if width <= 0:
        if replace_whitespace:
            text = re.sub(r"\s+", " ", text)
        if drop_whitespace:
            text = text.strip()
        return [text] if text else []

    if replace_whitespace:
        text = re.sub(r"\s+", " ", text)

    # Use provided splitter or get cached one based on tags mode
    if splitter is None:
        splitter = get_html_md_word_splitter(atomic_tags=(tags == TagWrapping.atomic))

    words = splitter(text)

    current_line: list[str] = []
    current_width = initial_column
    first_line = True

    # Walk through words, breaking them into lines.
    for word in words:
        word_width = len_fn(word)

        space_width = 1 if current_line else 0
        if current_width + word_width + space_width <= width:
            # Add word to current line.
            current_line.append(word)
            current_width += word_width + space_width
        else:
            # Start a new line.
            if current_line:
                line = " ".join(current_line)
                if drop_whitespace:
                    line = line.strip()
                lines.append(line)
                first_line = False

            # Check if word needs escaping at the start of this wrapped line.
            escaped_word = word
            if is_markdown and not first_line:
                escaped_word = markdown_escape_word(word)

            # Recalculate width after potential escaping for the new line.
            escaped_word_width = len_fn(escaped_word)

            # Start the new line with the (potentially escaped) word
            current_line = [escaped_word]
            current_width = subsequent_offset + escaped_word_width

    # Add the last line if necessary.
    if current_line:
        line = " ".join(current_line)
        if drop_whitespace:
            line = line.strip()
        lines.append(line)

    return lines


def wrap_paragraph(
    text: str,
    width: int,
    initial_indent: str = "",
    subsequent_indent: str = "",
    initial_column: int = 0,
    replace_whitespace: bool = True,
    drop_whitespace: bool = True,
    word_splitter: WordSplitter | None = None,
    len_fn: Callable[[str], int] = DEFAULT_LEN_FUNCTION,
    is_markdown: bool = False,
    tags: TagWrapping = TagWrapping.atomic,
) -> str:
    """
    Wrap lines of a single paragraph of plain text, returning a new string.

    The `tags` parameter controls template tag handling:
    - `atomic`: Tags are treated as indivisible tokens (never broken across lines)
    - `wrap`: Tags can wrap like normal text (legacy behavior with coalescing limits)
    """
    lines = wrap_paragraph_lines(
        text=text,
        width=width,
        replace_whitespace=replace_whitespace,
        drop_whitespace=drop_whitespace,
        splitter=word_splitter,
        initial_column=initial_column + len_fn(initial_indent),
        subsequent_offset=len_fn(subsequent_indent),
        len_fn=len_fn,
        is_markdown=is_markdown,
        tags=tags,
    )
    # Now insert indents on first and subsequent lines, if needed.
    if initial_indent and initial_column == 0 and len(lines) > 0:
        lines[0] = initial_indent + lines[0]
    if subsequent_indent and len(lines) > 1:
        lines[1:] = [subsequent_indent + line for line in lines[1:]]
    result = "\n".join(lines)

    # Restore original adjacency for paired tags (remove spaces added during tokenization)
    return denormalize_adjacent_tags(result)
