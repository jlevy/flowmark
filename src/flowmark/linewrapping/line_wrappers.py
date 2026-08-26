from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from flowmark.linewrapping.protocols import LineWrapper
from flowmark.linewrapping.sentence_split_regex import split_sentences_atomic
from flowmark.linewrapping.tag_handling import (
    add_tag_newline_handling,
    denormalize_adjacent_tags,
)
from flowmark.linewrapping.text_filling import DEFAULT_WRAP_WIDTH
from flowmark.linewrapping.text_wrapping import (
    DEFAULT_LEN_FUNCTION,
    markdown_escape_word,
    measure_protected_text,
    wrap_paragraph,
    wrap_paragraph_lines,
)
from flowmark.preservation.bridge import ProtectedSource

DEFAULT_MIN_LINE_LEN = 20
"""Default minimum line length for sentence breaking."""


class SentenceSplitter(Protocol):
    """Takes a text string and returns a list of sentences."""

    def __call__(self, text: str) -> list[str]: ...


@dataclass(frozen=True, slots=True)
class _BindableLineWrapper:
    """Existing callable interface plus an internal immutable protection binder."""

    callback: LineWrapper
    binder: Callable[[ProtectedSource], LineWrapper]

    def __call__(self, text: str, initial_indent: str, subsequent_indent: str) -> str:
        return self.callback(text, initial_indent, subsequent_indent)

    def bind_protected_source(self, protected_source: ProtectedSource) -> LineWrapper:
        return self.binder(protected_source)


def bind_protected_source(
    line_wrapper: LineWrapper, protected_source: ProtectedSource | None
) -> LineWrapper:
    """Bind side-table widths to built-in wrappers without changing the public callable."""
    if protected_source is not None and isinstance(line_wrapper, _BindableLineWrapper):
        return line_wrapper.bind_protected_source(protected_source)
    return line_wrapper


def split_sentences_no_min_length(text: str) -> list[str]:
    # Atomic-aware: never break a sentence inside a link/code span/URL (e.g. a "St."
    # inside link text must not trip the end-of-sentence heuristic).
    return split_sentences_atomic(text, min_length=0)


_line_break_re = re.compile(r"\\\n|  \n")


def split_markdown_hard_breaks(text: str) -> list[str]:
    """
    Split text by explicit Markdown line breaks.
    """
    return _line_break_re.split(text)


def _add_markdown_hard_break_handling(base_wrapper: LineWrapper) -> LineWrapper:
    """
    Augments a LineWrapper to first split the text by Markdown hard breaks,
    wrap each segment using the base_wrapper, and then rejoin them with
    a normalized Markdown hard break (backslash-newline).
    """

    def enhanced_wrapper(text: str, initial_indent: str, subsequent_indent: str) -> str:
        segments = split_markdown_hard_breaks(text)

        # Handle empty input.
        if not segments:
            return ""
        # Handle single segment (no hard line breaks).
        if len(segments) == 1:
            return base_wrapper(text, initial_indent, subsequent_indent)

        wrapped_segments: list[str] = []

        for i, segment in enumerate(segments):
            is_first = i == 0
            is_last = i == len(segments) - 1

            cur_initial_indent = initial_indent if is_first else subsequent_indent
            wrapped_segment = base_wrapper(segment, cur_initial_indent, subsequent_indent)
            if is_last:
                wrapped_segments.append(wrapped_segment)
            else:
                wrapped_segments.append(wrapped_segment + "\\")

        return "\n".join(wrapped_segments)

    return enhanced_wrapper


