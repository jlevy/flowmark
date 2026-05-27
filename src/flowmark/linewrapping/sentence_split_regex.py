from __future__ import annotations

from collections.abc import Callable
from typing import NamedTuple

import regex

from flowmark.linewrapping.atomic_patterns import (
    MARKDOWN_INLINE_PATTERNS,
    AtomicPattern,
    iter_atomic_words,
)

# XXX: Could also handle rare cases with both quotes and parentheses at sentence end
# but may not be worth it. Also does not detect sentences ending in numerals, which
# tends to cause too many false positives. Should be OK for most Latin languages but
# may need to rethink the 2-letter restriction for some languages.
# See also:
# https://github.com/jlevy/atom-flowmark/blob/master/lib/remark-smart-word-wrap.js#L17-L33
SENTENCE_END_RE = regex.compile(r"(\b\p{L}+[\p{Ll}])([.?!]['\"’”)]?|['\"’”)][.?!]) *$")

# Second heuristic: Very short sentences often not so useful.
SENTENCE_MIN_LENGTH = 15


def heuristic_end_of_sentence(word: str) -> bool:
    return bool(SENTENCE_END_RE.search(word))


def split_sentences_regex(
    text: str,
    min_length: int = SENTENCE_MIN_LENGTH,
    heuristic: Callable[[str], bool] = heuristic_end_of_sentence,
) -> list[str]:
    """
    Split text into sentences using an approximate, fast regex heuristic.

    Goal is to be conservative, not perfect, avoiding excessive breaks.

    The default heuristic: End of sentence must be two letters or more,
    with the last letter lowercase, followed by a period, exclamation point,
    question mark. A final or preceding parenthesis or quote is allowed.
    Does not break on colon or semicolon as that seems to have false
    positives too often with code or other syntax.

    They work pretty well when used for formatting and editing documents
    in English. It should be reasonable for most Latin languages.
    Note this is smarter than Python textwrap's simpler heuristic:
    https://github.com/python/cpython/blob/main/Lib/textwrap.py#L105-L110

    :param text: The text to split into sentences.
    :param heuristic: A callable that returns True if text ends at the end of a sentence.
    :param min_length: The minimum length of a sentence in characters.
    :return: A list of sentences.
    """
    words = text.split()
    sentences: list[str] = []
    sentence: list[str] = []
    words_len = 0
    for word in words:
        sentence.append(word)
        words_len += len(word)
        sentence_len = words_len + len(sentence) - 1
        if heuristic(word) and sentence_len >= min_length:
            sentences.append(" ".join(sentence))
            sentence = []
            words_len = 0
    if sentence:
        sentences.append(" ".join(sentence))
    return sentences


def first_sentences(
    text: str,
    n: int,
    min_length: int = SENTENCE_MIN_LENGTH,
    heuristic: Callable[[str], bool] = heuristic_end_of_sentence,
) -> list[str]:
    """
    Return the first n sentences from the text.
    """
    return split_sentences_regex(text, min_length=min_length, heuristic=heuristic)[:n]


def first_sentence(
    text: str,
    min_length: int = SENTENCE_MIN_LENGTH,
    heuristic: Callable[[str], bool] = heuristic_end_of_sentence,
) -> str:
    """
    Return the first sentence from the text. Returns input text unchanged if no
    sentences are found.
    """
    sentences = split_sentences_regex(text, min_length=min_length, heuristic=heuristic)
    return sentences[0] if sentences else text


class SentenceSpan(NamedTuple):
    """
    A sentence and its exact `[start, end)` character offsets into the original Markdown
    source, such that `text == source[start:end]` (verbatim, including any Markdown markup
    the sentence contains).
    """

    text: str
    start: int
    end: int


def split_sentences_with_spans(
    text: str,
    min_length: int = SENTENCE_MIN_LENGTH,
    heuristic: Callable[[str], bool] = heuristic_end_of_sentence,
    patterns: tuple[AtomicPattern, ...] = MARKDOWN_INLINE_PATTERNS,
) -> list[SentenceSpan]:
    """
    Split Markdown `text` into sentences, each returned as a `SentenceSpan`: the sentence
    text plus its exact `[start, end)` offsets into the original Markdown source (so
    `span.text == text[start:end]`, verbatim).

    This is the offset-preserving, Markdown-aware counterpart to `split_sentences_regex`
    (which normalizes whitespace via `split()`/`join()` and so loses offsets). It is
    "atomic-aware" with respect to Markdown inline constructs in `patterns` — links, code
    spans, autolinks, and bare URLs — keeping each one whole so a sentence boundary is
    never placed inside it (e.g. a link whose text contains spaces or a `.` is not
    bisected). The end-of-sentence heuristic is applied only at word boundaries between
    these constructs.
    """
    sentences: list[SentenceSpan] = []
    s_start = -1
    s_end = -1
    char_count = 0
    word_count = 0
    for word in iter_atomic_words(text, patterns):
        if s_start < 0:
            s_start = word.start
        s_end = word.end
        char_count += len(word.text)
        word_count += 1
        # Mirror split_sentences_regex's length accounting (words plus single spaces).
        sentence_len = char_count + word_count - 1
        if heuristic(word.text) and sentence_len >= min_length:
            sentences.append(SentenceSpan(text[s_start:s_end], s_start, s_end))
            s_start = -1
            s_end = -1
            char_count = 0
            word_count = 0
    if s_start >= 0:
        sentences.append(SentenceSpan(text[s_start:s_end], s_start, s_end))
    return sentences


def split_sentences_atomic(
    text: str,
    min_length: int = SENTENCE_MIN_LENGTH,
    heuristic: Callable[[str], bool] = heuristic_end_of_sentence,
) -> list[str]:
    """
    Atomic-aware sentence splitter returning sentence strings (a drop-in
    `SentenceSplitter`). Like `split_sentences_regex` but never splits inside a link,
    code span, or URL. Suitable as the `split_sentences` argument to
    `line_wrap_by_sentence`.
    """
    return [
        s.text for s in split_sentences_with_spans(text, min_length=min_length, heuristic=heuristic)
    ]
