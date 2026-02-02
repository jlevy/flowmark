"""
Section reference detection and renaming for Markdown documents.

This module provides:
- GitHub-compatible heading slug generation
- Section reference (internal link) detection
- Atomic section reference renaming

Key concepts:
- Slugs are generated using the GitHub slugging algorithm
- Duplicate heading text results in -1, -2, etc. suffixes
- Only internal fragment references (#slug) are modified
- External URLs and cross-file references are preserved
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from marko import inline

if TYPE_CHECKING:
    from marko.block import Document


def heading_to_slug(text: str) -> str:
    """
    Convert heading text to GitHub-compatible anchor slug.

    Implements the GitHub slugging algorithm:
    1. Lowercase
    2. Remove non-alphanumeric except hyphens/spaces
    3. Replace spaces with hyphens
    4. Collapse multiple hyphens
    5. Remove leading/trailing hyphens

    Args:
        text: The heading text (without # prefix).

    Returns:
        URL-safe anchor slug.
    """
    # Lowercase
    result = text.lower()

    # Remove characters that aren't alphanumeric, space, hyphen, or unicode letters
    # Keep: letters (including unicode), digits, spaces, hyphens
    cleaned: list[str] = []
    for char in result:
        if char.isalnum() or char == " " or char == "-":
            cleaned.append(char)
        elif unicodedata.category(char).startswith("L"):
            # Unicode letter category
            cleaned.append(char)
    result = "".join(cleaned)

    # Replace spaces with hyphens
    result = result.replace(" ", "-")

    # Collapse multiple hyphens into one
    result = re.sub(r"-+", "-", result)

    # Remove leading/trailing hyphens
    result = result.strip("-")

    return result


@dataclass
class GithubSlugger:
    """
    Stateful slugger that tracks duplicates within a document.

    GitHub appends -1, -2, etc. when the same slug appears multiple times.
    This class tracks occurrences to generate correct unique slugs.
    """

    _seen: dict[str, int] = field(default_factory=dict)

    def slug(self, text: str) -> str:
        """
        Generate a unique slug for the given heading text.

        Tracks duplicates and appends -1, -2, etc. as needed.

        Args:
            text: The heading text.

        Returns:
            Unique slug for this heading within the document.
        """
        base_slug = heading_to_slug(text)

        if base_slug not in self._seen:
            self._seen[base_slug] = 0
            return base_slug

        # Increment count and return with suffix
        self._seen[base_slug] += 1
        return f"{base_slug}-{self._seen[base_slug]}"

    def reset(self) -> None:
        """Clear duplicate tracking for a new document."""
        self._seen.clear()


@dataclass
class SectionRef:
    """
    A reference to a section within the document.

    Represents a Markdown link that points to an internal anchor (#slug).
    """

    element: inline.Link
    """The Marko link element."""

    slug: str
    """The fragment identifier (without the # prefix)."""

    is_internal: bool
    """True if this is a pure internal reference (#slug only)."""


def _is_internal_reference(dest: str) -> bool:
    """
    Check if a link destination is an internal section reference.

    Internal references start with # and have no path component.

    Args:
        dest: The link destination URL.

    Returns:
        True if this is an internal #slug reference.
    """
    if not dest.startswith("#"):
        return False
    # Pure internal references have no path (just #slug)
    # Cross-file references like ./other.md#slug don't start with #
    return True


def find_section_references(doc: Document) -> list[SectionRef]:
    """
    Find all internal section references in a document.

    Traverses the document tree to find all links with destinations
    starting with # (internal anchors). External URLs and cross-file
    references are excluded.

    Args:
        doc: The Marko Document to search.

    Returns:
        List of SectionRef objects for each internal link found.
    """
    refs: list[SectionRef] = []

    def visit(element: object) -> None:
        if isinstance(element, inline.Link):
            dest = element.dest
            if _is_internal_reference(dest):
                # Extract slug (remove the # prefix)
                slug = dest[1:]
                refs.append(SectionRef(element=element, slug=slug, is_internal=True))

        # Recurse into children
        children = getattr(element, "children", None)
        if isinstance(children, list):
            for child in children:  # pyright: ignore[reportUnknownVariableType]
                visit(child)  # pyright: ignore[reportUnknownArgumentType]

    visit(doc)
    return refs


@dataclass
class SectionRename:
    """A single section rename operation."""

    old_slug: str
    """The original slug to find."""

    new_slug: str
    """The new slug to replace with."""


@dataclass
class RenameResult:
    """
    Result of a section reference rename operation.

    This is a clean data structure that collects all results and warnings.
    Logging (if desired) happens separately after processing is complete,
    NOT embedded in the rename logic. This separation of concerns keeps
    the core logic pure and testable.
    """

    links_modified: int
    """Number of links that were updated."""

    warnings: list[str]
    """Warnings for unmatched references or other issues."""


def rename_section_references(
    doc: Document,
    renames: list[SectionRename],
    *,
    strict: bool = False,
) -> RenameResult:
    """
    Atomically rename all section references in a document.

    Processes all renames in a single pass, allowing for swaps
    (e.g., section A → B and B → A simultaneously).

    This function modifies the document in place.

    Args:
        doc: The Marko document tree.
        renames: List of (old_slug, new_slug) pairs to apply.
        strict: If True, raise error on invalid/unmatched references.
                If False (default), skip invalid references with warnings.

    Returns:
        RenameResult with count of modified links and any warnings.
    """
    # Build atomic old→new mapping (lowercase for case-insensitive matching)
    rename_map: dict[str, str] = {}
    for rename in renames:
        rename_map[rename.old_slug.lower()] = rename.new_slug

    # Find all internal section references
    refs = find_section_references(doc)

    links_modified = 0
    warnings: list[str] = []

    for ref in refs:
        slug_lower = ref.slug.lower()

        if slug_lower in rename_map:
            # Apply the rename
            new_slug = rename_map[slug_lower]
            ref.element.dest = f"#{new_slug}"
            links_modified += 1
        else:
            # Unknown reference - add warning or raise error
            msg = f"Link #{ref.slug} not found in rename list"
            if strict:
                raise ValueError(msg)
            warnings.append(msg)

    return RenameResult(links_modified=links_modified, warnings=warnings)
