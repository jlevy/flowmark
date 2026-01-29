# Plan Spec: Section Renumbering (`--renumber-sections` Option)

## Purpose

This is a technical design doc for adding a `--renumber-sections` CLI option to Flowmark
that automatically renumbers section headings (H1-H6) when they follow a consistent
numeric prefix convention.

**Core Concept**: If all sections up to a given heading level have numeric prefixes, the
document "qualifies" for section renumbering, and Flowmark will auto-renumber them based
on the document's outline structure.

## Background

Many documents use numbered section headings for organization:

```markdown
# 1. Introduction
## 1.1 Background
## 1.2 Motivation
# 2. Design
## 2.1 Architecture
### 2.1.1 Components
```

When editing such documents, section numbers can become inconsistent:
- Inserting a new section requires manual renumbering of all subsequent sections
- Moving sections breaks the numbering sequence
- Removing sections leaves gaps in numbering

**Current State**: Flowmark normalizes Markdown formatting but does not modify heading
content. This feature would add opt-in heading renumbering.

**Analogy**: Similar to how Markdown processors auto-number ordered lists (`1.`, `2.`,
`3.`), this feature would auto-number section headings based on their hierarchical
structure.

## Summary of Task

Add a `--renumber-sections` CLI flag that:

1. Detects if a document uses numbered section headings
2. Infers the numbering conventions from the existing content
3. Renumbers sections to maintain consistent sequential numbering

This will be exposed as:
- CLI: `--renumber-sections` (boolean flag, default: disabled)
- CLI: Included in `--auto` flag
- API: `renumber_sections: bool = False` parameter

## Detection Logic

### Per-Level Analysis

For each heading level (H1-H6), we analyze whether a **sufficient majority** of headings
have numeric prefixes. If they do, we infer the numbering style (e.g., `arabic`,
`roman_upper`, `alpha_lower`) and format structure.

### Qualification Rule (First-Two + Two-Thirds)

A heading level qualifies for renumbering if **both** conditions are met:

1. **First-two rule**: The **first two headings** at that level (in document order) must
   have matching numeric prefixes with the same pattern
2. **Two-thirds rule**: At least **2/3 (66%)** of all headings at that level must have
   a matching numeric prefix

This ensures:
- We always have at least 2 numbered headings (from the first-two rule)
- The document clearly follows a numbered pattern (from the two-thirds rule)
- Occasional missing numbers don't break renumbering

| Total Headings | First Two | 2/3 Threshold | Qualifies? |
|----------------|-----------|---------------|------------|
| 2 | Both numbered | 2/2 | ✓ |
| 3 | Both numbered | 2/3 | ✓ |
| 3 | First numbered, second not | - | ✗ (first-two fails) |
| 4 | Both numbered | 3/4 | ✓ |
| 4 | Both numbered | 2/4 | ✗ (2/3 fails) |
| 5 | Both numbered | 4/5 | ✓ |
| 6 | Both numbered | 4/6 | ✓ |
| 1 | Only one heading | - | ✗ (need at least 2) |

### Pattern Consistency

The first two headings determine the pattern (style and structure) for the level:

- Both `1.`, `2.` → single-component `arabic`
- Both `1.1`, `1.2` → two-component `arabic.arabic`
- Both `I.`, `II.` → single-component `roman_upper`
- `1.` and `1.1` → structures don't match → level is `none`
- `1.` and `II.` → styles don't match → level is `none`

Example:
- H1s: `# 1. Intro`, `# 2. Design`, `# Conclusion` → First two match single `arabic`,
  2/3 = 66% ✓ → H1 qualifies
- H1s: `# 1. Intro`, `# Design`, `# 3. Conclusion` → First two don't both have prefix
  → H1 is `none`

### Hierarchical Constraint (Final Check)

**Conventions must be contiguous starting from H1.** Valid configurations:

- ✓ H1 only
- ✓ H1 + H2
- ✓ H1 + H2 + H3
- ✓ H1 + H2 + H3 + H4
- etc.

**Invalid configurations** (gaps or missing H1):

- ✗ H2 only (missing H1)
- ✗ H1 + H3 (missing H2)
- ✗ H2 + H3 (missing H1)

If a gap is detected, all levels from the gap onward are set to `none`.

Example:
- Raw inference: H1=`{h1:arabic}.`, H2=`none`, H3=`{h1:arabic}.{h2:arabic}.{h3:arabic}`
- After hierarchical check: H1=`{h1:arabic}.`, H2=`none`, H3=`none`
  (H3 disabled because H2 is `none`)

### Recognized Patterns (General Approach)

We use a **single general regex** that recognizes all standard numbering styles in any
decimal combination, with optional trailing `.` or `)`.

**Recognized number styles:**

| Style | Pattern | Examples |
|-------|---------|----------|
| `arabic` | Decimal digits | `1`, `2`, `10`, `100` |
| `roman_upper` | Uppercase Roman | `I`, `II`, `III`, `IV`, `V`, `IX`, `X`, `XI` |
| `roman_lower` | Lowercase Roman | `i`, `ii`, `iii`, `iv`, `v`, `ix`, `x`, `xi` |
| `alpha_upper` | Uppercase letters | `A`, `B`, `C`, ... `Z`, `AA`, `AB` |
| `alpha_lower` | Lowercase letters | `a`, `b`, `c`, ... `z`, `aa`, `ab` |

**Recognized decimal patterns:**

Any combination of the above styles separated by `.`:
- `1.2.3` (all arabic)
- `I.A.1` (roman, alpha, arabic)
- `1.a.i` (arabic, alpha_lower, roman_lower)
- `A.1` (alpha, arabic)

