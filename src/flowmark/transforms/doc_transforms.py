from __future__ import annotations

from collections.abc import Callable

from marko import block, inline
from marko.block import Document
from marko.element import Element
from marko.ext import footnote
from marko.ext.gfm import elements as gfm_elements

ContainerElement = (
    block.Document,
    block.Quote,
    block.List,
    block.ListItem,
    block.Paragraph,  # Paragraphs contain inline elements
    block.Heading,  # Already handled, but include for completeness if structure changes
    inline.Emphasis,
    inline.StrongEmphasis,
    inline.Link,
    footnote.FootnoteDef,  # Footnote definitions contain paragraphs and other elements
    gfm_elements.Table,  # GFM tables contain rows
    gfm_elements.TableRow,  # Table rows contain cells
    gfm_elements.TableCell,  # Table cells contain inline elements
    gfm_elements.Strikethrough,  # Strikethrough contains inline elements
)

# Inline scopes are elements whose children are inline elements (RawText, CodeSpan,
# Emphasis, etc.) that should be processed together for cross-inline-element rewrites.
InlineScope = (
    block.Paragraph,
    block.Heading,
    gfm_elements.TableCell,
)


def transform_tree(element: Element, transformer: Callable[[Element], None]) -> None:
    """
    Recursively traverse the element tree and apply a transformer function to each node.
    """
    transformer(element)

    # Recursively process children for known container types
    if isinstance(element, ContainerElement):
        # Now we know element has a .children attribute that's a Sequence[Element] or str
        # We only care about processing Element children
        if isinstance(element.children, list):
            # Create a copy for safe iteration if modification occurs
            current_children = list(element.children)
            for child in current_children:
                transform_tree(child, transformer)


def coalesce_raw_text_nodes(doc: Document) -> None:
    """
    Coalesce adjacent RawText nodes that are separated only by LineBreak elements.

    This is useful for smart quotes processing which needs to see text that spans
    across line breaks as a single unit.
    """
    from flowmark.transforms.doc_transforms import transform_tree

    def transformer(element: Element) -> None:
        if hasattr(element, "children") and isinstance(element.children, list):  # pyright: ignore
            new_children: list[Element] = []
            i = 0
            children: list[Element] = element.children  # pyright: ignore
            while i < len(children):
                child = children[i]

                # If this is a RawText node, look ahead for a pattern of
                # RawText -> LineBreak -> RawText and coalesce them
                if isinstance(child, inline.RawText):
                    coalesced_text = child.children
                    j = i + 1

                    # Look for pattern: RawText, LineBreak, RawText, LineBreak, ...
                    while j + 1 < len(children):
                        next_elem = children[j]
                        following_elem = children[j + 1] if j + 1 < len(children) else None

                        if (
                            isinstance(next_elem, inline.LineBreak)
                            and next_elem.soft
                            and isinstance(following_elem, inline.RawText)
                        ):
                            # Coalesce: add newline and the next text
                            coalesced_text += "\n" + following_elem.children
                            j += 2  # Skip the LineBreak and RawText we just consumed
                        else:
                            break

                    # Create new RawText node with coalesced content
                    if j > i + 1:  # We coalesced something
                        child.children = coalesced_text
                        new_children.append(child)
                        i = j  # Skip all the nodes we coalesced
                    else:
                        new_children.append(child)
                        i += 1
                else:
                    new_children.append(child)
                    i += 1

            element.children = new_children  # pyright: ignore[reportAttributeAccessIssue]

    transform_tree(doc, transformer)


def rewrite_text_content(
    doc: Document, rewrite_func: Callable[[str], str], *, coalesce_lines: bool = False
) -> None:
    """
    Apply a string rewrite function to all `RawText` nodes that are not part of
    code blocks.

    This function modifies the Marko document tree in place.
    It traverses the document and applies `string_rewrite_func` to the content
    of `marko.inline.RawText` elements. It skips text within any kind of code
    block (`FencedCode`, `CodeBlock`, `CodeSpan`).

    Args:
        doc: The document to process
        rewrite_func: Function to apply to each RawText node's content
        coalesce_lines: If True, coalesce adjacent RawText nodes separated by
            LineBreak elements before applying the rewrite function. This is
            useful for functions like smart quotes that need to see text spans
            across line breaks as a single unit.
    """
    if coalesce_lines:
        coalesce_raw_text_nodes(doc)

    def transformer(element: Element) -> None:
        if isinstance(element, inline.RawText):
            assert isinstance(element.children, str)
            element.children = rewrite_func(element.children)

    transform_tree(doc, transformer)


