from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from typing import Protocol

from flowmark.linewrapping.atomic_patterns import ATOMIC_PATTERNS, iter_atomic_words
from flowmark.linewrapping.tag_handling import (
    denormalize_adjacent_tags,
    normalize_adjacent_tags,
)
from flowmark.preservation.bridge import InvalidTokenError, ProtectedSource
from flowmark.preservation.model import ProtectedRegion, RegionForm

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


class _HtmlMdWordSplitter:
    """
    Word splitter for Markdown/HTML that keeps certain constructs together.

    This handles LINE WRAPPING, not Markdown parsing. The distinction matters:
    - Markdown parsing (handled by Marko): Interprets code spans, applies escaping
      rules, converts line breaks to spaces per CommonMark spec
    - Line wrapping (this code): Decides where to break lines in source text

    Splits on whitespace via `iter_atomic_words`, which treats all atomic constructs
    (template tags, code spans, markdown links, HTML tags) as indivisible tokens that are
    never broken across lines.
    """

    def __call__(self, text: str) -> list[str]:
        # Normalize adjacent tags so paired tags tokenize as separate words.
        text = normalize_adjacent_tags(text)
        return [word.text for word in iter_atomic_words(text, ATOMIC_PATTERNS)]


@dataclass(frozen=True, slots=True)
class _WrappingFragment:
    """Plain parser text or one protected inline region inside a wrapping word."""

    text: str
    region: ProtectedRegion | None = None


@dataclass(frozen=True, slots=True)
class _TextMetrics:
    """Widths before the first and after the final authored protected LF."""

    first_width: int
    final_width: int
    has_authored_break: bool


def _protected_token_map(protected: ProtectedSource) -> dict[str, ProtectedRegion]:
    if len(protected.tokens) != len(protected.regions):
        raise InvalidTokenError("protected side table lengths do not match")
    token_map = dict(zip(protected.tokens, protected.regions, strict=True))
    if len(token_map) != len(protected.tokens):
        raise InvalidTokenError("protected side table contains duplicate tokens")
    return token_map


def _wrapping_fragments(
    text: str,
    protected: ProtectedSource,
    token_map: dict[str, ProtectedRegion] | None = None,
) -> tuple[_WrappingFragment, ...]:
    """Split parser text at exact side-table tokens without interpreting their bodies."""
    regions_by_token = _protected_token_map(protected) if token_map is None else token_map
    fragments: list[_WrappingFragment] = []
    position = 0
    while True:
        token_start = text.find(protected.sentinel, position)
        if token_start < 0:
            if position < len(text):
                fragments.append(_WrappingFragment(text[position:]))
            break
        if position < token_start:
            fragments.append(_WrappingFragment(text[position:token_start]))
        sentinel_end = text.find(protected.sentinel, token_start + len(protected.sentinel))
        if sentinel_end < 0:
            raise InvalidTokenError("protected token lost its closing sentinel during wrapping")
        token_end = sentinel_end + len(protected.sentinel)
        token = text[token_start:token_end]
        region = regions_by_token.get(token)
        if region is None:
            raise InvalidTokenError("unknown or malformed protected token during wrapping")
        if region.form is not RegionForm.inline:
            raise InvalidTokenError("opaque block token reached inline wrapping")
        fragments.append(_WrappingFragment(token, region))
        position = token_end
    return tuple(fragments)


def _measure_fragments(
    fragments: tuple[_WrappingFragment, ...],
    len_fn: Callable[[str], int],
) -> _TextMetrics:
    column = 0
    first_width: int | None = None
    has_authored_break = False
    for fragment in fragments:
        if fragment.region is None:
            column += len_fn(fragment.text)
            continue
        widths = fragment.region.logical_widths
        if not widths:
            raise InvalidTokenError("protected inline token has no logical width metadata")
        column += widths[0]
        if len(widths) > 1:
            if first_width is None:
                first_width = column
            has_authored_break = True
            column = widths[-1]
    return _TextMetrics(
        first_width=column if first_width is None else first_width,
        final_width=column,
        has_authored_break=has_authored_break,
    )


def measure_protected_text(
    text: str,
    protected: ProtectedSource,
    len_fn: Callable[[str], int] = DEFAULT_LEN_FUNCTION,
) -> _TextMetrics:
    """Measure parser text using source-side widths for every protected token."""
    return _measure_fragments(_wrapping_fragments(text, protected), len_fn)


def _wrap_protected_words(
    words: list[str],
    *,
    protected: ProtectedSource,
    width: int,
    initial_column: int,
    subsequent_offset: int,
    drop_whitespace: bool,
    len_fn: Callable[[str], int],
    is_markdown: bool,
) -> list[str]:
    """Wrap structured words while protected source controls width and authored LFs."""
    lines: list[str] = []
    current_line: list[str] = []
    current_width = initial_column
    first_line = True
    token_map = _protected_token_map(protected)

    for word in words:
        metrics = _measure_fragments(_wrapping_fragments(word, protected, token_map), len_fn)
        space_width = 1 if current_line else 0
        if current_width + space_width + metrics.first_width <= width:
            current_line.append(word)
            if metrics.has_authored_break:
                current_width = metrics.final_width
                first_line = False
            else:
                current_width += space_width + metrics.final_width
            continue

        if current_line:
            line = " ".join(current_line)
            lines.append(line.strip() if drop_whitespace else line)
            first_line = False

        escaped_word = markdown_escape_word(word) if is_markdown and not first_line else word
        escaped_metrics = _measure_fragments(
            _wrapping_fragments(escaped_word, protected, token_map), len_fn
        )
        current_line = [escaped_word]
        current_width = (
            escaped_metrics.final_width
            if escaped_metrics.has_authored_break
            else subsequent_offset + escaped_metrics.final_width
        )
        if escaped_metrics.has_authored_break:
            first_line = False

    if current_line:
        line = " ".join(current_line)
        lines.append(line.strip() if drop_whitespace else line)
    return lines


@cache
def get_html_md_word_splitter() -> WordSplitter:
    """
    Get cached word splitter instance. Thread-safe via @cache decorator.
    """
    return _HtmlMdWordSplitter()


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
    protected_source: ProtectedSource | None = None,
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

    # Use provided splitter or get cached one
    if splitter is None:
        splitter = get_html_md_word_splitter()

    words = splitter(text)

    if protected_source is not None and protected_source.regions:
        return _wrap_protected_words(
            words,
            protected=protected_source,
            width=width,
            initial_column=initial_column,
            subsequent_offset=subsequent_offset,
            drop_whitespace=drop_whitespace,
            len_fn=len_fn,
            is_markdown=is_markdown,
        )

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
    protected_source: ProtectedSource | None = None,
) -> str:
    """
    Wrap lines of a single paragraph of plain text, returning a new string.
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
        protected_source=protected_source,
    )
    # Now insert indents on first and subsequent lines, if needed.
    if initial_indent and initial_column == 0 and len(lines) > 0:
        lines[0] = initial_indent + lines[0]
    if subsequent_indent and len(lines) > 1:
        lines[1:] = [subsequent_indent + line for line in lines[1:]]
    result = "\n".join(lines)

    # Restore original adjacency for paired tags (remove spaces added during tokenization)
    return denormalize_adjacent_tags(result)