**Trailing characters:**
- `.` (period) - normalized output
- `)` (parenthesis) - recognized, normalized to `.`
- ` ` (space only) - recognized, normalized to `.`

**General regex pattern:**

```python
# Component patterns
ARABIC = r'\d+'
ROMAN_UPPER = r'[IVXLCDM]+'
ROMAN_LOWER = r'[ivxlcdm]+'
ALPHA_UPPER = r'[A-Z]+'
ALPHA_LOWER = r'[a-z]+'

# Single component (any style)
COMPONENT = rf'({ARABIC}|{ROMAN_UPPER}|{ROMAN_LOWER}|{ALPHA_UPPER}|{ALPHA_LOWER})'

# Full number pattern: one or more components separated by dots
# with optional trailing . or )
NUMBER_PATTERN = rf'^({COMPONENT}(?:\.{COMPONENT})*)[.\)]?\s+(.+)$'
```

### Style Inference

After parsing, we **infer the style** of each component. The order of checks matters
for ambiguous cases (e.g., "I" could be Roman 1 or Alpha):

```python
def infer_style(component: str) -> NumberStyle:
    """Infer the number style from a parsed component."""
    if component.isdigit():
        return NumberStyle.arabic
    # Check Roman before Alpha (handles ambiguous cases like "I", "C", "D")
    if all(c in 'IVXLCDM' for c in component):
        return NumberStyle.roman_upper
    if all(c in 'ivxlcdm' for c in component):
        return NumberStyle.roman_lower
    if component.isupper():
        return NumberStyle.alpha_upper
    if component.islower():
        return NumberStyle.alpha_lower
    return NumberStyle.arabic  # fallback
```

**Note on ambiguity**: Single letters like "I", "V", "X", "C", "D", "M" are interpreted
as Roman numerals, not alphabetic. To use alphabetic "I", a document would need letters
outside the Roman set (e.g., "A", "B", "E", "F") to establish the pattern.

**Level-wide disambiguation**: If headings at a single level contain *both* Roman-only
letters (I, V, X, C, D, M) and non-Roman letters (A, B, E, F, G, etc.), we treat the
entire level as alphabetic. For example, if H1s are "A.", "B.", "C.", "D.", the "C" and
"D" are not misinterpreted as Roman—the presence of "A", "B" establishes alphabetic intent.

### Examples of Prefix Extraction

| Input | Parsed Components | Inferred Styles | Title |
|-------|-------------------|-----------------|-------|
| `1. Introduction` | `["1"]` | `[arabic]` | `Introduction` |
| `1.2 Background` | `["1", "2"]` | `[arabic, arabic]` | `Background` |
| `I. Introduction` | `["I"]` | `[roman_upper]` | `Introduction` |
| `I.A Overview` | `["I", "A"]` | `[roman_upper, alpha_upper]` | `Overview` |
| `1.a Details` | `["1", "a"]` | `[arabic, alpha_lower]` | `Details` |
| `A.1.i Deep` | `["A", "1", "i"]` | `[alpha_upper, arabic, roman_lower]` | `Deep` |
| `Background` | None | - | - (no prefix) |

### Validation Rules

After parsing and style inference, we validate:

1. **Consistent style per level**: All H1 prefixes must use the same style for position 1,
   all H2 prefixes must use the same styles for positions 1-2, etc.
2. **Valid Roman numerals**: `IIII` is not valid (should be `IV`). We validate known Roman
   numeral sequences.
3. **Hierarchical structure**: H2 prefixes should have 2 components, H3 should have 3, etc.
   (though H1 can have 1 component with trailing `.`)

## Inferred Numbering Conventions

To preserve the document's existing style, we analyze heading levels and infer a
**format string** that describes the numbering convention.

### Format String Representation

Instead of enum values, we use a format string that explicitly describes the structure:

```
"{h1:arabic}."                              # H1 only: 1., 2., 3.
"{h1:arabic}.{h2:arabic}"                   # H1+H2: 1.1, 1.2, 2.1
"{h1:arabic}.{h2:arabic}.{h3:arabic}"       # H1+H2+H3: 1.1.1, 1.1.2
"{h1:roman_upper}."                         # Roman H1: I., II., III.
"{h1:roman_upper}.{h2:alpha_upper}"         # Roman H1 + Alpha H2: I.A, I.B
"{h1:arabic}.{h2:alpha_lower}.{h3:roman_lower}"  # Mixed: 1.a.i, 1.a.ii
```

This format string is self-documenting and supports all number styles (arabic, roman, alpha).

### `NumberStyle` Enum

The style of numbers (all supported):

```python
class NumberStyle(str, Enum):
    """Number style within a format component."""
    arabic = "arabic"            # 1, 2, 3, 10, 100
    roman_upper = "roman_upper"  # I, II, III, IV, V
    roman_lower = "roman_lower"  # i, ii, iii, iv, v
    alpha_upper = "alpha_upper"  # A, B, C, ... Z, AA, AB
    alpha_lower = "alpha_lower"  # a, b, c, ... z, aa, ab
```

**Conversion functions:**

```python
def to_number(style: NumberStyle, value: int) -> str:
    """Convert an integer to its string representation in the given style."""
    if style == NumberStyle.arabic:
        return str(value)
    elif style == NumberStyle.roman_upper:
        return int_to_roman(value).upper()
    elif style == NumberStyle.roman_lower:
        return int_to_roman(value).lower()
    elif style == NumberStyle.alpha_upper:
        return int_to_alpha(value).upper()
    elif style == NumberStyle.alpha_lower:
        return int_to_alpha(value).lower()

def from_number(style: NumberStyle, text: str) -> int:
    """Convert a string representation back to an integer."""
    if style == NumberStyle.arabic:
        return int(text)
    elif style in (NumberStyle.roman_upper, NumberStyle.roman_lower):
        return roman_to_int(text)
    elif style in (NumberStyle.alpha_upper, NumberStyle.alpha_lower):
        return alpha_to_int(text)
```

