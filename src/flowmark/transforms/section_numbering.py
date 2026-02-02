"""
Section numbering detection and renumbering for Markdown documents.

This module provides:
- Detection of numbered section conventions (e.g., "1. Intro", "1.1 Details")
- Inference of numbering style from existing content
- Automatic renumbering to maintain sequential order

Key concepts:
- A heading level qualifies for renumbering if 2/3+ of headings at that level
  have matching numeric prefixes (minimum 2 headings with prefixes)
- Numbered levels must be contiguous (H2+H3 is valid, H2+H4 gap is not)
- Single-H1 exception: when there's only one H1 (title), H2+ can be numbered
  independently without requiring H1 to be numbered
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

import re
from dataclasses import dataclass
from enum import Enum

# Module constants
MAX_HEADING_LEVELS = 6
"""Maximum number of heading levels supported (H1-H6)."""

TWO_THIRDS_THRESHOLD = 2 / 3
"""Minimum fraction of headings at a level that must be numbered to qualify."""

MIN_HEADINGS_FOR_INFERENCE = 2
"""Minimum number of headings required at a level to infer a convention."""

ALPHABET_SIZE = 26
"""Number of letters in the alphabet for alpha numbering."""


class NumberStyle(str, Enum):
    """Number style within a format component."""

    arabic = "arabic"  # 1, 2, 3, 10, 100
    roman_upper = "roman_upper"  # I, II, III, IV, V
    roman_lower = "roman_lower"  # i, ii, iii, iv, v
    alpha_upper = "alpha_upper"  # A, B, C, ... Z, AA, AB
    alpha_lower = "alpha_lower"  # a, b, c, ... z, aa, ab


def int_to_roman(n: int) -> str:
    """Convert an integer to uppercase Roman numeral string."""
    if n <= 0:
        raise ValueError("Roman numerals must be positive")
    result: list[str] = []
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
    result: list[str] = []
    while n > 0:
        n -= 1
        result.append(chr(ord("A") + (n % ALPHABET_SIZE)))
        n //= ALPHABET_SIZE
    return "".join(reversed(result))


def alpha_to_int(s: str) -> int:
    """Convert an alphabetic string to integer (A=1, B=2, ..., Z=26, AA=27, ...)."""
    s = s.upper()
    result = 0
    for char in s:
        result = result * ALPHABET_SIZE + (ord(char) - ord("A") + 1)
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
    else:  # style == NumberStyle.alpha_lower
        return int_to_alpha(value).lower()


def from_number(style: NumberStyle, text: str) -> int:
    """Convert a string representation back to an integer."""
    if style == NumberStyle.arabic:
        return int(text)
    elif style in (NumberStyle.roman_upper, NumberStyle.roman_lower):
        return roman_to_int(text)
    else:  # style in (NumberStyle.alpha_upper, NumberStyle.alpha_lower)
        return alpha_to_int(text)


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
        for i in range(MAX_HEADING_LEVELS - 1, -1, -1):
            if self.levels[i] is not None:
                return i + 1
        return 0

    @property
    def is_active(self) -> bool:
        """Whether this document qualifies for section renumbering."""
        return self.max_depth >= 1

    def __str__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Human-readable representation of the convention."""
        parts: list[str] = []
        for i, fmt in enumerate(self.levels):
            if fmt is not None:
                parts.append(f"H{i + 1}: {fmt.format_string()}")
        return ", ".join(parts) if parts else "none"


@dataclass
class ParsedPrefix:
    """
    Result of parsing a section number prefix from a heading.

    Examples:
    - "1. Introduction" -> ParsedPrefix(["1"], [arabic], ".", "Introduction")
    - "1.2 Details" -> ParsedPrefix(["1", "2"], [arabic, arabic], "", "Details")
    - "I.A Overview" -> ParsedPrefix(["I", "A"], [roman_upper, alpha_upper], "", "Overview")
    """

    components: list[str]  # Raw string components, e.g., ["1", "2"] or ["I", "A"]
    styles: list[NumberStyle]  # Inferred style for each component
    trailing: str  # Trailing character (".", ")", or "")
    title: str  # The heading text after the prefix


