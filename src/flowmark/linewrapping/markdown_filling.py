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

from flowmark.formats.flowmark_markdown import ListSpacing, flowmark_markdown
from flowmark.formats.frontmatter import split_frontmatter
from flowmark.linewrapping.line_wrappers import (
    line_wrap_by_sentence,
    line_wrap_to_width,
)
from flowmark.linewrapping.protocols import LineWrapper
from flowmark.linewrapping.tag_handling import preprocess_tag_block_spacing
from flowmark.linewrapping.text_filling import DEFAULT_WRAP_WIDTH
from flowmark.preservation.bridge import protect_source, restore_source
from flowmark.preservation.normalization import finalize_output, normalize_source
from flowmark.preservation.scanner import scan_protected_regions
from flowmark.transforms.doc_cleanups import doc_cleanups
from flowmark.transforms.doc_transforms import rewrite_text_across_inlines, rewrite_text_content
from flowmark.typography.ellipses import ellipses as apply_ellipses
from flowmark.typography.smartquotes import smart_quotes


def fill_markdown(
    markdown_text: str,
    dedent_input: bool = True,
    width: int = DEFAULT_WRAP_WIDTH,
    semantic: bool = False,
    cleanups: bool = False,
    smartquotes: bool = False,
    ellipses: bool = False,
    line_wrapper: LineWrapper | None = None,
    list_spacing: ListSpacing = ListSpacing.preserve,
) -> str:
    """
    Normalize and wrap Markdown text filling paragraphs to the full width.

    Wraps lines and adds line breaks within paragraphs and on
    best-guess estimations of sentences, to make diffs more readable.

    With `list_spacing="preserve"` (default), list spacing is preserved as authored.
    With `list_spacing="loose"`, all lists have blank lines between items.
    With `list_spacing="tight"`, lists are made tight where possible.

    `dedent_input=True` is an explicit convenience for direct docstring use. It dedents
    before source normalization. CLI and `reformat_text()` callers disable it so Markdown
    indentation reaches the parser unchanged.

    With `semantic` enabled, the line breaks are wrapped approximately
    by sentence boundaries, to make diffs more readable.

    Template tags (Markdoc, Jinja, HTML comments) are always treated atomically
    and never broken across lines.

    Preserves YAML frontmatter (delimited by --- lines) if present at the
    beginning of the document.
    """
    if line_wrapper is None:
        if semantic:
            line_wrapper = line_wrap_by_sentence(width=width, is_markdown=True)
        else:
            line_wrapper = line_wrap_to_width(width=width, is_markdown=True)

    if dedent_input:
        markdown_text = dedent(markdown_text)

    source = normalize_source(markdown_text)
    regions = scan_protected_regions(source)
    protected = protect_source(source, regions)

    # Frontmatter stays outside Marko, as before, but only after source normalization and
    # protection have established the complete document contract.
    frontmatter, parser_text = split_frontmatter(protected.text)
    if frontmatter:
        parser_text = parser_text.lstrip("\n")

    # Preprocess: ensure proper blank lines around block content within tags.
    # Protected bodies are tokens here, so preprocessing can inspect only unprotected gaps.
    parser_text = preprocess_tag_block_spacing(parser_text)

    # Parse and render.
    marko = flowmark_markdown(line_wrapper, list_spacing, _protected_source=protected)
    document = marko.parse(parser_text)
    if cleanups:
        doc_cleanups(document)
    if smartquotes:
        rewrite_text_across_inlines(document, smart_quotes)
    if ellipses:
        rewrite_text_content(document, apply_ellipses, coalesce_lines=True)
    rendered = marko.render(document)
    restored = restore_source(frontmatter + rendered, protected)
    return finalize_output(source, restored)