### `FormatComponent` Data Structure

A single component of the format string:

```python
@dataclass
class FormatComponent:
    """
    One component of a section number format.

    Examples:
    - FormatComponent(level=1, style=NumberStyle.arabic) → "{h1:arabic}"
    - FormatComponent(level=2, style=NumberStyle.roman_upper) → "{h2:roman_upper}"
    - FormatComponent(level=3, style=NumberStyle.alpha_lower) → "{h3:alpha_lower}"
    """
    level: int              # 1-6 for H1-H6
    style: NumberStyle      # arabic, roman_upper/lower, alpha_upper/lower
```

### `SectionNumFormat` Data Structure

The complete format for a heading level:

```python
@dataclass
class SectionNumFormat:
    """
    The inferred format for section numbers at a given heading level.

    Examples:
    - H1: components=[h1:arabic], trailing="." → "1.", "2.", "3."
    - H2: components=[h1:arabic, h2:arabic], trailing="" → "1.1", "1.2", "2.1"
    - H3: components=[h1:arabic, h2:arabic, h3:arabic], trailing="" → "1.1.1"
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

        Example: counters=[2, 3, 0, 0, 0, 0] with H2 format → "2.3" (arabic)
        Example: counters=[2, 3, 0, 0, 0, 0] with H2 format → "II.C" (roman_upper + alpha_upper)
        """
        parts = [to_number(c.style, counters[c.level - 1]) for c in self.components]
        return ".".join(parts) + self.trailing
```

### `SectionNumConvention` Data Structure

The complete inferred convention for a document:

```python
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
                parts.append(f"H{i+1}: {fmt.format_string()}")
        return ", ".join(parts) if parts else "none"
```

### Common Patterns

| Pattern | H1 Format | H2 Format | H3 Format | Example Output |
|---------|-----------|-----------|-----------|----------------|
| Arabic H1 only | `{h1:arabic}.` | None | None | `1.`, `2.`, `3.` |
| Arabic H1+H2 | `{h1:arabic}.` | `{h1:arabic}.{h2:arabic}` | None | `1.`, `1.1`, `1.2` |
| Arabic H1+H2+H3 | `{h1:arabic}.` | `{h1:arabic}.{h2:arabic}` | `{h1:arabic}.{h2:arabic}.{h3:arabic}` | `1.`, `1.1`, `1.1.1` |
| Roman H1 only | `{h1:roman_upper}.` | None | None | `I.`, `II.`, `III.` |
| Roman H1 + Alpha H2 | `{h1:roman_upper}.` | `{h1:roman_upper}.{h2:alpha_upper}` | None | `I.`, `I.A`, `I.B` |
| Alpha H1 only | `{h1:alpha_upper}.` | None | None | `A.`, `B.`, `C.` |
| Mixed: Arabic/alpha/roman | `{h1:arabic}.` | `{h1:arabic}.{h2:alpha_lower}` | `{h1:arabic}.{h2:alpha_lower}.{h3:roman_lower}` | `1.`, `1.a`, `1.a.i` |

### Inference Example

Given a document:
```markdown
# 1. Introduction
## 1.1 Background
## 1.2 Motivation
# 2. Design
## 2.1 Architecture
```

Inferred convention:
```python
SectionNumConvention(
    levels=(
        SectionNumFormat(  # H1
            components=[FormatComponent(1, NumberStyle.arabic)],
            trailing="."
        ),
        SectionNumFormat(  # H2
            components=[
                FormatComponent(1, NumberStyle.arabic),
                FormatComponent(2, NumberStyle.arabic),
            ],
            trailing=""
        ),
        None,  # H3
        None,  # H4
        None,  # H5
        None,  # H6
    )
)
# String representation: "H1: {h1:arabic}., H2: {h1:arabic}.{h2:arabic}"
```

### Normalization Rules

**When we recognize a pattern, we normalize to a consistent convention.**

The only normalization we currently perform is the trailing character:

1. **Trailing character**: Always normalize to `.` (period)
   - `1)` → `1.`
   - `1` (no trailing) → `1.`
   - `1.` → `1.` (unchanged)
   - `1.2)` → `1.2`
   - `1.2` (no trailing) → `1.2` (unchanged for decimals)
   - Rationale: Period is the most traditional and readable separator

2. **Spacing**: Always one space after the number/trailing character
   - Input: `1.Intro` → Output: `1. Intro`

3. **Decimal format**: No trailing dot on decimals (the dots are internal separators)
   - `1.2` not `1.2.` for H2 under H1
   - `1.2.3` not `1.2.3.` for H3 under H2

**Normalization examples:**

| Input | Output | Notes |
|-------|--------|-------|
| `# 1. Intro` | `# 1. Intro` | Already normalized |
| `# 1) Intro` | `# 1. Intro` | `)` → `.` |
| `# 1 Intro` | `# 1. Intro` | Add trailing `.` |
| `## 1.2 Details` | `## 1.2 Details` | Already normalized |
| `## 1.2. Details` | `## 1.2 Details` | Remove trailing `.` |
| `## 1.2) Details` | `## 1.2 Details` | Remove `)` |
| `# I. Intro` | `# I. Intro` | Roman, already normalized |
| `# I) Intro` | `# I. Intro` | Roman, `)` → `.` |
| `## I.A Details` | `## I.A Details` | Roman+Alpha, no trailing |
| `# A. Intro` | `# A. Intro` | Alpha, already normalized |
| `# a) intro` | `# a. intro` | Alpha lowercase, `)` → `.` |