# Characters that can appear in Roman numerals
ROMAN_CHARS_UPPER = set("IVXLCDM")
ROMAN_CHARS_LOWER = set("ivxlcdm")


def infer_style(component: str) -> NumberStyle:
    """
    Infer the number style from a parsed component.

    The order of checks matters for ambiguous cases (e.g., "I" could be Roman 1 or Alpha).
    We check Roman before Alpha to handle these ambiguous single letters.

    Args:
        component: A single component string like "1", "I", "A", etc.

    Returns:
        The inferred NumberStyle for this component.
    """
    if component.isdigit():
        return NumberStyle.arabic
    # Check Roman before Alpha (handles ambiguous cases like "I", "C", "D")
    if all(c in ROMAN_CHARS_UPPER for c in component):
        return NumberStyle.roman_upper
    if all(c in ROMAN_CHARS_LOWER for c in component):
        return NumberStyle.roman_lower
    if component.isupper():
        return NumberStyle.alpha_upper
    if component.islower():
        return NumberStyle.alpha_lower
    return NumberStyle.arabic  # fallback


# Pattern components for matching section prefixes
_ARABIC = r"\d+"
_ROMAN_UPPER = r"[IVXLCDM]+"
_ROMAN_LOWER = r"[ivxlcdm]+"
_ALPHA_UPPER = r"[A-Z]+"
_ALPHA_LOWER = r"[a-z]+"

# Single component (any style)
_COMPONENT = rf"({_ARABIC}|{_ROMAN_UPPER}|{_ROMAN_LOWER}|{_ALPHA_UPPER}|{_ALPHA_LOWER})"

# Full number pattern: one or more components separated by dots
# with optional trailing . or )
# Captures: (full_number_with_dots)(trailing)(space+title)
_NUMBER_PATTERN = re.compile(rf"^({_COMPONENT}(?:\.{_COMPONENT})*)" r"([.\)])?" r"\s+" r"(.+)$")


def extract_section_prefix(text: str) -> ParsedPrefix | None:
    """
    Extract a section number prefix from heading text.

    Args:
        text: The heading text, e.g., "1. Introduction" or "1.2 Details"

    Returns:
        ParsedPrefix with components, styles, trailing, and title.
        Returns None if no valid prefix is found.

    Examples:
        >>> extract_section_prefix("1. Introduction")
        ParsedPrefix(["1"], [arabic], ".", "Introduction")
        >>> extract_section_prefix("1.2 Details")
        ParsedPrefix(["1", "2"], [arabic, arabic], "", "Details")
        >>> extract_section_prefix("Background")
        None
    """
    match = _NUMBER_PATTERN.match(text)
    if not match:
        return None

    full_number = match.group(1)
    trailing = match.group(len(match.groups()) - 1) or ""
    title = match.group(len(match.groups()))

    # Split by dots to get components
    components = full_number.split(".")

    # Infer style for each component
    styles = [infer_style(comp) for comp in components]

    return ParsedPrefix(
        components=components,
        styles=styles,
        trailing=trailing,
        title=title,
    )


def _are_prefixes_compatible(p1: ParsedPrefix, p2: ParsedPrefix) -> bool:
    """
    Check if two prefixes are compatible (same structure and styles).

    Two prefixes are compatible if:
    - They have the same number of components
    - Each component has the same style
    """
    if len(p1.components) != len(p2.components):
        return False
    if len(p1.styles) != len(p2.styles):
        return False
    for s1, s2 in zip(p1.styles, p2.styles, strict=True):
        if s1 != s2:
            return False
    return True


