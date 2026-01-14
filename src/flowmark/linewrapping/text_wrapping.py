from __future__ import annotations

import re
from collections.abc import Callable
from typing import Protocol

from flowmark.linewrapping.tag_handling import (
    denormalize_adjacent_tags,
    generate_coalescing_patterns,
    get_tag_coalescing_patterns,
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


class _HtmlMdWordSplitter:
    """
    Word splitter for Markdown/HTML that keeps certain constructs together.

    This handles LINE WRAPPING, not Markdown parsing. The distinction matters:
    - Markdown parsing (handled by Marko): Interprets code spans, applies escaping
      rules, converts line breaks to spaces per CommonMark spec
    - Line wrapping (this code): Decides where to break lines in source text

    For inline code spans, we follow these principles:
    - Single-word code (`foo()`) stays atomic, doesn't merge with following text
    - Multi-word code (`code with spaces`) coalesces into one token
    - Punctuation stays attached (`method()`.` as one token)
    - Content is never modified (backslashes, special chars preserved)

    This is compatible with CommonMark because we don't interpret code span
    content—we just keep tokens together for sensible line wrapping.
    See: https://spec.commonmark.org/0.31.2/#code-spans

    Note: This class runs AFTER Markdown parsing, so any CommonMark escape
    sequences will have already been processed by Marko before we see the text.
    """

    # Pattern to detect COMPLETE inline code spans (both opening and closing backticks
    # in the same whitespace-delimited word). These should NOT trigger multi-word
    # coalescing—they're already complete units.
    # Examples: `foo()`, (`code`), `x`, prefix`code`suffix
    # This prevents the bug where `getRequiredEnv()` would incorrectly coalesce
    # with following words like "and", "must", etc.
    _complete_code_span: re.Pattern[str] = re.compile(r"[^\s`]*`[^`]+`[^\s`]*")

    def __init__(self):
        # Patterns for multi-word constructs that should be coalesced into single tokens.
        # Each pattern is a tuple of regexes: (start, middle..., end).
        self.patterns: list[tuple[str, ...]] = [
            # Template tag patterns (Jinja/Markdoc/HTML comments) from tag_handling module
            *get_tag_coalescing_patterns(),
            # Inline code spans with spaces: `code with spaces`
            # Per CommonMark, code spans are delimited by equal-length backtick strings.
            # We coalesce words between opening ` and closing ` to keep them atomic.
            # The [^\s`]* prefix/suffix allows punctuation like (`code`) or `code`.
            *generate_coalescing_patterns(
                start=r"[^\s`]*`[^`]*",
                end=r"[^`]*`[^\s`]*",
                middle=r"[^`]+",
            ),
            # HTML/XML tags: <tag attr="value">content</tag>
            *generate_coalescing_patterns(
                start=r"<[^>]+",
                end=r"[^<>]+>[^<>]*",
                middle=r"[^<>]+",
            ),
            # Markdown links: [text](url) or [text][ref]
            # Links with multi-word text like [Mark Suster, Upfront Ventures](url) are
            # kept together to avoid awkward line breaks within the link text.
            *generate_coalescing_patterns(
                start=r"\[",
                end=r"[^\[\]]+\][^\[\]]*",
                middle=r"[^\[\]]+",
            ),
        ]
        self.compiled_patterns: list[tuple[re.Pattern[str], ...]] = [
            tuple(re.compile(pattern) for pattern in pattern_group)
            for pattern_group in self.patterns
        ]

    def __call__(self, text: str) -> list[str]:
        # First normalize adjacent tags to ensure proper tokenization
        text = normalize_adjacent_tags(text)

        words = text.split()
        result: list[str] = []
        i = 0
        while i < len(words):
            coalesced = self.coalesce_words(words[i:])
            if coalesced > 0:
                result.append(" ".join(words[i : i + coalesced]))
                i += coalesced
            else:
                result.append(words[i])
                i += 1
        return result

    def coalesce_words(self, words: list[str]) -> int:
        # Skip coalescing if the first word is already a complete inline code span.
        # This prevents `foo()` from incorrectly coalescing with following words.
        if words and self._complete_code_span.fullmatch(words[0]):
            return 0

        for pattern_group in self.compiled_patterns:
            if self.match_pattern_group(words, pattern_group):
                return len(pattern_group)
        return 0

    def match_pattern_group(self, words: list[str], patterns: tuple[re.Pattern[str], ...]) -> bool:
        if len(words) < len(patterns):
            return False

        return all(pattern.match(word) for pattern, word in zip(patterns, words, strict=False))


html_md_word_splitter: WordSplitter = _HtmlMdWordSplitter()
"""
Split words, but not within HTML tags or Markdown links.
"""


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
    splitter: WordSplitter = html_md_word_splitter,
    len_fn: Callable[[str], int] = DEFAULT_LEN_FUNCTION,
    is_markdown: bool = False,
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
    word_splitter: WordSplitter = html_md_word_splitter,
    len_fn: Callable[[str], int] = DEFAULT_LEN_FUNCTION,
    is_markdown: bool = False,
) -> str:
    """
    Wrap lines of a single paragraph of plain text, returning a new string.
    By default, uses an HTML- and Markdown-aware word splitter.
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
    )
    # Now insert indents on first and subsequent lines, if needed.
    if initial_indent and initial_column == 0 and len(lines) > 0:
        lines[0] = initial_indent + lines[0]
    if subsequent_indent and len(lines) > 1:
        lines[1:] = [subsequent_indent + line for line in lines[1:]]
    result = "\n".join(lines)
    # Restore original adjacency for paired tags (remove spaces added during tokenization)
    return denormalize_adjacent_tags(result)