**Style preservation**: Normalization only affects trailing characters, not number
styles. If a document uses Roman numerals (`I.`, `II.`) or alphabetic (`A.`, `B.`),
the style is preserved during renumbering—only the sequence is corrected.

## Architecture

### Self-Contained Module

All section numbering logic lives in a single, testable module:

```
src/flowmark/transforms/section_numbering.py
```

This module is self-contained with:
- Data structures (enums, dataclasses)
- Parsing functions (regex-based extraction)
- Inference functions (convention detection)
- Renumbering functions (number generation)

### Module Structure

```python
# src/flowmark/transforms/section_numbering.py

# === Data Structures ===
class NumberStyle(str, Enum): ...           # arabic, roman_upper/lower, alpha_upper/lower
@dataclass class FormatComponent: ...       # {h1:arabic} component
@dataclass class SectionNumFormat: ...      # Full format for one level
@dataclass class SectionNumConvention: ...  # Convention for all 6 levels
@dataclass class ParsedHeading: ...         # Parsed heading with extracted prefix

# === Parsing Functions ===
def extract_section_prefix(text: str) -> ParsedPrefix | None: ...
    # Returns: ParsedPrefix(components, styles, trailing, title) or None
    # Example: "1.2. Intro" → (["1", "2"], [arabic, arabic], ".", "Intro")
def parse_heading(level: int, text: str) -> ParsedHeading: ...

# === Inference Functions ===
def infer_format_for_level(headings: list[ParsedHeading], level: int) -> SectionNumFormat | None: ...
def infer_section_convention(headings: list[ParsedHeading]) -> SectionNumConvention: ...
def apply_hierarchical_constraint(convention: SectionNumConvention) -> SectionNumConvention: ...
def normalize_convention(convention: SectionNumConvention) -> SectionNumConvention: ...

# === Renumbering Functions ===
class SectionRenumberer:
    def __init__(self, convention: SectionNumConvention): ...
    def next_number(self, level: int) -> str: ...      # Increment and format
    def format_heading(self, level: int, title: str) -> str: ...

# === Top-Level API ===
def renumber_headings(headings: list[tuple[int, str]]) -> list[tuple[int, str]]: ...
```

### Processing Flow

```
CLI: --renumber-sections
         │
         ▼
    reformat_file()
         │
         ▼
    [1. Parse all headings from document]
         │
         ▼
    [2. infer_section_convention()]
         │
         ├── For each level H1-H6:
         │   ├── Extract prefixes from all headings at level
         │   ├── Check first 2+ for pattern consistency
         │   ├── Check 2/3 threshold
         │   └── Set level config (style + trailing_char)
         │
         ├── apply_hierarchical_constraint()
         │   └── Disable levels after first gap
         │
         └── normalize_convention()
             └── Set trailing_char = "." for all active levels
         │
         ▼
    [3. SectionRenumberer with inferred convention]
         │
         ▼
    [4. render_heading() applies renumbering]
         │
         └── For each heading:
             ├── If level is active: generate new number, format heading
             └── If level is none: pass through unchanged
```

### Key Functions (Unit Testable)

| Function | Input | Output | Tests |
|----------|-------|--------|-------|
| `extract_section_prefix()` | `"1. Intro"` | `(["1"], [arabic], ".", "Intro")` | Arabic single |
| `extract_section_prefix()` | `"1.2 Details"` | `(["1", "2"], [arabic, arabic], "", "Details")` | Arabic decimal |
| `extract_section_prefix()` | `"I.A Details"` | `(["I", "A"], [roman_upper, alpha_upper], "", "Details")` | Mixed styles |
| `extract_section_prefix()` | `"Background"` | `None` | No prefix |
| `SectionNumFormat.format_string()` | H2 format | `"{h1:arabic}.{h2:arabic}"` | String repr |
| `SectionNumFormat.format_number()` | `[2, 3, 0, 0, 0, 0]` | `"2.3"` | Number formatting |
| `infer_format_for_level()` | List of H1s | `SectionNumFormat` or `None` | First-two + 2/3 |
| `apply_hierarchical_constraint()` | Convention with gaps | Convention with gaps filled | Contiguity |
| `normalize_convention()` | Convention | Convention with `.` trailing | Normalization |
| `SectionRenumberer.next_number()` | level=1 | `"1."`, `"2."`, ... | Counter state |
| `SectionRenumberer.format_heading()` | level=2, title="Foo" | `"1.1 Foo"` | Full heading |

### Section Renumbering State

During rendering, track:
- Current counters for each heading level (H1, H2, H3, etc.)
- When entering a heading, increment the counter for that level
- Reset all deeper level counters when a shallower heading is encountered

```python
# Example state during rendering:
# Heading: "# 1. Intro"     → counters: [1, 0, 0, 0, 0, 0]
# Heading: "## 1.1 Foo"     → counters: [1, 1, 0, 0, 0, 0]
# Heading: "## 1.2 Bar"     → counters: [1, 2, 0, 0, 0, 0]
# Heading: "# 2. Next"      → counters: [2, 0, 0, 0, 0, 0]  (H2+ reset)
# Heading: "## 2.1 More"    → counters: [2, 1, 0, 0, 0, 0]
```

## Implementation Plan