def _disambiguate_level_styles(
    prefixes: list[ParsedPrefix],
) -> list[ParsedPrefix]:
    """
    Apply level-wide disambiguation for Roman vs Alphabetic.

    If any heading at this level contains non-Roman letters (A, B, E, F, G, etc.),
    then all Roman-only letters (I, V, X, C, D, M) are reinterpreted as alphabetic.

    This handles cases like "A, B, C, D" where C and D might be misread as Roman.
    """
    if not prefixes:
        return prefixes

    # For each component position, check if any prefix has non-Roman letters
    num_components = len(prefixes[0].components)

    for pos in range(num_components):
        # Collect all styles at this position
        styles_at_pos = [p.styles[pos] for p in prefixes if pos < len(p.styles)]

        # Check if this position has a mix of Roman and non-Roman interpretations
        has_roman_upper = NumberStyle.roman_upper in styles_at_pos
        has_alpha_upper = NumberStyle.alpha_upper in styles_at_pos
        has_roman_lower = NumberStyle.roman_lower in styles_at_pos
        has_alpha_lower = NumberStyle.alpha_lower in styles_at_pos

        # If we have both Roman and Alpha at same position, convert all to Alpha
        if has_roman_upper and has_alpha_upper:
            # Convert all roman_upper to alpha_upper at this position
            for p in prefixes:
                if pos < len(p.styles) and p.styles[pos] == NumberStyle.roman_upper:
                    p.styles[pos] = NumberStyle.alpha_upper
        if has_roman_lower and has_alpha_lower:
            # Convert all roman_lower to alpha_lower at this position
            for p in prefixes:
                if pos < len(p.styles) and p.styles[pos] == NumberStyle.roman_lower:
                    p.styles[pos] = NumberStyle.alpha_lower

    return prefixes


def infer_format_for_level(headings: list[tuple[int, str]], level: int) -> SectionNumFormat | None:
    """
    Infer the section number format for a specific heading level.

    Applies the First-Two + Two-Thirds qualification rules:
    1. First two headings at this level must have matching numeric prefixes
    2. At least 2/3 (66%) of all headings at this level must have prefixes

    Args:
        headings: List of (level, text) tuples for all headings in the document.
        level: The heading level to analyze (1-6).

    Returns:
        SectionNumFormat if the level qualifies, None otherwise.
    """
    # Filter headings to this level
    level_headings = [(lvl, text) for lvl, text in headings if lvl == level]

    if len(level_headings) < MIN_HEADINGS_FOR_INFERENCE:
        return None

    # Parse prefixes for all headings at this level
    parsed: list[tuple[int, str, ParsedPrefix | None]] = []
    for lvl, text in level_headings:
        prefix = extract_section_prefix(text)
        parsed.append((lvl, text, prefix))

    # First-two rule: first two must both have prefixes
    if parsed[0][2] is None or parsed[1][2] is None:
        return None

    # Collect all valid prefixes
    valid_prefixes = [p[2] for p in parsed if p[2] is not None]

    # Apply level-wide disambiguation (Roman vs Alpha) BEFORE compatibility check
    valid_prefixes = _disambiguate_level_styles(valid_prefixes)

    # Two-thirds rule: at least 66% must have prefixes
    total = len(parsed)
    with_prefix = len(valid_prefixes)
    if with_prefix / total < TWO_THIRDS_THRESHOLD:
        return None

    # First-two rule: prefixes must be compatible (same structure and styles)
    # Check AFTER disambiguation
    first_prefix = valid_prefixes[0]
    second_prefix = valid_prefixes[1]

    if not _are_prefixes_compatible(first_prefix, second_prefix):
        return None

    # Build FormatComponents from the prefix structure
    # Component levels are calculated based on the heading level and number of components
    # For H2 with "1.1" (2 components): levels are 1, 2
    # For H2 with "1." (1 component): level is 2 (matches heading level)
    # For H3 with "1.1.1" (3 components): levels are 1, 2, 3
    num_components = len(first_prefix.styles)
    start_level = level - num_components + 1

    components: list[FormatComponent] = []
    for i, style in enumerate(first_prefix.styles):
        component_level = start_level + i
        components.append(FormatComponent(level=component_level, style=style))

    # Determine trailing character (use first prefix's trailing, normalized later)
    trailing = first_prefix.trailing

    return SectionNumFormat(components=components, trailing=trailing)


