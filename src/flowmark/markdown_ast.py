"""
Public, read-only helpers for walking a parsed Markdown AST and extracting inline
structure (currently links).

Parse documents with :func:`flowmark.flowmark_markdown` (GFM + footnote), then use these
helpers instead of re-implementing marko tree walks that must track GFM/footnote element
types.

**Identity, not spans.** A *span* here means a slice of source text plus its
`[start, end)` character offsets. marko does not record source offsets for inline
elements, so :func:`extract_links` returns link *text/url/title* but no span. Recovering
one is a source-mapping problem the consumer owns: duplicate link text, reference links,
escaped text, and nested inline markup mean it is not simply "find the link text" — it
must be reconciled against the original source.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import NamedTuple, cast

from marko import inline
from marko.block import Document
from marko.element import Element


class Link(NamedTuple):
    """
    A link found in a Markdown document.

    `text` is the rendered link text (empty for autolinks/bare URLs, where the URL is the
    text). `url` is the destination. `title` is the optional link title. There is no
    source span (no `[start, end)` offsets): marko does not position inline elements, so a
    consumer that needs offsets recovers them itself (see module docstring).
    """

    text: str
    url: str
    title: str | None


def walk_elements(element: Element) -> Iterator[Element]:
    """
    Depth-first iteration over all descendant elements of `element`, in document order.

    Read-only: yields each child/descendant element without modifying the tree. The root
    `element` itself is not yielded. This is a generic tree walk — it yields block
    elements, inline elements, and the raw text inside code blocks alike, so callers
    filter by element type.
    """
    children = getattr(element, "children", None)
    if isinstance(children, list):
        for child in cast("list[Element]", children):
            yield child
            yield from walk_elements(child)


def _inline_text(element: Element) -> str:
    """Concatenate the plain text content of an element's inline subtree."""
    children = getattr(element, "children", None)
    if isinstance(children, str):
        return children
    if isinstance(children, list):
        return "".join(_inline_text(child) for child in cast("list[Element]", children))
    return ""


def extract_links(
    doc: Document,
    *,
    include_autolinks: bool = True,
    include_images: bool = False,
) -> list[Link]:
    """
    Extract all links from a parsed Markdown document, in document order.

    Reflects what Markdown actually treats as a link (reference links resolved, escapes
    honored), unlike the regex patterns in :mod:`flowmark.atomic_spans`.

    :param include_autolinks: include ``<url>`` autolinks and GFM bare-URL autolinks
        (their `text` equals the URL). GFM bare URLs (`gfm_elements.Url`) subclass
        `inline.AutoLink`, so both are covered by the one autolink case.
    :param include_images: include images (``![alt](url)``); off by default since images
        are not navigable links.
    """
    links: list[Link] = []
    for element in walk_elements(doc):
        if isinstance(element, inline.Link):
            links.append(Link(_inline_text(element), element.dest, element.title))
        elif isinstance(element, inline.Image):
            if include_images:
                links.append(Link(_inline_text(element), element.dest, element.title))
        elif isinstance(element, inline.AutoLink):
            if include_autolinks:
                # `dest` carries the scheme (e.g. `mailto:` for `<user@example.com>`);
                # the display text is the rendered link text. Autolinks have no title.
                links.append(Link(_inline_text(element), element.dest, None))
    return links


__all__ = (
    "Link",
    "walk_elements",
    "extract_links",
)
