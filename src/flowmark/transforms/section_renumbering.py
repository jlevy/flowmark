"""
Section renumbering transform for Marko document trees.

This module provides the bridge between the section_numbering logic
and the Marko document tree.
"""

from __future__ import annotations

from marko import block, inline
from marko.block import Document

from flowmark.transforms.section_numbering import (
    SectionRenumberer,
    apply_hierarchical_constraint,
    extract_section_prefix,
    infer_section_convention,
    normalize_convention,
)


def _get_heading_text(heading: block.Heading) -> str:
    """
    Extract the plain text from a heading element.

    Handles inline elements like RawText, Emphasis, etc.
    """
    text_parts: list[str] = []

    def collect_text(element: object) -> None:
        if isinstance(element, inline.RawText):
            assert isinstance(element.children, str)
            text_parts.append(element.children)
        else:
            children = getattr(element, "children", None)
            if isinstance(children, list):
                for child in children:  # pyright: ignore[reportUnknownVariableType]
                    collect_text(child)  # pyright: ignore[reportUnknownArgumentType]
            elif isinstance(children, str):
                text_parts.append(children)

    collect_text(heading)
    return "".join(text_parts)


def _set_heading_text(heading: block.Heading, new_text: str) -> None:
    """
    Set the text of a heading element.

    Replaces the first RawText node with the new text.
    If no RawText node exists, creates one.
    """

    # Find the first RawText node and replace its content
    def find_and_replace(element: object) -> bool:
        if isinstance(element, inline.RawText):
            element.children = new_text
            return True
        else:
            children = getattr(element, "children", None)
            if isinstance(children, list):
                for child in children:  # pyright: ignore[reportUnknownVariableType]
                    if find_and_replace(child):  # pyright: ignore[reportUnknownArgumentType]
                        return True
        return False

    # Try to find and replace existing RawText
    if not find_and_replace(heading):
        # If no RawText found, create one by setting children directly
        # We create an object that acts like RawText
        raw_text = inline.RawText.__new__(inline.RawText)
        raw_text.children = new_text
        heading.children = [raw_text]


def apply_section_renumbering(doc: Document) -> None:
    """
    Apply section renumbering to a Marko document tree.

    This function:
    1. Collects all headings from the document
    2. Infers the numbering convention
    3. Renumbers headings according to the convention

    Modifies the document in place.

    Args:
        doc: The Marko Document to process.
    """
    # Step 1: Collect all headings
    headings: list[tuple[int, str, block.Heading]] = []

    def collect_headings(element: object) -> None:
        if isinstance(element, block.Heading):
            text = _get_heading_text(element)
            headings.append((element.level, text, element))
        else:
            children = getattr(element, "children", None)
            if isinstance(children, list):
                for child in children:  # pyright: ignore[reportUnknownVariableType]
                    collect_headings(child)  # pyright: ignore[reportUnknownArgumentType]

    collect_headings(doc)

    if not headings:
        return

    # Step 2: Infer convention
    heading_tuples = [(level, text) for level, text, _ in headings]
    convention = infer_section_convention(heading_tuples)
    # Pass heading_tuples for single-H1 exception check
    convention = apply_hierarchical_constraint(convention, heading_tuples)
    convention = normalize_convention(convention)

    if not convention.is_active:
        return

    # Check for single-H1 situation
    h1_count = sum(1 for level, _, _ in headings if level == 1)
    single_h1 = h1_count == 1

    # Step 3: Renumber headings
    renumberer = SectionRenumberer(convention, single_h1=single_h1)

    for level, text, heading_elem in headings:
        fmt = convention.levels[level - 1]

        if fmt is None:
            # Level not numbered, leave unchanged
            continue

        # Extract prefix from heading
        prefix = extract_section_prefix(text)
        if prefix is None:
            # Heading doesn't have a prefix, leave unchanged
            continue

        # Renumber the heading
        new_text = renumberer.format_heading(level, prefix.title)
        _set_heading_text(heading_elem, new_text)