All code goes in `src/flowmark/transforms/section_numbering.py` with tests in
`tests/test_section_numbering.py`.

### Phase 1: Core Data Structures

- [ ] Add `NumberStyle` enum (`arabic`, `roman_upper`, `roman_lower`, `alpha_upper`, `alpha_lower`)
- [ ] Add `FormatComponent` dataclass (level + style)
- [ ] Add `SectionNumFormat` dataclass (components + trailing)
  - `format_string()` method → `"{h1:arabic}.{h2:arabic}"`
  - `format_number(counters)` method → `"1.2"`
- [ ] Add `SectionNumConvention` dataclass (tuple of 6 formats, each `SectionNumFormat | None`)
  - `max_depth` property
  - `is_active` property
  - `__str__` method for debugging
- [ ] Add `ParsedHeading` dataclass (level, original_text, number_parts, trailing, title)
- [ ] Unit tests: dataclass creation, format_string(), format_number(), max_depth, is_active

### Phase 2: Prefix Extraction (Parsing)

- [ ] Implement `extract_section_prefix(text: str)` function
  - Returns: `ParsedPrefix(components, styles, trailing, title)` or `None`
  - `components`: The raw string components, e.g., `["1"]` or `["1", "2"]` or `["I", "A"]`
  - `styles`: The inferred style for each component, e.g., `[arabic]` or `[roman_upper, alpha_upper]`
  - `trailing`: The character after the number (`.`, `)`, or `""`)
  - `title`: The heading text after the prefix
- [ ] Implement helper functions:
  - `infer_style(component: str) -> NumberStyle`
  - `int_to_roman(n: int) -> str` and `roman_to_int(s: str) -> int`
  - `int_to_alpha(n: int) -> str` and `alpha_to_int(s: str) -> int`
- [ ] Unit tests for `extract_section_prefix()`:
  - Arabic:
    - `"1. Intro"` → `(["1"], [arabic], ".", "Intro")`
    - `"1) Intro"` → `(["1"], [arabic], ")", "Intro")`
    - `"1 Intro"` → `(["1"], [arabic], "", "Intro")`
    - `"1.2 Details"` → `(["1", "2"], [arabic, arabic], "", "Details")`
    - `"1.2.3 Deep"` → `(["1", "2", "3"], [arabic, arabic, arabic], "", "Deep")`
  - Roman:
    - `"I. Intro"` → `(["I"], [roman_upper], ".", "Intro")`
    - `"II.A Overview"` → `(["II", "A"], [roman_upper, alpha_upper], "", "Overview")`
    - `"i. intro"` → `(["i"], [roman_lower], ".", "intro")`
  - Alphabetic:
    - `"A. Intro"` → `(["A"], [alpha_upper], ".", "Intro")`
    - `"A.1 Details"` → `(["A", "1"], [alpha_upper, arabic], "", "Details")`
    - `"a) intro"` → `(["a"], [alpha_lower], ")", "intro")`
  - Mixed:
    - `"1.a.i Deep"` → `(["1", "a", "i"], [arabic, alpha_lower, roman_lower], "", "Deep")`
  - No prefix:
    - `"Background"` → `None`
    - `"The 1st Item"` → `None` (number not at start)
- [ ] Unit tests for style inference:
  - `"1"` → `arabic`, `"123"` → `arabic`
  - `"I"` → `roman_upper`, `"IV"` → `roman_upper`, `"XII"` → `roman_upper`
  - `"i"` → `roman_lower`, `"iv"` → `roman_lower`
  - `"A"` → `alpha_upper`, `"AA"` → `alpha_upper`, `"AZ"` → `alpha_upper`
  - `"a"` → `alpha_lower`, `"aa"` → `alpha_lower`
- [ ] Unit tests for number conversion:
  - `int_to_roman(4)` → `"IV"`, `roman_to_int("IV")` → `4`
  - `int_to_alpha(1)` → `"A"`, `int_to_alpha(27)` → `"AA"`, `alpha_to_int("AA")` → `27`

### Phase 3: Convention Inference

- [ ] Implement `infer_format_for_level(headings, level)` function
  - Filters headings to given level
  - Checks first-two rule: first two headings must have matching prefix structure
  - Checks two-thirds rule: ≥66% of all headings have prefix
  - Returns `SectionNumFormat` or `None`
  - The format is built from the number_parts structure:
    - H1 with `[n]` → `SectionNumFormat([h1:arabic], trailing)`
    - H2 with `[n, m]` → `SectionNumFormat([h1:arabic, h2:arabic], trailing)`
- [ ] Implement `infer_section_convention(headings)` function
  - Calls `infer_format_for_level()` for each level H1-H6
  - Returns raw `SectionNumConvention`
- [ ] Unit tests for first-two rule:
  - First two numbered → passes first-two
  - First numbered, second not → fails first-two
  - First not, second numbered → fails first-two
  - Only one heading total → fails (need at least 2)
- [ ] Unit tests for two-thirds rule:
  - 2/2 (100%) → qualifies
  - 2/3 (66%) → qualifies
  - 1/3 (33%) → does not qualify
  - 3/4 (75%) → qualifies
  - 2/4 (50%) → does not qualify
  - 4/6 (66%) → qualifies
  - 3/6 (50%) → does not qualify
