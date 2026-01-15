# Plan Spec: List Spacing Control (`--list-spacing` Option)

## Purpose

This is a technical design doc for adding a `--list-spacing` CLI option to Flowmark that
controls how tight vs loose list formatting is handled during Markdown normalization.

**Terminology Note**: CommonMark uses "tight" and "loose" as the official terms for list
spacing. A tight list has no blank lines between items; a loose list has blank lines.

## Background

Flowmark has historically converted **all lists to loose format** (blank lines between
items). This was an intentional design decision documented in
[markdown_filling.py:51-52](src/flowmark/linewrapping/markdown_filling.py#L51-L52):

> "Also enforces that all list items have two newlines between them, so that items are
> separate paragraphs when viewed as plaintext."

**CommonMark Spec Reference:**

Per [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/#lists):

| List Type | Definition | HTML Rendering |
|-----------|------------|----------------|
| **Tight** | No blank lines between items | Content NOT wrapped in `<p>` tags |
| **Loose** | Blank lines between items OR internal blank lines | Content wrapped in `<p>` tags |

A list becomes loose if:
1. Any blank line separates consecutive items
2. Any item contains multiple block elements with blank lines between them

**Current Behavior Issues:**

- Cannot round-trip documents (tight lists become loose)
- Author intent for compact lists is not preserved
- HTML rendering changes semantically (`<li>text</li>` vs `<li><p>text</p></li>`)
- Files become larger due to extra newlines

**Key Finding:**

Marko (the Markdown parser) exposes a `tight` boolean attribute on parsed `List` elements,
making it feasible to detect and preserve the original list style.

## Summary of Task

Add a `--list-spacing` CLI option with three modes:

| Mode | Behavior |
|------|----------|
| `preserve` | Keep lists tight or loose as authored (NEW DEFAULT) |
| `loose` | Convert all lists to loose format (current behavior) |
| `tight` | Convert all lists to tight format where possible |

This will be exposed as:
- CLI: `--list-spacing={preserve|tight|loose}` (default: `preserve`)
- API: `list_spacing: Literal["preserve", "tight", "loose"] = "preserve"` parameter

## Backward Compatibility

**BACKWARD COMPATIBILITY REQUIREMENTS:**

- **Code types, methods, and function signatures**: KEEP DEPRECATED - existing callers
  using default parameters should get the new `preserve` behavior, but we need to ensure
  no breaking changes for anyone explicitly passing parameters

- **Library APIs**: KEEP DEPRECATED for `reformat_text()` and `fill_markdown()` - add new
  `list_spacing` parameter with default that maintains current output for most use cases

- **CLI behavior**: BREAKING CHANGE (intentional) - the new default `preserve` will
  produce different output for tight lists. This is the desired behavior per user request.

- **File formats**: SUPPORT BOTH - existing Markdown files should produce similar output
  for already-loose lists; tight lists will now remain tight by default

**Key Compatibility Note:**

The `testdoc.expected.*.md` files will need to be regenerated since they contain tight
lists that are currently converted to loose. The new expected output will preserve tight
lists.

## Stage 1: Planning Stage

### Minimum Viable Feature

1. Add `--list-spacing` CLI option with `preserve`, `loose`, and `tight` modes
2. Default to `preserve` (breaking change from current `loose` behavior)
3. Detect list tightness via Marko's `list.tight` attribute
4. Thread spacing mode through to list rendering
5. Update test expectations

### Not In Scope

- Per-list overrides (e.g., `<!-- flowmark: loose -->` comments)
- Heuristic-based auto-detection of "should be tight" vs "should be loose"
- Different behavior for nested lists vs top-level lists

### Acceptance Criteria

1. `flowmark --list-spacing=preserve file.md` preserves tight lists as tight
2. `flowmark --list-spacing=preserve file.md` preserves loose lists as loose
3. `flowmark --list-spacing=loose file.md` converts all lists to loose (current behavior)
4. `flowmark --list-spacing=tight file.md` converts all lists to tight where possible
5. `flowmark file.md` uses `preserve` by default
6. Nested lists are controlled independently (each preserves its own tightness)
7. Lists with multi-paragraph items remain loose regardless of mode (CommonMark requirement)
8. `make lint` and `make test` pass

### Resolved Questions

- [x] **Q1**: Should `tight` mode force-convert loose lists, or only convert lists that
  CAN be tight (no multi-paragraph items)?
  **Decision**: Only convert lists that can be tight; leave multi-paragraph items loose.

- [x] **Q2**: How should nested lists behave? Same mode as parent, or independent?
  **Decision**: Each list independently uses the mode—nested tight stays tight, nested
  loose stays loose in `preserve` mode.

- [x] **Q3**: Should `--auto` flag continue to use `loose`, or switch to `preserve`?
  **Decision**: All modes use `preserve` as the default. Explicit `--list-spacing=X`
  overrides any other settings (including `--auto`).

## Stage 2: Architecture Stage

### Current Architecture

List rendering is handled in
[flowmark_markdown.py:226-261](src/flowmark/formats/flowmark_markdown.py#L226-L261):

```python
def render_list(self, element: block.List) -> str:
    # Currently ignores element.tight
    result: list[str] = []
    for i, child in enumerate(element.children):
        # ... configure prefix ...
        with self.container(prefix, subsequent_indent):
            rendered_item = self.render(child)
            result.append(rendered_item)
    return "".join(result)

def render_list_item(self, element: block.ListItem) -> str:
    result = ""
    # We want all list items to have two newlines between them.
    if self._suppress_item_break:
        self._suppress_item_break = False
    else:
        result += self._second_prefix.strip() + "\n"  # <-- Always adds blank line
    result += self.render_children(element)
    return result
```

**Key Issue**: `render_list_item()` always adds a blank line between items via
`_suppress_item_break` logic, regardless of the original list tightness.

### Proposed Changes

#### Change 1: Add `ListSpacing` Enum

**Location**: New in `flowmark_markdown.py` or separate types module

```python
from enum import StrEnum

class ListSpacing(StrEnum):
    preserve = "preserve"
    loose = "loose"
    tight = "tight"
```

#### Change 2: Thread Spacing Mode Through Renderer

**Location**: `MarkdownNormalizer.__init__()` and `flowmark_markdown()`

Add `_list_spacing: ListSpacing` instance variable that controls list rendering behavior.

#### Change 3: Modify `render_list()` to Detect Tightness

**Location**: `render_list()` method

```python
def render_list(self, element: block.List) -> str:
    # Determine effective tightness based on mode
    if self._list_spacing == ListSpacing.preserve:
        is_tight = element.tight
    elif self._list_spacing == ListSpacing.tight:
        is_tight = self._can_be_tight(element)  # Check for multi-para items
    else:  # loose
        is_tight = False

    # Pass is_tight to render_list_item via instance variable
    old_tight = self._current_list_tight
    self._current_list_tight = is_tight
    # ... existing rendering logic ...
    self._current_list_tight = old_tight
```

#### Change 4: Modify `render_list_item()` to Respect Tightness

**Location**: `render_list_item()` method

```python
def render_list_item(self, element: block.ListItem) -> str:
    result = ""
    # Only add blank line for loose lists
    if not self._current_list_tight:
        if self._suppress_item_break:
            self._suppress_item_break = False
        else:
            result += self._second_prefix.strip() + "\n"
    # ... rest of method
```

#### Change 5: Update CLI and API

**Locations**:
- `cli.py`: Add `--list-spacing` argument
- `reformat_api.py`: Add `list_spacing` parameter to `reformat_text()`, `reformat_file()`,
  `reformat_files()`
- `markdown_filling.py`: Add `list_spacing` parameter to `fill_markdown()`

### Architecture Diagram

```
CLI: --list-spacing=preserve
         │
         ▼
    reformat_file()
         │
         ▼
    fill_markdown(list_spacing="preserve")
         │
         ▼
    flowmark_markdown(line_wrapper, list_spacing="preserve")
         │
         ▼
    MarkdownNormalizer(line_wrapper, list_spacing="preserve")
         │
         ├─► render_list() ──► reads element.tight
         │        │
         │        ▼
         │   Determines effective tightness based on mode
         │        │
         │        ▼
         └─► render_list_item() ──► adds blank line only if not tight
```

## Stage 3: Implementation Phases

### Phase 1: Core Infrastructure

- [x] Add `ListSpacing` enum
- [x] Add `list_spacing` parameter to `MarkdownNormalizer.__init__()`
- [x] Add `_current_list_tight` instance variable for threading state
- [x] Add `_can_be_tight()` helper method for `tight` mode

### Phase 2: List Rendering Changes

- [x] Modify `render_list()` to compute effective tightness
- [x] Modify `render_list_item()` to conditionally add blank lines
- [x] Handle edge cases (nested lists, code blocks in items, etc.)

### Phase 3: API Updates

- [x] Add `list_spacing` parameter to `fill_markdown()`
- [x] Add `list_spacing` parameter to `reformat_text()`
- [x] Add `list_spacing` parameter to `reformat_file()` and `reformat_files()`

### Phase 4: CLI Updates

- [x] Add `--list-spacing` argument to CLI
- [x] Update `--auto` flag to use `preserve`
- [x] Update help text

### Phase 5: Testing and Documentation

- [x] Add unit tests for `ListSpacing` modes
- [x] Update `test_list_spacing.py` with preserve/tight mode tests
- [x] Regenerate `testdoc.expected.*.md` files
- [x] Update README/docstrings

## Stage 4: Validation Stage

### Test Strategy

1. **Unit Tests**: Test each spacing mode with tight and loose input lists
2. **Edge Cases**:
   - Nested lists (tight outer, loose inner and vice versa)
   - Lists with code blocks (must remain loose per CommonMark)
   - Lists with multiple paragraphs (must remain loose)
   - Mixed content lists
3. **Integration Tests**: Full document processing with various modes
4. **Regression Tests**: Ensure loose mode produces identical output to current behavior

### Test Cases

```python
# Tight list stays tight in preserve mode
def test_tight_list_preserved():
    input = "- one\n- two\n- three"
    output = fill_markdown(input, list_spacing="preserve")
    assert output == "- one\n- two\n- three\n"

# Tight list becomes loose in loose mode
def test_tight_list_to_loose():
    input = "- one\n- two\n- three"
    output = fill_markdown(input, list_spacing="loose")
    assert output == "- one\n\n- two\n\n- three\n"

# Loose list becomes tight in tight mode
def test_loose_list_to_tight():
    input = "- one\n\n- two\n\n- three"
    output = fill_markdown(input, list_spacing="tight")
    assert output == "- one\n- two\n- three\n"

# Multi-paragraph item stays loose even in tight mode
def test_multi_para_stays_loose():
    input = "- para1\n\n  para2\n- item2"
    output = fill_markdown(input, list_spacing="tight")
    # Item with multiple paragraphs forces loose
    assert "\n\n" in output
```

### Success Criteria

- [x] All existing tests pass (with updated expectations)
- [x] New spacing mode tests pass
- [x] `make lint` passes
- [x] `make test` passes
- [x] Manual testing with real documents confirms expected behavior
