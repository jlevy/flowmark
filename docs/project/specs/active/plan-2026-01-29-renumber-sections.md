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
have numeric prefixes. If they do, we determine the style (`arabic_integer` or
`arabic_decimal`).

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

The first two headings determine the pattern (style) for the level:

- Both `1.`, `2.` → `arabic_integer`
- Both `1.1`, `1.2` → `arabic_decimal`
- `1.` and `1.1` → patterns don't match → level is `none`
- `1.` and `II.` → patterns don't match → level is `none`

Example:
- H1s: `# 1. Intro`, `# 2. Design`, `# Conclusion` → First two match `arabic_integer`,
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
- Raw inference: H1=`arabic_integer`, H2=`none`, H3=`arabic_decimal`
- After hierarchical check: H1=`arabic_integer`, H2=`none`, H3=`none`
  (H3 disabled because H2 is `none`)

### Numeric Prefix Patterns

**Integer pattern** (for H1, typically):
```
^(\d+)[.\):\s]\s*(.+)$
```
Matches: `1.`, `1)`, `1:`, `1 ` followed by title

**Decimal pattern** (for H2+, hierarchical):
```
^(\d+(?:\.\d+)+)[.\):\s]?\s*(.+)$
```
Matches: `1.2`, `1.2.3`, `7.18.3` optionally followed by separator and title

### Style Inference Rules

1. **H1 headings**: If pattern matches integer → `arabic_integer`
2. **H2+ headings**: If pattern matches decimal with N components → `arabic_decimal`
3. **No match or inconsistent**: `none` for that level

Examples of prefix extraction:
- `# 1. Introduction` → H1, style: `arabic_integer`, number: `1`, title: `Introduction`
- `## 1.2 Background` → H2, style: `arabic_decimal`, number: `1.2`, title: `Background`
- `### 7.18.3 Details` → H3, style: `arabic_decimal`, number: `7.18.3`, title: `Details`
- `## Background` → H2, style: `none` (no prefix)

## Inferred Numbering Conventions

To preserve the document's existing style, we analyze each heading level independently and
infer per-level conventions.

### `SectionNumStyle` Enum

Each heading level can have one of these numbering styles:

```python
class SectionNumStyle(str, Enum):
    """
    The numbering style for a single heading level.
    """
    none = "none"                    # No numbering at this level
    arabic_integer = "arabic_integer"  # Simple integer: 1, 2, 3
    arabic_decimal = "arabic_decimal"  # Hierarchical decimal: 1.1, 1.2.3

    # Future extensions:
    # roman_upper = "roman_upper"    # I, II, III
    # roman_lower = "roman_lower"    # i, ii, iii
    # alpha_upper = "alpha_upper"    # A, B, C
    # alpha_lower = "alpha_lower"    # a, b, c
```

**Style meanings:**
- `none`: This heading level has no numeric prefix (e.g., `## Background`)
- `arabic_integer`: Simple integer prefix (e.g., `# 1. Introduction`, `# 2. Design`)
- `arabic_decimal`: Hierarchical decimal prefix (e.g., `## 1.1 Overview`, `### 2.3.1 Details`)

### `SectionLevelConfig` Data Structure

Configuration for a single heading level:

```python
@dataclass
class SectionLevelConfig:
    """
    Numbering configuration for a single heading level (H1-H6).
    """
    style: SectionNumStyle

    # The trailing character after the number (typically ".")
    # Only meaningful when style != none
    trailing_char: str = "."
```

### `SectionNumConvention` Data Structure

The complete inferred convention for a document:

```python
@dataclass
class SectionNumConvention:
    """
    Represents the inferred numbering conventions for a document's sections.

    Contains per-level configuration for H1 through H6.
    """
    # Configuration for each heading level (index 0 = H1, index 5 = H6)
    levels: tuple[
        SectionLevelConfig,  # H1
        SectionLevelConfig,  # H2
        SectionLevelConfig,  # H3
        SectionLevelConfig,  # H4
        SectionLevelConfig,  # H5
        SectionLevelConfig,  # H6
    ]

    @property
    def max_depth(self) -> int:
        """
        The deepest heading level with numbering (1-6), or 0 if no numbering.

        A document is "active" for renumbering if max_depth >= 1.
        """
        for i in range(5, -1, -1):  # Check H6 down to H1
            if self.levels[i].style != SectionNumStyle.none:
                return i + 1
        return 0

    @property
    def is_active(self) -> bool:
        """Whether this document qualifies for section renumbering."""
        return self.max_depth >= 1
```

### Common Patterns

| Pattern | H1 | H2 | H3 | H4-H6 | Example |
|---------|----|----|----|----|---------|
| H1 only | `arabic_integer` | `none` | `none` | `none` | `# 1. Intro`, `## Background` |
| H1+H2 | `arabic_integer` | `arabic_decimal` | `none` | `none` | `# 1. Intro`, `## 1.1 Details` |
| H1+H2+H3 | `arabic_integer` | `arabic_decimal` | `arabic_decimal` | `none` | `# 1.`, `## 1.1`, `### 1.1.1` |

### Normalization Rules

When renumbering, we normalize to consistent conventions:

1. **Trailing character**: Always normalize to `.` (period)
   - Input: `1) Intro` or `1 Intro` → Output: `1. Intro`
   - Rationale: Period is the most traditional and readable separator