def infer_section_convention(
    headings: list[tuple[int, str]],
) -> SectionNumConvention:
    """
    Infer the complete section numbering convention for a document.

    Analyzes headings at each level (H1-H6) and returns a convention
    describing the numbering format at each level.

    Args:
        headings: List of (level, text) tuples for all headings in the document.

    Returns:
        SectionNumConvention with format for each level (or None for unnumbered levels).
    """
    levels: list[SectionNumFormat | None] = []

    for level in range(1, MAX_HEADING_LEVELS + 1):
        fmt = infer_format_for_level(headings, level)
        levels.append(fmt)

    return SectionNumConvention(
        levels=(levels[0], levels[1], levels[2], levels[3], levels[4], levels[5])
    )


def renumber_headings(
    headings: list[tuple[int, str]],
) -> list[tuple[int, str]]:
    """
    Top-level API to renumber section headings.

    Takes a list of (level, text) tuples and returns them with corrected
    section numbers, if the document qualifies for renumbering.

    Args:
        headings: List of (level, text) tuples representing headings.

    Returns:
        List of (level, text) tuples with renumbered headings.
        If the document doesn't qualify, returns the original list unchanged.
    """
    # Infer convention from headings
    convention = infer_section_convention(headings)

    # Apply hierarchical constraint (pass headings for single-H1 exception)
    convention = apply_hierarchical_constraint(convention, headings)

    # Normalize trailing characters
    convention = normalize_convention(convention)

    # If no active convention, return unchanged
    if not convention.is_active:
        return headings

    # Check for single-H1 situation
    h1_count = sum(1 for level, _ in headings if level == 1)
    single_h1 = h1_count == 1

    # Create renumberer and process headings
    renumberer = SectionRenumberer(convention, single_h1=single_h1)
    result: list[tuple[int, str]] = []

    for level, text in headings:
        fmt = convention.levels[level - 1]

        if fmt is None:
            # Level not numbered, pass through unchanged
            result.append((level, text))
        else:
            # Extract prefix from heading
            prefix = extract_section_prefix(text)
            if prefix is None:
                # Heading doesn't have a prefix, pass through unchanged
                result.append((level, text))
            else:
                # Renumber the heading
                new_text = renumberer.format_heading(level, prefix.title)
                result.append((level, new_text))

    return result


class SectionRenumberer:
    """
    Renumbers section headings according to a convention.

    Tracks counters for each heading level and generates sequential numbers.
    When a shallower heading is encountered, deeper level counters are reset.

    Usage:
        renumberer = SectionRenumberer(convention)
        new_h1 = renumberer.format_heading(1, "Introduction")  # "1. Introduction"
        new_h2 = renumberer.format_heading(2, "Background")    # "1.1 Background"
    """

    convention: SectionNumConvention
    counters: list[int]

    def __init__(self, convention: SectionNumConvention, *, single_h1: bool = False) -> None:
        """
        Initialize the renumberer with a convention.

        Args:
            convention: The section numbering convention to use.
            single_h1: If True, indicates the document has a single H1 heading.
                When H1 is not numbered but deeper levels reference H1 counter,
                the H1 counter is pre-initialized to 1.
        """
        self.convention = convention
        # Counters for each level (H1-H6), initialized to 0
        self.counters = [0] * MAX_HEADING_LEVELS

        # Handle single-H1 exception: if H1 is not numbered but deeper levels
        # reference H1 counter (e.g., H2 format is {h1}.{h2}), pre-initialize
        # the H1 counter to 1 so that H2s render as "1.1", "1.2", not "0.1", "0.2"
        if single_h1 and convention.levels[0] is None:
            # Check if any deeper level references H1 counter
            for fmt in convention.levels[1:]:
                if fmt is not None:
                    for comp in fmt.components:
                        if comp.level == 1:
                            self.counters[0] = 1
                            break
                    break

    def next_number(self, level: int) -> str:
        """
        Generate the next number for a heading level.

        Increments the counter for the level and resets all deeper levels.

        Args:
            level: Heading level (1-6).

        Returns:
            Formatted number string (e.g., "1.", "1.1", "II.A").
        """
        if level < 1 or level > MAX_HEADING_LEVELS:
            raise ValueError(f"Level must be 1-{MAX_HEADING_LEVELS}, got {level}")

        fmt = self.convention.levels[level - 1]
        if fmt is None:
            return ""

        # Increment this level's counter
        self.counters[level - 1] += 1

        # Reset all deeper level counters
        for i in range(level, MAX_HEADING_LEVELS):
            self.counters[i] = 0

        # Format the number using the convention
        return fmt.format_number(self.counters)

    def format_heading(self, level: int, title: str) -> str:
        """
        Format a complete heading with number and title.

        Args:
            level: Heading level (1-6).
            title: The heading text (without number prefix).

        Returns:
            Complete heading text (e.g., "1. Introduction").
            If the level is not numbered, returns just the title.
        """
        fmt = self.convention.levels[level - 1]
        if fmt is None:
            return title

        number = self.next_number(level)
        # Add space between number and title
        # The trailing char is already in the number (e.g., "1." or "1.1")
        if number:
            return f"{number} {title}"
        return title


