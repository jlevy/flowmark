"""
Section numbering detection and renumbering for Markdown documents.

This module provides:
- Detection of numbered section conventions (e.g., "1. Intro", "1.1 Details")
- Inference of numbering style from existing content
- Automatic renumbering to maintain sequential order

Key concepts:
- A heading level qualifies for renumbering if 2/3+ of headings at that level
  have matching numeric prefixes (minimum 2 headings with prefixes)
- Conventions must be contiguous from H1 (H1, H1+H2, H1+H2+H3, etc.)
- Trailing separators are normalized to periods (e.g., "1)" -> "1.")
- Unnumbered headings pass through unchanged

Usage:
    from flowmark.transforms.section_numbering import (
        infer_section_convention,
        SectionRenumberer,
    )

    # Infer convention from document headings
    convention = infer_section_convention(headings)

    # Create renumberer and apply to headings
    if convention.is_active:
        renumberer = SectionRenumberer(convention)
        for level, title in headings:
            new_heading = renumberer.format_heading(level, title)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NumberStyle(str, Enum):
    """Number style within a format component."""

    arabic = "arabic"  # 1, 2, 3, 10, 100
    roman_upper = "roman_upper"  # I, II, III, IV, V
    roman_lower = "roman_lower"  # i, ii, iii, iv, v
    alpha_upper = "alpha_upper"  # A, B, C, ... Z, AA, AB
    alpha_lower = "alpha_lower"  # a, b, c, ... z, aa, ab


# === Number Conversion Functions ===


def int_to_roman(n: int) -> str:
    """Convert an integer to uppercase Roman numeral string."""
    if n <= 0:
        raise ValueError("Roman numerals must be positive")
    result = []
    for value, numeral in [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]:
        while n >= value:
            result.append(numeral)
            n -= value
    return "".join(result)


def roman_to_int(s: str) -> int:
    """Convert a Roman numeral string to integer."""
    s = s.upper()
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    result = 0
    prev = 0
    for char in reversed(s):
        curr = values.get(char, 0)
        if curr < prev:
            result -= curr
        else:
            result += curr
        prev = curr
    return result


def int_to_alpha(n: int) -> str:
    """Convert an integer to uppercase alphabetic string (A, B, ..., Z, AA, AB, ...)."""
    if n <= 0:
        raise ValueError("Alpha values must be positive")
    result = []
    while n > 0:
        n -= 1
        result.append(chr(ord("A") + (n % 26)))
        n //= 26
    return "".join(reversed(result))


def alpha_to_int(s: str) -> int:
    """Convert an alphabetic string to integer (A=1, B=2, ..., Z=26, AA=27, ...)."""
    s = s.upper()
    result = 0
    for char in s:
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result


def to_number(style: NumberStyle, value: int) -> str:
    """Convert an integer to its string representation in the given style."""
    if style == NumberStyle.arabic:
        return str(value)
    elif style == NumberStyle.roman_upper:
        return int_to_roman(value)
    elif style == NumberStyle.roman_lower:
        return int_to_roman(value).lower()
    elif style == NumberStyle.alpha_upper:
        return int_to_alpha(value)
    elif style == NumberStyle.alpha_lower:
        return int_to_alpha(value).lower()
    else:
        return str(value)


def from_number(style: NumberStyle, text: str) -> int:
    """Convert a string representation back to an integer."""
    if style == NumberStyle.arabic:
        return int(text)
    elif style in (NumberStyle.roman_upper, NumberStyle.roman_lower):
        return roman_to_int(text)
    elif style in (NumberStyle.alpha_upper, NumberStyle.alpha_lower):
        return alpha_to_int(text)
    else:
        return int(text)


# === Data Structures ===


@dataclass
class FormatComponent:
    """
    One component of a section number format.

    Examples:
    - FormatComponent(level=1, style=NumberStyle.arabic) -> "{h1:arabic}"
    - FormatComponent(level=2, style=NumberStyle.roman_upper) -> "{h2:roman_upper}"
    - FormatComponent(level=3, style=NumberStyle.alpha_lower) -> "{h3:alpha_lower}"
    """

    level: int  # 1-6 for H1-H6
    style: NumberStyle  # arabic, roman_upper/lower, alpha_upper/lower


@dataclass
class SectionNumFormat:
    """
    The inferred format for section numbers at a given heading level.

    Examples:
    - H1: components=[h1:arabic], trailing="." -> "1.", "2.", "3."
    - H2: components=[h1:arabic, h2:arabic], trailing="" -> "1.1", "1.2", "2.1"
    - H3: components=[h1:arabic, h2:arabic, h3:arabic], trailing="" -> "1.1.1"
    """

    # The components that make up the number (e.g., [h1, h2] for "1.2")
    components: list[FormatComponent]

    # The trailing character after the final number (typically "." for H1, "" for H2+)
    trailing: str

    def format_string(self) -> str:
        """
        Return the format as a string like "{h1:arabic}.{h2:arabic}".
        """
        parts = [f"{{h{c.level}:{c.style.value}}}" for c in self.components]
        result = ".".join(parts)
        if self.trailing:
            result += self.trailing
        return result

    def format_number(self, counters: list[int]) -> str:
        """
        Format counters according to this format.

        Args:
            counters: List of 6 integers, one for each heading level (H1-H6).

        Returns:
            Formatted number string, e.g., "2.3" for counters=[2, 3, 0, 0, 0, 0]

        Example:
            counters=[2, 3, 0, 0, 0, 0] with H2 format -> "2.3" (arabic)
            counters=[2, 3, 0, 0, 0, 0] with H2 format -> "II.C" (roman_upper + alpha_upper)
        """
        parts = [to_number(c.style, counters[c.level - 1]) for c in self.components]
        return ".".join(parts) + self.trailing


@dataclass
class SectionNumConvention:
    """
    Represents the inferred numbering conventions for a document's sections.

    Contains the format for each heading level (H1-H6).
    None means the level is not numbered.
    """

    # Format for each heading level (index 0 = H1, index 5 = H6)
    # None means the level is not numbered
    levels: tuple[
        SectionNumFormat | None,  # H1
        SectionNumFormat | None,  # H2
        SectionNumFormat | None,  # H3
        SectionNumFormat | None,  # H4
        SectionNumFormat | None,  # H5
        SectionNumFormat | None,  # H6
    ]

    @property
    def max_depth(self) -> int:
        """The deepest heading level with numbering (1-6), or 0 if no numbering."""
        for i in range(5, -1, -1):
            if self.levels[i] is not None:
                return i + 1
        return 0

    @property
    def is_active(self) -> bool:
        """Whether this document qualifies for section renumbering."""
        return self.max_depth >= 1

    def __str__(self) -> str:
        """Human-readable representation of the convention."""
        parts = []
        for i, fmt in enumerate(self.levels):
            if fmt is not None:
                parts.append(f"H{i + 1}: {fmt.format_string()}")
        return ", ".join(parts) if parts else "none"