- [ ] Unit tests for format inference:
  - H1s with `[1], [2], [3]` → format `{h1:arabic}.`
  - H2s with `[1,1], [1,2], [2,1]` → format `{h1:arabic}.{h2:arabic}`
  - H1s with `[I], [II], [III]` → format `{h1:roman_upper}.`
  - H1s with `[A], [B], [C]` → format `{h1:alpha_upper}.`
  - H1s with `[I], [II]`, H2s with `[I.A], [I.B]` → format `{h1:roman_upper}.{h2:alpha_upper}`
  - First two with different structures (e.g., `[1]` and `[1,2]`) → `None`
  - First two with different styles (e.g., `[1]` and `[I]`) → `None`
- [ ] Unit tests for level-wide disambiguation:
  - H1s with `[A], [B], [C], [D]` → all `alpha_upper` (C, D not misread as Roman)
  - H1s with `[I], [II], [III], [IV]` → all `roman_upper` (pure Roman set)
  - H1s with `[a], [b], [c], [d]` → all `alpha_lower` (c, d not misread as Roman)

### Phase 4: Hierarchical Constraint

- [ ] Implement `apply_hierarchical_constraint(convention)` function
  - Checks for gaps in H1 → H2 → H3 → ... chain
  - Sets all levels after first gap to `none`
- [ ] Unit tests:
  - H1+H2+H3 → unchanged
  - H1+H3 (gap at H2) → H1 only
  - H2 only (no H1) → all `none`
  - H1+H2+H4 (gap at H3) → H1+H2 only

### Phase 5: Normalization

- [ ] Implement `normalize_convention(convention)` function
  - Sets `trailing_char = "."` for all active levels
- [ ] Unit tests:
  - Convention with `)` → Convention with `.`
  - Convention with mixed separators → all `.`

### Phase 6: Renumbering Logic

- [ ] Implement `SectionRenumberer` class
  - `__init__(convention)`: Store convention, initialize counters to [0,0,0,0,0,0]
  - `next_number(level)`: Increment counter, reset deeper levels, return formatted
  - `format_heading(level, title)`: Combine number + trailing_char + space + title
- [ ] Unit tests for counter state (Arabic):
  - H1 → "1", H1 → "2", H1 → "3"
  - H1 → "1", H2 → "1.1", H2 → "1.2", H1 → "2", H2 → "2.1"
  - H1 → "1", H2 → "1.1", H3 → "1.1.1", H3 → "1.1.2", H2 → "1.2", H3 → "1.2.1"
- [ ] Unit tests for counter state (Roman):
  - H1 → "I", H1 → "II", H1 → "III", H1 → "IV"
  - H1 → "I", H2 → "I.A", H2 → "I.B", H1 → "II", H2 → "II.A"
- [ ] Unit tests for counter state (Mixed styles):
  - H1 roman_upper, H2 alpha_upper: H1 → "I", H2 → "I.A", H2 → "I.B", H1 → "II"
  - H1 arabic, H2 alpha_lower, H3 roman_lower: "1", "1.a", "1.a.i", "1.a.ii"
- [ ] Unit tests for formatting:
  - `format_heading(1, "Intro")` → `"1. Intro"` (arabic)
  - `format_heading(2, "Details")` → `"1.1 Details"` (after H1, arabic)
  - `format_heading(1, "Chapter")` → `"I. Chapter"` (roman_upper)
  - `format_heading(2, "Section")` → `"I.A Section"` (roman_upper + alpha_upper)

### Phase 7: Integration with Renderer

- [ ] Add `section_renumberer` parameter to `MarkdownNormalizer`
- [ ] Modify `render_heading()` to apply renumbering when enabled
- [ ] Thread `renumber_sections` through API: `fill_markdown()`, `reformat_text()`, etc.
- [ ] Integration tests with full markdown documents

### Phase 8: CLI Integration

- [ ] Add `--renumber-sections` flag to CLI
- [ ] Update help text
- [ ] Include in `--auto` flag

### Phase 9: End-to-End Testing

- [ ] Test documents with various numbering styles
- [ ] Test 2/3 threshold edge cases
- [ ] Test hierarchical constraint edge cases
- [ ] Test separator normalization
- [ ] Update documentation

## Acceptance Criteria

### Functional
1. `flowmark --renumber-sections file.md` correctly renumbers sections in a numbered
   document
2. `flowmark --auto file.md` includes section renumbering
3. Documents without consistent numbering are left unchanged
4. 2/3 threshold correctly qualifies/disqualifies levels
5. Hierarchical constraint enforced (no gaps, must start at H1)
6. Nested numbering is handled correctly (1.1, 1.2, 2.1, etc.)
7. Unnumbered headings at qualified levels pass through unchanged
8. Trailing separators normalized to period

### Quality
9. `make lint` passes (ruff, pyright, etc.)
10. `make test` passes with comprehensive coverage
11. All public functions have docstrings
12. Module has comprehensive docstring with usage example

### Documentation
13. README.md updated with section renumbering documentation
14. CLI help text includes `--renumber-sections` flag
15. `--auto` description updated to include section renumbering

## Test Cases

