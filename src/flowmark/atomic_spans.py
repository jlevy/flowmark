"""
Public API for Markdown *atomic constructs* and the offset-preserving tokenizers built on
them.

Terminology used throughout this module:

- **offsets** — 0-based character indices into the source string. Ranges are half-open
  `[start, end)`, so `source[start:end]` is exactly the referenced text.
- **span** — a slice of source text together with its `[start, end)` offsets; its `text`
  always equals `source[start:end]`. (Contrast a bare *range*, which is offsets with no
  text — not used in this module's return types.)
- **atomic construct** — a Markdown or templating inline construct that must be kept whole
  and never broken in the middle: a code span, link, autolink, bare URL, or HTML/Jinja
  tag or comment. `ATOMIC_PATTERNS` is the full set used for line wrapping;
  `MARKDOWN_INLINE_PATTERNS` is the Markdown-only prose subset.
- **word** — a whitespace-delimited token, except that an atomic construct is kept whole
  (its internal spaces never split it, and it glues to adjacent non-space characters).

These are the same patterns flowmark uses internally for line wrapping, exposed here as a
stable, intentional surface so downstream tools can reuse them instead of copying
flowmark internals.

**Heuristic, not a parser.** These patterns identify *unbreakable spans* for wrapping and
tokenization. They are deliberately simpler than a real Markdown parser: ``MARKDOWN_LINK``
does not resolve reference links, handle nested brackets, distinguish images, or honor
escapes. Do **not** use them to enumerate links — for that, parse with
:func:`flowmark.flowmark_markdown` and use :func:`flowmark.markdown_ast.extract_links`, which
reflects what Markdown actually treats as a link.

This module also exposes the offset-preserving tokenizers built on these patterns
(:func:`iter_atomic_spans`, :func:`iter_atomic_words`) and the atomic-aware sentence
splitter :func:`split_sentences_with_spans`.
"""

from __future__ import annotations

from flowmark.linewrapping.atomic_patterns import (
    ATOMIC_CONSTRUCT_PATTERN,
    ATOMIC_PATTERNS,
    AUTOLINK,
    BARE_URL,
    HTML_CLOSE_TAG,
    HTML_OPEN_TAG,
    INLINE_CODE_SPAN,
    MARKDOWN_INLINE_PATTERNS,
    MARKDOWN_LINK,
    PAIRED_HTML_COMMENT,
    PAIRED_JINJA_COMMENT,
    PAIRED_JINJA_TAG,
    PAIRED_JINJA_VAR,
    SINGLE_HTML_COMMENT,
    SINGLE_JINJA_COMMENT,
    SINGLE_JINJA_TAG,
    SINGLE_JINJA_VAR,
    AtomicPattern,
    AtomicSpan,
    AtomicWord,
    iter_atomic_spans,
    iter_atomic_words,
)
from flowmark.linewrapping.sentence_split_regex import (
    SentenceSpan,
    split_sentences_atomic,
    split_sentences_with_spans,
)

__all__ = (
    "AtomicPattern",
    "ATOMIC_PATTERNS",
    "ATOMIC_CONSTRUCT_PATTERN",
    "MARKDOWN_INLINE_PATTERNS",
    "INLINE_CODE_SPAN",
    "MARKDOWN_LINK",
    "AUTOLINK",
    "BARE_URL",
    "SINGLE_JINJA_TAG",
    "PAIRED_JINJA_TAG",
    "SINGLE_JINJA_COMMENT",
    "PAIRED_JINJA_COMMENT",
    "SINGLE_JINJA_VAR",
    "PAIRED_JINJA_VAR",
    "SINGLE_HTML_COMMENT",
    "PAIRED_HTML_COMMENT",
    "HTML_OPEN_TAG",
    "HTML_CLOSE_TAG",
    "AtomicSpan",
    "AtomicWord",
    "iter_atomic_spans",
    "iter_atomic_words",
    "SentenceSpan",
    "split_sentences_with_spans",
    "split_sentences_atomic",
)
