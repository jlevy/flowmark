"""
Section renumbering transform for Markdown documents.

This transform automatically renumbers section headings to maintain sequential order
and updates internal section references (#slug links) to match the new heading slugs.

ACTIVATION
----------
The transform activates when a heading level "qualifies" for renumbering:
- At least 2/3 of headings at that level must have recognized numeric prefixes
- Minimum 2 headings with prefixes required at that level
- Each level is evaluated independently

RECOGNIZED PREFIX STYLES
------------------------
- Decimal: 1, 2, 3 or 1., 2., 3.
- Roman lowercase: i, ii, iii, iv, v...
- Roman uppercase: I, II, III, IV, V...
- Alphabetic lowercase: a, b, c... z, aa, ab...
- Alphabetic uppercase: A, B, C... Z, AA, AB...
- Hierarchical: 1.1, 1.2, 2.1 or 1.a, 1.b, 2.a (parent number + child style)

Separators (., ), :, or space) are normalized to periods in output.

HIERARCHICAL CONSTRAINT
-----------------------
Numbered levels must be contiguous—no gaps allowed:
- H1 + H2: valid
- H1 + H2 + H3: valid
- H2 + H4 (gap at H3): H4 will NOT be renumbered
- H3 alone (no H2): will NOT be renumbered

SINGLE-H1 EXCEPTION
-------------------
When there is exactly one H1 heading (acting as document title), that H1 is excluded
from the hierarchical constraint. This allows H2+ to be numbered independently:
- "# My Title" + "## 1. Intro" + "## 3. Details" → H2s renumbered to 1, 2
- The single H1 passes through unchanged (whether numbered or not)

REFERENCE RENAMING
------------------
Internal section references are automatically updated to match new slugs:
- "#3-design" → "#2-design" (when "## 3. Design" becomes "## 2. Design")
- Uses GitHub-compatible slug algorithm (lowercase, spaces→hyphens, special chars removed)
- Cross-file references ("./other.md#section") are NOT modified
- External URLs are NOT modified
- Unknown references generate warnings in RenameResult but are not modified

PASS-THROUGH BEHAVIOR
---------------------
The following pass through unchanged:
- Headings without recognized numeric prefixes
- Headings at levels that don't qualify (below 2/3 threshold)
- Headings at levels with gaps in the hierarchy
- The single H1 when acting as document title

EXAMPLE
-------
Input:
    # My Document
    ## 1. Introduction
    ## 3. Design
    See [Design](#3-design) for details.
    ## 5. Conclusion

Output:
    # My Document
    ## 1. Introduction
    ## 2. Design
    See [Design](#2-design) for details.
    ## 3. Conclusion
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
from flowmark.transforms.section_references import (
    RenameResult,
    SectionRename,
    heading_to_slug,
    rename_section_references,
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


def apply_section_renumbering(
    doc: Document,
) -> RenameResult | None:
    """
    Apply section renumbering to a Marko document tree.

    This function:
    1. Collects all headings from the document
    2. Infers the numbering convention
    3. Renumbers headings according to the convention
    4. Updates internal section references to match new slugs

    Modifies the document in place.

    Returns:
        RenameResult with count of modified links and warnings,
        or None if the document doesn't qualify for renumbering.
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
        return None

    # Step 2: Infer convention
    heading_tuples = [(level, text) for level, text, _ in headings]
    convention = infer_section_convention(heading_tuples)
    # Pass heading_tuples for single-H1 exception check
    convention = apply_hierarchical_constraint(convention, heading_tuples)
    convention = normalize_convention(convention)

    if not convention.is_active:
        return None

    # Check for single-H1 situation
    h1_count = sum(1 for level, _, _ in headings if level == 1)
    single_h1 = h1_count == 1

    # Step 3: Renumber headings and collect renames
    renumberer = SectionRenumberer(convention, single_h1=single_h1)
    renames: list[SectionRename] = []

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

        # Calculate old and new slugs before renumbering
        old_slug = heading_to_slug(text)

        # Renumber the heading
        new_text = renumberer.format_heading(level, prefix.title)
        new_slug = heading_to_slug(new_text)

        # Only add rename if slug actually changed
        if old_slug != new_slug:
            renames.append(SectionRename(old_slug=old_slug, new_slug=new_slug))

        _set_heading_text(heading_elem, new_text)

    # Step 4: Rename section references to match new slugs
    return rename_section_references(doc, renames)
