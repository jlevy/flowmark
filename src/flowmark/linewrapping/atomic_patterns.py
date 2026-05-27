"""
Atomic pattern definitions for constructs that should not be broken during wrapping.

Each AtomicPattern defines a regex for a specific type of construct (code span, link,
template tag, etc.) that should be kept together as a single token during line wrapping.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from functools import cache
from typing import NamedTuple


@dataclass(frozen=True)
class AtomicPattern:
    """
    Defines a regex pattern for an atomic construct that should not be broken.

    Only `name` and `pattern` are needed to define a construct for tokenization; a
    consumer adding a custom construct can write `AtomicPattern(name=..., pattern=...)`.

    The delimiter fields are used only by the tag-adjacency handling for paired
    template tags: `open_delim`/`close_delim` store the raw delimiters and
    `open_re`/`close_re` store regex-escaped versions. They default to empty for
    non-delimiter patterns (code spans, links, etc.).
    """

    name: str
    pattern: str
    open_delim: str = ""
    close_delim: str = ""
    open_re: str = ""
    close_re: str = ""


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

# Angle-bracket autolinks: <scheme:...> (CommonMark URI autolink) or <email>.
AUTOLINK = AtomicPattern(
    name="autolink",
    pattern=r"<[A-Za-z][A-Za-z0-9+.\-]*:[^\s<>]*>|<[^\s<>@]+@[^\s<>]+>",
)

# Bare URLs (GFM autolinks): http(s):// or www. runs. The final character class
# excludes trailing sentence punctuation so a period/comma/paren ending a sentence is
# not swallowed into the URL (mirrors GFM's trailing-punctuation trimming).
BARE_URL = AtomicPattern(
    name="bare_url",
    pattern=r"(?:https?://|www\.)[^\s<>]*[^\s<>?!.,:;*_~'\")\]]",
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

# A focused subset for prose: the Markdown-inline constructs (code spans, links, and
# autolinks/bare URLs), excluding the HTML/Jinja templating patterns in the full wrapping
# set. Useful for sentence splitting and other text analysis that only cares about
# Markdown inlines. Not a subset of `ATOMIC_PATTERNS`: the two sets are purpose-built (the
# wrapping set keeps URLs whole via whitespace and matches `<...>` as an HTML tag, so it
# omits the dedicated URL patterns this prose set needs).
MARKDOWN_INLINE_PATTERNS: tuple[AtomicPattern, ...] = (
    INLINE_CODE_SPAN,
    MARKDOWN_LINK,
    AUTOLINK,
    BARE_URL,
)


class AtomicSpan(NamedTuple):
    """
    A span (a slice of source text plus its half-open `[start, end)` character offsets,
    so `text == source[start:end]`) produced by `iter_atomic_spans`. `is_atomic` is True
    when the span is an atomic construct — a link, code span, autolink, URL, or tag that
    must not be split mid-construct — and False for the plain-text gaps between them.

    `name` is the `AtomicPattern.name` of the construct that matched (e.g. `"markdown_link"`
    vs `"inline_code_span"`), or `None` for non-atomic spans. It lets a consumer tell a
    link span from a code span without re-matching the patterns.
    """

    text: str
    start: int
    end: int
    is_atomic: bool
    name: str | None = None


@cache
def _combined_pattern(patterns: tuple[AtomicPattern, ...]) -> re.Pattern[str]:
    return re.compile("|".join(p.pattern for p in patterns), re.DOTALL)


@cache
def _named_patterns(
    patterns: tuple[AtomicPattern, ...],
) -> tuple[tuple[str, re.Pattern[str]], ...]:
    # Individual compiled patterns, in priority order, used to label which construct a
    # combined-regex match came from. We can't use named groups in the combined regex
    # because several patterns rely on numbered backreferences (e.g. code spans).
    return tuple((p.name, re.compile(p.pattern, re.DOTALL)) for p in patterns)


def _match_name(patterns: tuple[AtomicPattern, ...], text: str, start: int) -> str | None:
    # The combined alternation is ordered, so the matched construct is the first pattern
    # that matches anchored at `start`.
    for name, rx in _named_patterns(patterns):
        if rx.match(text, start):
            return name
    return None


def iter_atomic_spans(
    text: str, patterns: tuple[AtomicPattern, ...] = ATOMIC_PATTERNS
) -> Iterator[AtomicSpan]:
    """
    Split `text` into contiguous spans (each a slice of `text` with its `[start, end)`
    offsets) that cover it exactly, each flagged `is_atomic`.

    Atomic spans match one of `patterns` — a Markdown/templating construct that must not
    be broken mid-construct (code span, link, autolink, URL, tag); non-atomic spans are
    the plain-text gaps between them. Each atomic span's `name` is the matched
    `AtomicPattern.name`. Round-trips: `"".join(s.text ...) == text` and
    `text[s.start:s.end] == s.text` for every span. An empty `patterns` yields the whole
    input as a single non-atomic span.
    """
    if not patterns:
        if text:
            yield AtomicSpan(text, 0, len(text), False)
        return
    regex = _combined_pattern(patterns)
    pos = 0
    for m in regex.finditer(text):
        if m.start() > pos:
            yield AtomicSpan(text[pos : m.start()], pos, m.start(), False)
        yield AtomicSpan(
            m.group(0), m.start(), m.end(), True, _match_name(patterns, text, m.start())
        )
        pos = m.end()
    if pos < len(text):
        yield AtomicSpan(text[pos:], pos, len(text), False)


_WHITESPACE_OR_WORD = re.compile(r"\S+|\s+")


class AtomicWord(NamedTuple):
    """
    A word (a whitespace-delimited token, with any atomic construct kept whole) plus its
    half-open `[start, end)` character offsets, so `text == source[start:end]`. Produced
    by `iter_atomic_words`.
    """

    text: str
    start: int
    end: int


def iter_atomic_words(
    text: str, patterns: tuple[AtomicPattern, ...] = ATOMIC_PATTERNS
) -> Iterator[AtomicWord]:
    """
    Yield the whitespace-delimited words of `text` with their `[start, end)` offsets,
    treating each atomic construct (link, code span, URL, tag) as indivisible: a
    construct's internal whitespace never splits a word, and a construct glues to adjacent
    non-space characters (e.g. `foo[a](b)bar` and `[click here](u)` are each one word).

    This is the offset-carrying basis for both the wrapping word splitter and
    `split_sentences_with_spans`.
    """
    buf: list[str] = []
    w_start = -1
    w_end = -1
    for sp in iter_atomic_spans(text, patterns):
        if sp.is_atomic:
            if w_start < 0:
                w_start = sp.start
            buf.append(sp.text)
            w_end = sp.end
        else:
            for tok in _WHITESPACE_OR_WORD.finditer(sp.text):
                if tok.group().isspace():
                    if buf:
                        yield AtomicWord("".join(buf), w_start, w_end)
                        buf = []
                        w_start = -1
                        w_end = -1
                else:
                    if w_start < 0:
                        w_start = sp.start + tok.start()
                    buf.append(tok.group())
                    w_end = sp.start + tok.end()
    if buf:
        yield AtomicWord("".join(buf), w_start, w_end)