def _collect_inline_segments(
    element: Element,
) -> list[tuple[str, inline.RawText | None]]:
    """
    Collect text segments from inline elements within an inline scope.

    Returns a list of (text, node_or_None) tuples. RawText nodes have their
    node reference stored (mutable segments). All other inline element text
    is included for context but marked as None (immutable segments).
    """
    segments: list[tuple[str, inline.RawText | None]] = []

    if isinstance(element, inline.RawText):
        assert isinstance(element.children, str)
        segments.append((element.children, element))
    elif isinstance(element, inline.CodeSpan):
        # Include code span content for context (helps regex see surrounding text)
        # but mark as immutable — code content is never modified.
        assert isinstance(element.children, str)
        segments.append((element.children, None))
    elif isinstance(element, inline.LineBreak):
        segments.append(("\n", None))
    elif isinstance(element, inline.Literal):
        # Escaped characters — include for context but don't modify.
        assert isinstance(element.children, str)
        segments.append((element.children, None))
    elif isinstance(element, inline.InlineHTML):
        assert isinstance(element.children, str)
        segments.append((element.children, None))
    elif hasattr(element, "children") and isinstance(element.children, list):  # pyright: ignore[reportAttributeAccessIssue]
        # Recursive container (Emphasis, StrongEmphasis, Link, Strikethrough, etc.)
        children: list[Element] = element.children  # pyright: ignore[reportAttributeAccessIssue]
        for child in children:
            segments.extend(_collect_inline_segments(child))
    elif hasattr(element, "children") and isinstance(element.children, str):  # pyright: ignore[reportAttributeAccessIssue]
        # Any other element with string content — include for context.
        segments.append((element.children, None))  # pyright: ignore[reportAttributeAccessIssue]

    return segments


def rewrite_text_across_inlines(doc: Document, rewrite_func: Callable[[str], str]) -> None:
    """
    Apply a length-preserving rewrite function across all inline elements within
    each inline scope (Paragraph, Heading, TableCell).

    Unlike `rewrite_text_content` which processes each RawText node independently,
    this function concatenates all text within an inline scope and applies the
    rewrite function to the composite text. This allows the rewrite function to
    handle patterns (like quote pairs) that span across inline elements such as
    code spans, emphasis, or links.

    Changes are mapped back only to RawText nodes; text from CodeSpan, InlineHTML,
    Literal, etc. is used for context but never modified.

    The rewrite function must be length-preserving (each input character maps to
    exactly one output character). This is true for smart_quotes which replaces
    ASCII quotes (1 char) with Unicode typographic quotes (1 char).

    Line coalescing (merging adjacent RawText nodes separated by soft LineBreaks)
    is performed automatically before processing.
    """
    # Coalesce adjacent RawText nodes across soft line breaks so the rewrite
    # function can see text spanning line breaks as a single unit.
    coalesce_raw_text_nodes(doc)

    def transformer(element: Element) -> None:
        if not isinstance(element, InlineScope):
            return

        if not hasattr(element, "children") or not isinstance(element.children, list):
            return

        # Collect all inline segments from this scope
        segments: list[tuple[str, inline.RawText | None]] = []
        for child in element.children:
            segments.extend(_collect_inline_segments(child))

        if not segments:
            return

        # Build composite text from all segments
        composite = "".join(text for text, _ in segments)

        if not composite:
            return

        # Apply rewrite to the full composite text
        converted = rewrite_func(composite)

        assert len(converted) == len(composite), (
            f"Rewrite function must be length-preserving: "
            f"input length {len(composite)} != output length {len(converted)}"
        )

        # Map changes back only to mutable (RawText) segments
        pos = 0
        for text, node in segments:
            segment_len = len(text)
            if node is not None:
                node.children = converted[pos : pos + segment_len]
            pos += segment_len

    transform_tree(doc, transformer)