2. **Spacing**: Always one space after the trailing character
   - Input: `1.Intro` → Output: `1. Intro`

3. **Decimal format**: Use minimal dots (no trailing dot in decimals)
   - `1.2` not `1.2.` for H2 under H1
   - `1.2.3` not `1.2.3.` for H3 under H2

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
class SectionNumStyle(str, Enum): ...
@dataclass class SectionLevelConfig: ...
@dataclass class SectionNumConvention: ...
@dataclass class ParsedHeading: ...

# === Parsing Functions ===
def extract_section_prefix(text: str) -> tuple[SectionNumStyle, str, str] | None: ...
def parse_heading(level: int, text: str) -> ParsedHeading: ...

# === Inference Functions ===
def infer_level_convention(headings: list[ParsedHeading], level: int) -> SectionLevelConfig: ...
def infer_section_convention(headings: list[ParsedHeading]) -> SectionNumConvention: ...
def apply_hierarchical_constraint(convention: SectionNumConvention) -> SectionNumConvention: ...
def normalize_convention(convention: SectionNumConvention) -> SectionNumConvention: ...

# === Renumbering Functions ===
class SectionRenumberer:
    def __init__(self, convention: SectionNumConvention): ...
    def next_number(self, level: int) -> str: ...
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
| `extract_section_prefix()` | `"1. Intro"` | `(arabic_integer, "1", "Intro")` | Pattern matching |
| `extract_section_prefix()` | `"1.2 Details"` | `(arabic_decimal, "1.2", "Details")` | Decimal patterns |
| `extract_section_prefix()` | `"Background"` | `None` | No prefix |
| `infer_level_convention()` | List of H1s | `SectionLevelConfig` | 2/3 threshold |
| `apply_hierarchical_constraint()` | Convention with gaps | Convention with gaps filled | Contiguity |
| `normalize_convention()` | Convention | Convention with `.` trailing | Normalization |
| `SectionRenumberer.next_number()` | level=1 | `"1"`, `"2"`, ... | Counter state |
| `SectionRenumberer.format_heading()` | level=2, title="Foo" | `"1.1 Foo"` | Formatting |

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

- [ ] Add `SectionNumStyle` enum (`none`, `arabic_integer`, `arabic_decimal`)
- [ ] Add `SectionLevelConfig` dataclass (style + trailing_char)
- [ ] Add `SectionNumConvention` dataclass (tuple of 6 level configs)
- [ ] Add `ParsedHeading` dataclass (level, original_text, style, number, title)
- [ ] Unit tests: dataclass creation, `max_depth` property, `is_active` property

### Phase 2: Prefix Extraction (Parsing)

- [ ] Implement `extract_section_prefix(text: str)` function
  - Returns: `(SectionNumStyle, number_str, title)` or `None`
  - Regex matches: integer (`1.`), decimal (`1.2`, `1.2.3`), various separators
- [ ] Unit tests for `extract_section_prefix()`:
  - `"1. Intro"` → `(arabic_integer, "1", "Intro")`
  - `"1) Intro"` → `(arabic_integer, "1", "Intro")`
  - `"1 Intro"` → `(arabic_integer, "1", "Intro")`
  - `"1.2 Details"` → `(arabic_decimal, "1.2", "Details")`
  - `"1.2.3 Deep"` → `(arabic_decimal, "1.2.3", "Deep")`
  - `"7.18 Big"` → `(arabic_decimal, "7.18", "Big")`
  - `"Background"` → `None`
  - `"The 1st Item"` → `None` (number not at start)

### Phase 3: Convention Inference

- [ ] Implement `infer_level_convention(headings, level)` function
  - Filters headings to given level
  - Checks first-two rule: first two headings must have matching prefix
  - Checks two-thirds rule: ≥66% of all headings have prefix
  - Returns `SectionLevelConfig`
- [ ] Implement `infer_section_convention(headings)` function
  - Calls `infer_level_convention()` for each level H1-H6
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
- [ ] Unit tests for pattern consistency:
  - First two both `arabic_integer` → pattern is `arabic_integer`
  - First two both `arabic_decimal` → pattern is `arabic_decimal`
  - First two different patterns → level is `none`

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
- [ ] Unit tests for counter state:
  - H1 → "1", H1 → "2", H1 → "3"
  - H1 → "1", H2 → "1.1", H2 → "1.2", H1 → "2", H2 → "2.1"
  - H1 → "1", H2 → "1.1", H3 → "1.1.1", H3 → "1.1.2", H2 → "1.2", H3 → "1.2.1"
- [ ] Unit tests for formatting:
  - `format_heading(1, "Intro")` → `"1. Intro"`
  - `format_heading(2, "Details")` → `"1.1 Details"` (after H1)

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

- Roman numeral support (`I.`, `II.`, `III.`)
- Alphabetic numbering (`A.`, `B.`, `C.`)
- Mixed styles (Roman for H1, Arabic for H2)
- Option to add numbers to unnumbered documents
- Option to remove numbers from numbered documents

## References

- Existing list spacing implementation: `docs/project/specs/active/plan-2026-01-14-list-spacing-control.md`
- Marko heading parsing: `src/flowmark/formats/flowmark_markdown.py:384-403`
- CLI option pattern: `src/flowmark/cli.py:141-149`
