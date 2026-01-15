from __future__ import annotations

import re
from collections.abc import Callable
from functools import cache
from typing import Protocol

from flowmark.linewrapping.tag_handling import (
    MAX_TAG_WORDS,
    TagWrapping,
    denormalize_adjacent_tags,
    generate_coalescing_patterns,
    get_tag_coalescing_patterns_by_start,
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

    When `atomic_tags=True`, template tags are treated as indivisible tokens
    regardless of internal whitespace. This prevents tags from being broken
    across lines during wrapping.
    """

    # Pattern to detect COMPLETE inline code spans (both opening and closing backticks
    # in the same whitespace-delimited word). These should NOT trigger multi-word
    # coalescing—they're already complete units.
    # Examples: `foo()`, (`code`), `x`, prefix`code`suffix
    # This prevents the bug where `getRequiredEnv()` would incorrectly coalesce
    # with following words like "and", "must", etc.
    _complete_code_span: re.Pattern[str] = re.compile(r"[^\s`]*`[^`]+`[^\s`]*")

    # Pattern to match inline code spans for atomic mode. Matches complete code spans
    # including any prefix/suffix punctuation. Handles multi-backtick spans like ``code``.
    # This protects content inside code spans from being treated as template tags.
    _code_span_pattern: re.Pattern[str] = re.compile(r"[^\s`]*(`+)[^`]+\1[^\s`]*")

    # In atomic mode, use high limit so tags virtually never break internally
    ATOMIC_MAX_TAG_WORDS: int = 128

    # Characters that can start a multi-word construct. If a word doesn't start
    # with one of these (or contain a backtick for code spans), it can't match
    # any coalescing pattern, so we skip all pattern checks.
    _START_CHARS: frozenset[str] = frozenset("{<[`")

    atomic_tags: bool

    def __init__(self, atomic_tags: bool = False):
        self.atomic_tags = atomic_tags
        # Use higher word limit for atomic mode so tags stay together
        tag_max_words = self.ATOMIC_MAX_TAG_WORDS if atomic_tags else MAX_TAG_WORDS

        # Group patterns by what character they can match first for faster lookup.
        # This reduces iterations from O(all_patterns) to O(patterns_for_char).
        self._patterns_by_start: dict[str, list[tuple[re.Pattern[str], ...]]] = {
            "{": [],
            "<": [],
            "[": [],
            "`": [],  # For backtick patterns (code spans)
        }

        # Get tag patterns already grouped by start character from tag_handling module.
        # This keeps tag-specific knowledge (which patterns match which delimiters)
        # encapsulated in the tag_handling module.
        tag_patterns_by_start = get_tag_coalescing_patterns_by_start(max_words=tag_max_words)
        for start_char, patterns in tag_patterns_by_start.items():
            for pattern_tuple in patterns:
                compiled = tuple(re.compile(p) for p in pattern_tuple)
                self._patterns_by_start[start_char].append(compiled)

        # Non-tag patterns defined here with their expected start characters.

        # Inline code spans with spaces: `code with spaces`
        # Per CommonMark, code spans are delimited by equal-length backtick strings.
        # We coalesce words between opening ` and closing ` to keep them atomic.
        # The [^\s`]* prefix/suffix allows punctuation like (`code`) or `code`.
        code_span_patterns = generate_coalescing_patterns(
            start=r"[^\s`]*`[^`]*",
            end=r"[^`]*`[^\s`]*",
            middle=r"[^`]+",
            max_words=tag_max_words,
        )
        for pattern_tuple in code_span_patterns:
            compiled = tuple(re.compile(p) for p in pattern_tuple)
            self._patterns_by_start["`"].append(compiled)

        # HTML/XML tags: <tag attr="value">content</tag>
        html_tag_patterns = generate_coalescing_patterns(
            start=r"<[^>]+",
            end=r"[^<>]+>[^<>]*",
            middle=r"[^<>]+",
            max_words=tag_max_words,
        )
        for pattern_tuple in html_tag_patterns:
            compiled = tuple(re.compile(p) for p in pattern_tuple)
            self._patterns_by_start["<"].append(compiled)

        # Markdown links: [text](url) or [text][ref]
        # Links with multi-word text like [Mark Suster, Upfront Ventures](url) are
        # kept together to avoid awkward line breaks within the link text.
        md_link_patterns = generate_coalescing_patterns(
            start=r"\[",
            end=r"[^\[\]]+\][^\[\]]*",
            middle=r"[^\[\]]+",
            max_words=tag_max_words,
        )
        for pattern_tuple in md_link_patterns:
            compiled = tuple(re.compile(p) for p in pattern_tuple)
            self._patterns_by_start["["].append(compiled)

        # Build flat list for compatibility (used in match_pattern_group)
        self.compiled_patterns: list[tuple[re.Pattern[str], ...]] = []
        for patterns in self._patterns_by_start.values():
            self.compiled_patterns.extend(patterns)

    def __call__(self, text: str) -> list[str]:
        # First normalize adjacent tags to ensure proper tokenization
        text = normalize_adjacent_tags(text)

        if self.atomic_tags:
            return self._split_with_atomic_constructs(text)
        else:
            return self._split_with_coalescing(text)

    def _split_with_coalescing(self, text: str) -> list[str]:
        """Coalescing-based splitting."""
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

        # Second pass: merge adjacent opening+closing tag pairs
        # This handles cases where opening tag was coalesced but closing tag
        # is separate (e.g., {% field kind="long" ... %} {% /field %})
        if self.atomic_tags:
            result = self._merge_paired_tags(result)

        return result

    def _merge_paired_tags(self, tokens: list[str]) -> list[str]:
        """
        Merge adjacent opening+closing tag pairs into single tokens.

        After coalescing, an opening tag like `{% field ... %}` becomes one token,
        but the closing tag `{% /field %}` is separate. This pass merges them.
        """
        if len(tokens) < 2:
            return tokens

        result: list[str] = []
        i = 0
        while i < len(tokens):
            if i + 1 < len(tokens):
                current = tokens[i]
                next_token = tokens[i + 1]

                # Check if current ends with tag close and next is closing tag
                if self._is_tag_close(current) and self._is_closing_tag(next_token):
                    # Merge them (with the space that normalize_adjacent_tags added)
                    result.append(current + " " + next_token)
                    i += 2
                    continue

            result.append(tokens[i])
            i += 1

        return result

    def _is_tag_close(self, token: str) -> bool:
        """Check if token ends with a tag closing delimiter."""
        return (
            token.endswith("%}")
            or token.endswith("#}")
            or token.endswith("}}")
            or token.endswith("-->")
        )

    def _is_closing_tag(self, token: str) -> bool:
        """Check if token is a closing tag (starts with {% /, {# /, etc.)."""
        stripped = token.strip()
        return (
            stripped.startswith("{% /")
            or stripped.startswith("{# /")
            or stripped.startswith("{{ /")
            or stripped.startswith("<!-- /")
        )

    def _split_with_atomic_constructs(self, text: str) -> list[str]:
        """
        Split for atomic mode - uses same coalescing with higher word limit.

        In atomic mode, the patterns were generated with ATOMIC_MAX_TAG_WORDS (128)
        instead of MAX_TAG_WORDS (12), so tags virtually never break internally.
        This preserves original whitespace while preventing tag breaks.
        """
        # Patterns were already generated with higher limit in __init__
        return self._split_with_coalescing(text)

    def coalesce_words(self, words: list[str]) -> int:
        if not words:
            return 0

        first_word = words[0]
        first_char = first_word[0]

        # Quick reject: if first word doesn't start with a trigger character
        # and doesn't contain a backtick (for code spans like "prefix`code"),
        # it can't match any pattern, so skip expensive pattern matching.
        has_backtick = "`" in first_word
        if first_char not in self._START_CHARS and not has_backtick:
            return 0

        # Skip coalescing if the first word is already a complete inline code span.
        # This prevents `foo()` from incorrectly coalescing with following words.
        if self._complete_code_span.fullmatch(first_word):
            return 0

        # Use grouped patterns for faster lookup - only check patterns that could match
        # based on the first character, rather than iterating through all patterns.
        patterns_to_check: list[tuple[re.Pattern[str], ...]] = []
        if first_char in self._patterns_by_start:
            patterns_to_check = self._patterns_by_start[first_char]
        elif has_backtick:
            patterns_to_check = self._patterns_by_start["`"]

        for pattern_group in patterns_to_check:
            if self.match_pattern_group(words, pattern_group):
                return len(pattern_group)
        return 0

    def match_pattern_group(self, words: list[str], patterns: tuple[re.Pattern[str], ...]) -> bool:
        if len(words) < len(patterns):
            return False

        return all(pattern.match(word) for pattern, word in zip(patterns, words, strict=False))


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