def normalize_convention(
    convention: SectionNumConvention,
) -> SectionNumConvention:
    """
    Normalize a convention to use consistent trailing characters.

    Normalization rules:
    - Single-component formats (H1 style): trailing becomes "."
    - Multi-component formats (decimal style like "1.2"): trailing becomes ""

    Args:
        convention: The convention to normalize.

    Returns:
        A new convention with normalized trailing characters.
    """
    levels: list[SectionNumFormat | None] = []

    for fmt in convention.levels:
        if fmt is None:
            levels.append(None)
        else:
            # Single component (like "1.") gets trailing "."
            # Multi-component (like "1.2") gets no trailing
            if len(fmt.components) == 1:
                normalized_trailing = "."
            else:
                normalized_trailing = ""

            levels.append(
                SectionNumFormat(
                    components=fmt.components,
                    trailing=normalized_trailing,
                )
            )

    return SectionNumConvention(
        levels=(levels[0], levels[1], levels[2], levels[3], levels[4], levels[5])
    )


def apply_hierarchical_constraint(
    convention: SectionNumConvention,
    headings: list[tuple[int, str]] | None = None,
) -> SectionNumConvention:
    """
    Apply the hierarchical constraint to a convention.

    Numbered levels must be contiguous:
    - H1 + H2: valid
    - H1 + H2 + H3: valid
    - H1 + H3 (gap at H2): invalid, H3+ become None
    - H3 only (no H2): invalid, all become None

    Single-H1 exception: When there is only one H1 in the document (acting as title),
    H1 is excluded from the hierarchy check. This allows H2+ to be numbered
    independently without requiring H1 to be numbered.

    Args:
        convention: The raw convention from inference.
        headings: Optional list of (level, text) tuples to check for single-H1.

    Returns:
        A new convention with gaps filled (levels after first gap set to None).
    """
    levels = list(convention.levels)

    # Check for single-H1 exception
    start_level = 0  # Start checking from H1 by default
    if headings is not None:
        h1_count = sum(1 for level, _ in headings if level == 1)
        if h1_count == 1:
            # Single H1 exception: skip H1 from hierarchy check
            # H1 stays as-is (None if not qualified, format if qualified)
            # Start the contiguity check from H2
            start_level = 1

    # Find the first gap in the contiguous chain
    first_gap = start_level
    for i in range(start_level, MAX_HEADING_LEVELS):
        if levels[i] is None:
            first_gap = i
            break
        first_gap = i + 1

    # Set all levels from the first gap onward to None
    for i in range(first_gap, MAX_HEADING_LEVELS):
        levels[i] = None

    return SectionNumConvention(
        levels=(levels[0], levels[1], levels[2], levels[3], levels[4], levels[5])
    )