def line_wrap_to_width(
    width: int = DEFAULT_WRAP_WIDTH,
    len_fn: Callable[[str], int] = DEFAULT_LEN_FUNCTION,
    is_markdown: bool = False,
    protected_source: ProtectedSource | None = None,
) -> LineWrapper:
    """
    Wrap lines of text to a given width.
    """

    def build(bound_source: ProtectedSource | None) -> LineWrapper:
        def line_wrapper(text: str, initial_indent: str, subsequent_indent: str) -> str:
            return wrap_paragraph(
                text,
                width=width,
                initial_indent=initial_indent,
                subsequent_indent=subsequent_indent,
                len_fn=len_fn,
                is_markdown=is_markdown,
                protected_source=bound_source,
            )

        callback: LineWrapper = line_wrapper
        if is_markdown:
            # Apply tag newline handling first, then hard break handling. Order matters:
            # tags operate on authored newlines before hard-break normalization.
            callback = _add_markdown_hard_break_handling(add_tag_newline_handling(callback))
        return _BindableLineWrapper(callback, build)

    return build(protected_source)


def line_wrap_by_sentence(
    split_sentences: SentenceSplitter = split_sentences_no_min_length,
    width: int = DEFAULT_WRAP_WIDTH,
    min_line_len: int = DEFAULT_MIN_LINE_LEN,
    len_fn: Callable[[str], int] = DEFAULT_LEN_FUNCTION,
    is_markdown: bool = False,
    protected_source: ProtectedSource | None = None,
) -> LineWrapper:
    """
    Wrap lines of text to a given width but also keep sentences on their own lines.
    If the last line ends up shorter than `min_line_len`, it's combined with the
    next sentence.
    """

    def build(bound_source: ProtectedSource | None) -> LineWrapper:
        def logical_final_width(text: str) -> int:
            if bound_source is None:
                return len_fn(text)
            return measure_protected_text(text, bound_source, len_fn).final_width

        def line_wrapper(text: str, initial_indent: str, subsequent_indent: str) -> str:
            text = text.replace("\n", " ")

            # Handle width <= 0 as "no wrapping". Tokens contain no whitespace, so
            # authored whitespace inside protected source remains exclusively side-table data.
            if width <= 0:
                return initial_indent + " ".join(text.split())

            lines: list[str] = []
            first_line = True
            initial_indent_len = len_fn(initial_indent)
            subsequent_indent_len = len_fn(subsequent_indent)

            sentences = split_sentences(text)

            for sentence in sentences:
                starts_new_output_line = bool(lines)
                current_column = initial_indent_len if first_line else subsequent_indent_len
                if lines and logical_final_width(lines[-1]) < min_line_len:
                    current_column += logical_final_width(lines[-1])

                wrapped = wrap_paragraph_lines(
                    sentence,
                    width=width,
                    initial_column=current_column,
                    subsequent_offset=subsequent_indent_len,
                    is_markdown=is_markdown,
                    len_fn=len_fn,
                    protected_source=bound_source,
                )
                # If the last line is short, combine it with the next sentence's first line.
                next_first_width = (
                    measure_protected_text(wrapped[0], bound_source, len_fn).first_width
                    if bound_source is not None and wrapped
                    else len_fn(wrapped[0])
                    if wrapped
                    else 0
                )
                if (
                    lines
                    and wrapped
                    and logical_final_width(lines[-1]) < min_line_len
                    and logical_final_width(lines[-1]) + 1 + next_first_width <= width
                ):
                    lines[-1] += " " + wrapped[0]
                    wrapped.pop(0)
                    starts_new_output_line = False

                if is_markdown and starts_new_output_line and wrapped:
                    first_word, separator, remainder = wrapped[0].partition(" ")
                    wrapped[0] = markdown_escape_word(first_word) + separator + remainder

                lines.extend(wrapped)

                first_line = False

            # Now insert the indents and assemble the paragraph.
            if initial_indent and lines:
                lines[0] = initial_indent + lines[0]
            if subsequent_indent and len(lines) > 1:
                lines[1:] = [subsequent_indent + line for line in lines[1:]]

            result = "\n".join(lines)

            # Restore original adjacency for paired tags added during tokenization.
            return denormalize_adjacent_tags(result)

        callback: LineWrapper = line_wrapper
        if is_markdown:
            callback = _add_markdown_hard_break_handling(add_tag_newline_handling(callback))
        return _BindableLineWrapper(callback, build)

    return build(protected_source)