```python
# Basic renumbering - H1 only
def test_simple_renumber():
    input = """# 1. Intro
# 3. Middle
# 2. End"""
    expected = """# 1. Intro
# 2. Middle
# 3. End"""
    assert reformat(input, renumber_sections=True) == expected

# Nested renumbering - H1 + H2
def test_nested_renumber():
    input = """# 1. First
## 1.1 Sub A
## 1.3 Sub B
# 3. Second
## 3.1 Sub C"""
    expected = """# 1. First
## 1.1 Sub A
## 1.2 Sub B
# 2. Second
## 2.1 Sub C"""
    assert reformat(input, renumber_sections=True) == expected

# First-two + 2/3: First two numbered, 2/3 total → qualifies
def test_first_two_and_two_thirds_qualifies():
    input = """# 1. Intro
# 2. Design
# Background"""
    expected = """# 1. Intro
# 2. Design
# Background"""
    # First two H1s numbered ✓, 2/3 total ✓ → H1 qualifies
    # Already correctly numbered, so output same (but would renumber if wrong)
    assert reformat(input, renumber_sections=True) == expected

# First-two fails: First two not both numbered → does NOT qualify
def test_first_two_fails():
    input = """# 1. Intro
# Background
# 3. Conclusion"""
    # First two H1s: only first is numbered → first-two fails
    # Document left unchanged
    assert reformat(input, renumber_sections=True) == input

# 2/3 fails: First two numbered, but only 2/4 total → does NOT qualify
def test_two_thirds_fails():
    input = """# 1. Intro
# 2. Design
# Background
# Conclusion"""
    # First two H1s numbered ✓, but only 2/4 = 50% < 66% → 2/3 fails
    # Document left unchanged
    assert reformat(input, renumber_sections=True) == input

# Both pass: First two numbered, 3/4 total → qualifies and renumbers
def test_first_two_and_two_thirds_renumbers():
    input = """# 1. Intro
# 3. Design
# Background
# 5. Conclusion"""
    expected = """# 1. Intro
# 2. Design
# Background
# 3. Conclusion"""
    # First two H1s numbered ✓, 3/4 = 75% ✓ → H1 qualifies, renumbered
    # Unnumbered H1 ("Background") passes through unchanged
    assert reformat(input, renumber_sections=True) == expected

# H1 numbered, H2 not numbered (mixed levels)
def test_h1_numbered_h2_not():
    input = """# 1. Intro
## Background
## Details
# 3. Conclusion
## Summary"""
    expected = """# 1. Intro
## Background
## Details
# 2. Conclusion
## Summary"""
    # Only H1s are renumbered; H2s have no numbers so they stay as-is
    assert reformat(input, renumber_sections=True) == expected

# 2/3 threshold for H2: 4 of 6 H2s numbered → qualifies
def test_h2_two_thirds_threshold():
    input = """# 1. Intro
## 1.1 Sub A
## 1.2 Sub B
## Background
# 3. Design
## 3.1 Arch
## 3.2 Impl
## Overview"""
    expected = """# 1. Intro
## 1.1 Sub A
## 1.2 Sub B
## Background
# 2. Design
## 2.1 Arch
## 2.2 Impl
## Overview"""
    # H1s: 2/2 numbered → renumbered
    # H2s: 4/6 numbered (66%) → renumbered
    # Unnumbered H2s pass through unchanged
    assert reformat(input, renumber_sections=True) == expected

# H2 below threshold: 2 of 6 H2s numbered → does NOT qualify
def test_h2_below_threshold_not_renumbered():
    input = """# 1. Intro
## 1.1 Sub A
## Background
## Details
# 3. Design
## 3.1 Arch
## Overview
## Notes"""
    expected = """# 1. Intro
## 1.1 Sub A
## Background
## Details
# 2. Design
## 3.1 Arch
## Overview
## Notes"""
    # H1s: 2/2 numbered → renumbered
    # H2s: 2/6 numbered (33%) → does NOT qualify, originals preserved
    assert reformat(input, renumber_sections=True) == expected

# Separator normalization - always use period
def test_separator_normalized_to_period():
    input = """# 1) Intro
# 3) End"""
    expected = """# 1. Intro
# 2. End"""
    # Parenthesis separator normalized to period
    assert reformat(input, renumber_sections=True) == expected

# Three-level numbering
def test_three_level_numbering():
    input = """# 1. First
## 1.1 Sub A
### 1.1.1 Detail X
### 1.1.3 Detail Y
## 1.2 Sub B
# 2. Second"""
    expected = """# 1. First
## 1.1 Sub A
### 1.1.1 Detail X
### 1.1.2 Detail Y
## 1.2 Sub B
# 2. Second"""
    assert reformat(input, renumber_sections=True) == expected

# Decimal without trailing period normalized
def test_decimal_without_period():
    input = """# 1 Intro
## 1.1 Details
# 2 Conclusion"""
    expected = """# 1. Intro
## 1.1 Details
# 2. Conclusion"""
    # Missing periods are added
    assert reformat(input, renumber_sections=True) == expected

# Roman numeral renumbering
def test_roman_numeral_renumber():
    input = """# I. Introduction
# III. Middle
# II. End"""
    expected = """# I. Introduction
# II. Middle
# III. End"""
    # Roman numerals renumbered sequentially
    assert reformat(input, renumber_sections=True) == expected

# Roman H1 with alphabetic H2
def test_roman_h1_alpha_h2():
    input = """# I. Chapter One
## A. Overview
## C. Details
# III. Chapter Two
## A. Summary"""
    expected = """# I. Chapter One
## A. Overview
## B. Details
# II. Chapter Two
## A. Summary"""
    # Roman H1 + Alpha H2, both renumbered
    assert reformat(input, renumber_sections=True) == expected

# Mixed styles: Arabic H1, alpha_lower H2, roman_lower H3
def test_mixed_styles_three_levels():
    input = """# 1. First
## a. Sub A
### i. Detail X
### iii. Detail Y
## b. Sub B
# 3. Second"""
    expected = """# 1. First
## a. Sub A
### i. Detail X
### ii. Detail Y
## b. Sub B
# 2. Second"""
    assert reformat(input, renumber_sections=True) == expected

# Lowercase Roman numerals
def test_lowercase_roman():
    input = """# i. first
# iii. second
# ii. third"""
    expected = """# i. first
# ii. second
# iii. third"""
    assert reformat(input, renumber_sections=True) == expected

# Alphabetic only (uppercase)
def test_alpha_uppercase_only():
    input = """# A. Introduction
# C. Middle
# B. Conclusion"""
    expected = """# A. Introduction
# B. Middle
# C. Conclusion"""
    assert reformat(input, renumber_sections=True) == expected

# Alphabetic sequence beyond Z (AA, AB, etc.)
def test_alpha_beyond_z():
    # Testing that AA comes after Z
    input = """# Z. Last single letter
# AB. Wrong double"""
    expected = """# Z. Last single letter
# AA. Wrong double"""
    # AA should be renumbered (Z=26, next is AA=27)
    assert reformat(input, renumber_sections=True) == expected
```

