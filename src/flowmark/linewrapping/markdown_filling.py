"""
Auto-formatting of Markdown text.

This is similar to what is offered by
[markdownfmt](https://github.com/shurcooL/markdownfmt) but with a few adaptations,
including more aggressive normalization and support for wrapping of lines
semi-semantically (e.g. on sentence boundaries when appropriate).
(See [here](https://github.com/shurcooL/markdownfmt/issues/17) for some old
discussion on why line wrapping this way is convenient.)
"""

from __future__ import annotations

from textwrap import dedent

from flowmark.formats.flowmark_markdown import flowmark_markdown
from flowmark.formats.frontmatter import split_frontmatter
from flowmark.linewrapping.line_wrappers import (
    LineWrapper,
    line_wrap_by_sentence,
    line_wrap_to_width,
)
from flowmark.linewrapping.sentence_split_regex import split_sentences_regex
from flowmark.linewrapping.text_filling import DEFAULT_WRAP_WIDTH
from flowmark.transforms.doc_cleanups import doc_cleanups
from flowmark.transforms.doc_transforms import rewrite_text_content
from flowmark.typography.ellipses import ellipses as apply_ellipses
from flowmark.typography.smartquotes import smart_quotes


def split_sentences_no_min_length(text: str) -> list[str]:
    return split_sentences_regex(text, min_length=0)


def fill_markdown(
    markdown_text: str,
    dedent_input: bool = True,
    width: int = DEFAULT_WRAP_WIDTH,
    semantic: bool = False,
    cleanups: bool = False,
    smartquotes: bool = False,
    ellipses: bool = False,
    line_wrapper: LineWrapper | None = None,
) -> str:
    """
    Normalize and wrap Markdown text filling paragraphs to the full width.

    Wraps lines and adds line breaks within paragraphs and on
    best-guess estimations of sentences, to make diffs more readable.

    Also enforces that all list items have two newlines between them, so
    that items are separate paragraphs when viewed as plaintext.

    Optionally also dedents and strips the input, so it can be used
    on docstrings.

    With `semantic` enabled, the line breaks are wrapped approximately
    by sentence boundaries, to make diffs more readable.

    Preserves YAML frontmatter (delimited by --- lines) if present at the
    beginning of the document.
    """
    if line_wrapper is None:
        if semantic:
            line_wrapper = line_wrap_by_sentence(width=width, is_markdown=True)
        else:
            line_wrapper = line_wrap_to_width(width=width, is_markdown=True)

    # Extract frontmatter before any processing
    frontmatter, content = split_frontmatter(markdown_text)

    # Only format the content part if there's frontmatter
    if frontmatter:
        markdown_text = content

    if dedent_input:
        markdown_text = dedent(markdown_text).strip()

    markdown_text = markdown_text.strip() + "\n"

    # Parse and render.
    marko = flowmark_markdown(line_wrapper)
    document = marko.parse(markdown_text)
    if cleanups:
        doc_cleanups(document)
    if smartquotes:
        rewrite_text_content(document, smart_quotes, coalesce_lines=True)
    if ellipses:
        rewrite_text_content(document, apply_ellipses, coalesce_lines=True)
    result = marko.render(document)

    # Reattach frontmatter if it was present
    if frontmatter:
        result = frontmatter + result

    return result
