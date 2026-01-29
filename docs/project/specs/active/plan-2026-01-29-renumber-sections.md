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

For each heading level (H1-H6), we analyze whether **all headings at that level** have
numeric prefixes. If they do, we determine the style (`arabic_integer` or `arabic_decimal`).

The analysis is per-level and independent:
- H1 might be numbered while H2 is not
- H2 might be numbered while H3 is not
- etc.

### Qualifying Documents

A document qualifies for section renumbering if at least one heading level has consistent
numbering (i.e., `max_depth >= 1`).

Examples:

| Document | H1 Style | H2 Style | H3 Style | max_depth | Qualifies? |
|----------|----------|----------|----------|-----------|------------|
| All H1s numbered, all H2s numbered | `arabic_integer` | `arabic_decimal` | `none` | 2 | Yes |
| All H1s numbered, H2s not numbered | `arabic_integer` | `none` | `none` | 1 | Yes |
| Some H1s numbered, some not | `none` | `none` | `none` | 0 | No |
| No headings numbered | `none` | `none` | `none` | 0 | No |

**Key rules**:
1. For a level to qualify as numbered, **all** headings at that level must have a numeric
   prefix. If even one heading at a level lacks a prefix, that level is `none`.
2. **Minimum threshold**: A level must have **2 or more headings** to qualify for
   renumbering. A single numbered heading is not enough to infer a convention.

This minimum threshold ensures very low false positive rates—a document won't accidentally
trigger renumbering unless it clearly follows a numbered section pattern.

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

1. **H1 headings**: If all H1s match integer pattern → `arabic_integer`
2. **H2+ headings**: If all headings at level N match decimal pattern with N components
   → `arabic_decimal`
3. **Mixed or partial**: If not all headings at a level match → `none` for that level

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

### Processing Flow

```
CLI: --renumber-sections
         │
         ▼
    reformat_file()
         │
         ▼
    [Pre-processing step: analyze headings]
         │
         ├── Extract all headings with levels
         ├── Detect numeric prefixes
         ├── Infer numbering convention
         │
         ▼
    fill_markdown(renumber_sections=True, convention=inferred)
         │
         ▼
    flowmark_markdown(..., section_renumberer=renumberer)
         │
         ▼
    MarkdownNormalizer with section renumbering
         │
         └── render_heading() → applies renumbering
```

### Key Components

1. **`SectionNumberExtractor`**: Parses heading text to extract numeric prefix and title
2. **`SectionConventionDetector`**: Analyzes all headings to infer the convention
3. **`SectionRenumberer`**: Generates new section numbers based on document structure
4. **Modified `render_heading()`**: Applies renumbering during Markdown normalization

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

### Phase 1: Core Data Structures

- [ ] Add `SectionNumStyle` enum (`none`, `arabic_integer`, `arabic_decimal`)
- [ ] Add `SectionLevelConfig` dataclass (style + trailing_char)
- [ ] Add `SectionNumConvention` dataclass (tuple of 6 level configs)
- [ ] Add unit tests for data structures

### Phase 2: Detection and Extraction

- [ ] Implement `extract_section_prefix()` function (regex-based)
  - Returns: `(style, number_parts, title)` or `None` if no prefix
- [ ] Implement `infer_section_convention()` function
  - Analyzes all headings in document
  - Returns `SectionNumConvention` with per-level styles
- [ ] Add unit tests for extraction and inference

### Phase 3: Renumbering Logic

- [ ] Implement `SectionRenumberer` class
  - Counter state: `list[int]` for H1-H6 counters
  - Method: `next_number(level: int) -> str` - increment and format
  - Method: `format_number(level: int, counters: list[int]) -> str`
- [ ] Add unit tests for renumbering logic

### Phase 4: Integration with Renderer

- [ ] Add `section_renumberer` parameter to `MarkdownNormalizer`
- [ ] Modify `render_heading()` to apply renumbering when enabled
- [ ] Thread `renumber_sections` through API: `fill_markdown()`, `reformat_text()`, etc.

### Phase 5: CLI Integration

- [ ] Add `--renumber-sections` flag to CLI
- [ ] Update help text
- [ ] Include in `--auto` flag (reliable due to 2+ header threshold)

### Phase 6: Testing and Edge Cases

- [ ] Add comprehensive tests for various numbering styles
- [ ] Test documents with partial numbering (H1 yes, H2 no)
- [ ] Test deeply nested heading levels (H1-H4)
- [ ] Test edge cases: empty headings, headings with only numbers
- [ ] Test separator normalization (`)` → `.`)
- [ ] Update documentation

## Acceptance Criteria

1. `flowmark --renumber-sections file.md` correctly renumbers sections in a numbered
   document
2. Documents without consistent numbering are left unchanged
3. The inferred convention (separator style, spacing) is preserved
4. Nested numbering is handled correctly (1.1, 1.2, 2.1, etc.)
5. Unnumbered headings below the max_depth are left unchanged
6. `make lint` and `make test` pass

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

# No change when not all H1s are numbered
def test_partial_h1_numbering_unchanged():
    input = """# 1. Intro
# Background
# 3. Conclusion"""
    # H1 level doesn't qualify - not all H1s are numbered
    # Document left unchanged
    assert reformat(input, renumber_sections=True) == input

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

# IMPORTANT: Partial H2 numbering - some H2s numbered, some not
# H2 level does NOT qualify, so numbered H2s keep original numbers
def test_partial_h2_numbering_not_renumbered():
    input = """# 1. Intro
## 1.1 First Sub
## Background
# 3. Design
## 3.1 Architecture
## Overview"""
    expected = """# 1. Intro
## 1.1 First Sub
## Background
# 2. Design
## 3.1 Architecture
## Overview"""
    # H1s: all numbered → renumbered (1, 2 instead of 1, 3)
    # H2s: some numbered, some not → H2 level is `none`, NO renumbering
    # The numbered H2s keep their ORIGINAL numbers (1.1, 3.1 unchanged)
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
     - It requires 2+ headers at a level to activate (prevents false positives)
     - We infer conventions from the document and reinforce the same patterns
     - The only normalization is trailing punctuation → period (consistent style)
   - A document won't trigger renumbering unless it clearly follows a numbered pattern.

2. **How to handle trailing characters (`.`, `)`, etc.)?**
   - **Decision**: Always normalize to `.` (period). This is the most traditional format.
   - Input variations like `1)` or `1:` will be normalized to `1.`

3. **How to handle headings without numbers at a numbered level?**
   - **Decision**: A level only qualifies as numbered if **all** headings at that level
     have numeric prefixes. If any heading lacks a prefix, the level is `none`.
   - This means we never add numbers to unnumbered headings.

4. **How to handle inconsistent numbering depth per section?**
   - **Decision**: Per-level analysis. Each level is evaluated independently.
   - If all H1s are numbered but only some H2s are numbered, then H1 is `arabic_integer`
     and H2 is `none`.

## Open Questions

1. **Edge case: What if H2s are numbered but H1s are not?**
   - This would be unusual but possible. Should we support it?
   - Tentative: Yes, support it. H1 would be `none`, H2 would be `arabic_decimal`.

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
