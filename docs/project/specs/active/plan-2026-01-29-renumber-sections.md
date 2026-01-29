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
- API: `renumber_sections: bool = False` parameter

## Detection Logic

### Qualifying Documents

A document qualifies for section renumbering if **all headings up to a given level** have
numeric prefixes. The "numbering depth" is the deepest level where this holds true.

Examples:

| Document | Numbering Depth | Qualifies? |
|----------|-----------------|------------|
| All H1s have numbers, all H2s have numbers | 2 | Yes |
| All H1s have numbers, some H2s don't | 1 | Yes (H1 only) |
| Some H1s have numbers, some don't | 0 | No |
| No headings have numbers | 0 | No |

### Numeric Prefix Pattern

A heading has a numeric prefix if it matches the pattern:

```
^(\d+(?:\.\d+)*)[.\):\s]\s*(.+)$
```

This captures:
- `1` - Simple integer
- `1.2` - Two-level numbering
- `1.2.3` - Three-level numbering (and so on)
- With trailing `.`, `)`, `:`, or space as separator before the title

Examples of valid prefixes:
- `# 1. Introduction` → prefix: `1`, title: `Introduction`
- `## 1.2 Background` → prefix: `1.2`, title: `Background`
- `### 7.18.3 Details` → prefix: `7.18.3`, title: `Details`
- `# 1) Overview` → prefix: `1`, title: `Overview`

## Inferred Numbering Conventions

To preserve the document's existing style, we need to infer the conventions used.

### `SectionNumberingConvention` Data Structure

```python
@dataclass
class SectionNumberingConvention:
    """
    Represents the inferred numbering conventions for a document's sections.
    """
    # The deepest heading level with consistent numbering (0 = no numbering, 1-6 = H1-H6)
    max_depth: int

    # The separator used after the number (e.g., ".", ")", ":", " ")
    separator: str

    # Whether there's a space between number and title (e.g., "1. Title" vs "1.Title")
    space_after_separator: bool

    # The number style (for future extensibility)
    number_style: NumberStyle  # "arabic" for now, future: "roman", "alpha"

    # Whether sub-sections restart at 1 or continue (e.g., 1.1, 1.2 vs 1.1, 2.1)
    # This is always hierarchical (1.1, 1.2, 2.1, 2.2) in standard docs
    hierarchical: bool = True
```

### `NumberStyle` Enum

```python
class NumberStyle(str, Enum):
    """
    The style of numbers used in section prefixes.
    """
    arabic = "arabic"      # 1, 2, 3 (current scope)
    # Future extensions:
    # roman_upper = "roman_upper"  # I, II, III
    # roman_lower = "roman_lower"  # i, ii, iii
    # alpha_upper = "alpha_upper"  # A, B, C
    # alpha_lower = "alpha_lower"  # a, b, c
```

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

### Phase 1: Core Infrastructure

- [ ] Add `NumberStyle` enum
- [ ] Add `SectionNumberingConvention` dataclass
- [ ] Implement `extract_section_number()` function (regex-based)
- [ ] Implement `detect_numbering_convention()` function
- [ ] Add unit tests for extraction and detection

### Phase 2: Renumbering Logic

- [ ] Implement `SectionRenumberer` class with counter state
- [ ] Add method to generate next section number for a given level
- [ ] Add method to format section number according to convention
- [ ] Add unit tests for renumbering logic

### Phase 3: Integration with Renderer

- [ ] Add `section_renumberer` parameter to `MarkdownNormalizer`
- [ ] Modify `render_heading()` to apply renumbering when enabled
- [ ] Thread `renumber_sections` through API: `fill_markdown()`, `reformat_text()`, etc.

### Phase 4: CLI Integration

- [ ] Add `--renumber-sections` flag to CLI
- [ ] Update help text
- [ ] Consider adding to `--auto` flag (or keep separate for safety)

### Phase 5: Testing and Edge Cases

- [ ] Add comprehensive tests for various numbering styles
- [ ] Test documents with partial numbering
- [ ] Test nested heading levels
- [ ] Test edge cases: empty headings, headings with only numbers, etc.
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
# Basic renumbering
def test_simple_renumber():
    input = """# 1. Intro
# 3. Middle
# 2. End"""
    expected = """# 1. Intro
# 2. Middle
# 3. End"""
    assert reformat(input, renumber_sections=True) == expected

# Nested renumbering
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

# No change when not all sections are numbered
def test_partial_numbering_unchanged():
    input = """# 1. Intro
# Background
# 3. Conclusion"""
    # Document doesn't qualify - not all H1s are numbered
    assert reformat(input, renumber_sections=True) == input

# Different separator preserved
def test_separator_preserved():
    input = """# 1) Intro
# 3) End"""
    expected = """# 1) Intro
# 2) End"""
    assert reformat(input, renumber_sections=True) == expected
```

## Open Questions

1. **Should `--renumber-sections` be included in `--auto`?**
   - Tentative: No, keep it separate since it modifies content, not just formatting.

2. **How to handle headings that gain/lose numbering?**
   - If a document qualifies at depth N, should unnumbered headings at levels ≤N get
     numbers added?
   - Tentative: No, only renumber existing numbered headings. Adding numbers is a
     separate feature.

3. **How to handle inconsistent numbering depth per section?**
   - Example: Section 1 has H1, H2, H3 numbered but Section 2 only has H1, H2 numbered.
   - Tentative: Use the minimum consistent depth across all top-level sections.

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