## Resolved Questions

1. **Should `--renumber-sections` be included in `--auto`?**
   - **Decision**: Yes, include it in `--auto`.
   - **Rationale**: The feature is equally reliable as smart quotes because:
     - It requires 2+ headers with matching patterns to activate
     - The 2/3 threshold prevents false positives while allowing occasional mistakes
     - We infer conventions from the document and reinforce the same patterns
     - The only normalization is trailing punctuation → period (consistent style)
   - A document won't trigger renumbering unless it clearly follows a numbered pattern.

2. **How to handle trailing characters (`.`, `)`, etc.)?**
   - **Decision**: Always normalize to `.` (period). This is the most traditional format.
   - Input variations like `1)` or `1:` will be normalized to `1.`

3. **How to handle headings without numbers at a numbered level?**
   - **Decision**: Use 2/3 threshold. A level qualifies if:
     - At least 2 headings have a matching prefix, AND
     - At least 66% of headings at that level have a matching prefix
   - Unnumbered headings at a qualifying level pass through unchanged (no numbers added).
   - This allows for occasional missing numbers while still requiring clear intent.

4. **How to handle inconsistent numbering depth per section?**
   - **Decision**: Per-level analysis with hierarchical constraint.
   - Each level is evaluated independently using the 2/3 threshold.
   - Then hierarchical constraint is applied: conventions must be contiguous from H1.
   - If H1 is `none`, all levels are `none`. If H2 is `none`, H3+ are `none`.

5. **What if H2s are numbered but H1s are not?**
   - **Decision**: Not supported. Hierarchical constraint requires contiguous levels.
   - H2 numbering without H1 → all levels are `none` (no renumbering).

## Open Questions

None at this time.

## Documentation Plan

All documentation should follow the existing conventions for typography features
(smart quotes, ellipses). Section renumbering is part of `--auto`.

### README.md Updates

Add a new subsection under "Typographic Cleanups" or create a new section
"Structural Cleanups":

```markdown
### Section Renumbering

Flowmark can automatically renumber section headings when a document uses a consistent
numbered section convention (e.g., `# 1. Introduction`, `## 1.1 Background`).

This is useful for documents where section numbers have become inconsistent after
editing—inserting, moving, or removing sections no longer requires manual renumbering.

The feature:
- Detects if a document uses numbered sections (requires 2+ headings with matching
  patterns at each level, with at least 2/3 of headings following the convention)
- Infers the numbering style from existing content
- Renumbers to maintain sequential order while preserving unnumbered headings

Section renumbering only applies to documents that clearly follow a numbered pattern.
Unnumbered headings within a numbered document pass through unchanged.

This feature is enabled with the `--renumber-sections` flag or the `--auto`
convenience flag.
```

### CLI Help Text Updates

Update the `--auto` flag description:

```
--auto               Same as `--inplace --nobackup --semantic --cleanups --smartquotes
                     --ellipses --renumber-sections`, as a convenience for fully
                     auto-formatting files
```

Add new flag:

```
--renumber-sections  Automatically renumber section headings in documents that use
                     numbered sections (e.g., 1., 1.1, 1.2). Only applies when a
                     clear numbering pattern is detected. (only applies to Markdown
                     mode)
```

### API Docstrings

Update `reformat_text()` and related functions:

```python
def reformat_text(
    text: str,
    *,
    renumber_sections: bool = False,
    # ... other params
) -> str:
    """
    Reformat Markdown text with optional section renumbering.

    Args:
        renumber_sections: If True, automatically renumber section headings
            when a consistent numbering convention is detected. Requires
            2+ headings with matching numeric prefixes at each level.
    """
```

### Module Docstring

`src/flowmark/transforms/section_numbering.py`:

```python
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
- Trailing separators are normalized to periods (e.g., "1)" → "1.")
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
```

### Self-Documentation Checklist

- [ ] README.md: Add section under "Typographic Cleanups" or new "Structural Cleanups"
- [ ] README.md: Update `--auto` flag description in usage examples
- [ ] CLI help: Add `--renumber-sections` flag with clear description
- [ ] CLI help: Update `--auto` to include `--renumber-sections`
- [ ] Module docstring: Comprehensive explanation with usage example
- [ ] Function docstrings: All public functions documented
- [ ] Type hints: All parameters and return types annotated
- [ ] Inline comments: Complex regex patterns explained

## Future Extensions

- Option to add numbers to unnumbered documents
- Option to remove numbers from numbered documents
- Option to convert between number styles (e.g., Roman → Arabic)
- Support for nested list-style numbering (e.g., "1.1.1.1" beyond H3)

## References

- Existing list spacing implementation: `docs/project/specs/active/plan-2026-01-14-list-spacing-control.md`
- Marko heading parsing: `src/flowmark/formats/flowmark_markdown.py:384-403`
- CLI option pattern: `src/flowmark/cli.py:141-149`
