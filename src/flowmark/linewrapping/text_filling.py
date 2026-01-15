import re
from collections.abc import Callable
from enum import Enum

from flowmark.linewrapping.text_wrapping import (
    DEFAULT_LEN_FUNCTION,
    WordSplitter,
    get_html_md_word_splitter,
    wrap_paragraph,
)

DEFAULT_WRAP_WIDTH = 88
"""
Default wrap width. This is a compromise between traditional but sometimes
impractically narrow 80-char console width and being too wide to read comfortably
for text, markup, and code. 88 is the same as Black.
"""


DEFAULT_INDENT = "    "


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n{2,}", text)]


class Wrap(Enum):
    """
    A few convenient text wrapping styles.
    """

    NONE = "none"
    """No wrapping."""

    WRAP = "wrap"
    """Basic wrapping but preserves whitespace within paragraphs."""

    WRAP_FULL = "wrap_full"
    """Wraps and also normalizes whitespace."""

    WRAP_INDENT = "wrap_indent"
    """Wrap and also indent."""

    INDENT_ONLY = "indent_only"
    """Just indent."""

    HANGING_INDENT = "hanging_indent"
    """Wrap with hanging indent (indented except for the first line)."""

    MARKDOWN_ITEM = "markdown_item"
    """2-space hanging indent for markdown list items."""

    @property
    def initial_indent(self) -> str:
        if self in [Wrap.INDENT_ONLY, Wrap.WRAP_INDENT]:
            return DEFAULT_INDENT
        else:
            return ""

    @property
    def subsequent_indent(self) -> str:
        if self == Wrap.MARKDOWN_ITEM:
            return "  "
        elif self in [Wrap.INDENT_ONLY, Wrap.WRAP_INDENT, Wrap.HANGING_INDENT]:
            return DEFAULT_INDENT
        else:
            return ""

    @property
    def should_wrap(self) -> bool:
        return self in [
            Wrap.WRAP,
            Wrap.WRAP_FULL,
            Wrap.WRAP_INDENT,
            Wrap.HANGING_INDENT,
            Wrap.MARKDOWN_ITEM,
        ]

    @property
    def initial_indent_first_para_only(self) -> bool:
        return self in [Wrap.HANGING_INDENT, Wrap.MARKDOWN_ITEM]

    @property
    def replace_whitespace(self) -> bool:
        return self in [Wrap.WRAP_FULL, Wrap.WRAP_INDENT, Wrap.HANGING_INDENT]


def fill_text(
    text: str,
    text_wrap: Wrap = Wrap.WRAP,
    width: int = DEFAULT_WRAP_WIDTH,
    extra_indent: str = "",
    empty_indent: str = "",
    initial_column: int = 0,
    word_splitter: WordSplitter | None = None,
    len_fn: Callable[[str], int] = DEFAULT_LEN_FUNCTION,
) -> str:
    """
    Most flexible way to wrap and fill any number of paragraphs of plain text, with
    both text wrap options and extra indentation. Use for plain text.

    By default, uses the HTML and Markdown aware word splitter. This is probably
    what you want, but you can also use the `simple_word_splitter` plaintext wrapping.
    """
    if word_splitter is None:
        word_splitter = get_html_md_word_splitter()

    if not text_wrap.should_wrap:
        indent = extra_indent + DEFAULT_INDENT if text_wrap == Wrap.INDENT_ONLY else extra_indent
        lines = text.splitlines()
        if lines:
            return "\n".join(indent + line for line in lines)
        else:
            return empty_indent
    else:
        # Common settings for all wrap modes.
        empty_indent = empty_indent.strip()
        initial_indent = extra_indent + text_wrap.initial_indent
        subsequent_indent = extra_indent + text_wrap.subsequent_indent

        # These vary by wrap mode.
        width = width - len_fn(subsequent_indent)
        replace_whitespace = text_wrap.replace_whitespace

        paragraphs = split_paragraphs(text)
        wrapped_paragraphs: list[str] = []

        # Wrap each paragraph.
        for i, paragraph in enumerate(paragraphs):
            # Special case for hanging indent modes.
            # Hang the first line of the first paragraph. All other paragraphs are indented.
            if text_wrap.initial_indent_first_para_only and i > 0:
                initial_indent = subsequent_indent

            wrapped_paragraphs.append(
                wrap_paragraph(
                    paragraph,
                    width=width,
                    initial_indent=initial_indent,
                    subsequent_indent=subsequent_indent,
                    initial_column=initial_column,
                    replace_whitespace=replace_whitespace,
                    word_splitter=word_splitter,
                    len_fn=len_fn,
                )
            )

        para_sep = f"\n{empty_indent}\n"
        return para_sep.join(wrapped_paragraphs)
