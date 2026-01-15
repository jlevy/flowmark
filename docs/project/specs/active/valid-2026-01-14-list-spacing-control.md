# Feature Validation: List Spacing Control (`--list-spacing` Option)

## Purpose

This is a validation spec for the `--list-spacing` CLI option that controls how tight vs
loose list formatting is handled during Markdown normalization.

**Feature Plan:** [plan-2026-01-14-list-spacing-control.md](plan-2026-01-14-list-spacing-control.md)

## Stage 4: Validation Stage

## Automated Validation (Testing Performed)

### Unit Testing

The following unit tests have been added or updated in `tests/test_list_spacing.py`:

**Preserve Mode Tests (default):**
- `test_tight_list_preserved` - Tight lists stay tight
- `test_loose_list_preserved` - Loose lists stay loose
- `test_preserve_is_default` - Confirm preserve is the default
- `test_numbered_list_preserve` - Numbered lists preserve tightness

**Loose Mode Tests:**
- `test_tight_list_to_loose` - Tight lists become loose
- `test_loose_list_stays_loose` - Loose lists stay loose
- `test_numbered_list_to_loose` - Numbered lists become loose

**Tight Mode Tests:**
- `test_loose_list_to_tight` - Loose lists become tight
- `test_tight_list_stays_tight` - Tight lists stay tight
- `test_multi_para_stays_loose_in_tight_mode` - Multi-paragraph items force loose (CommonMark
  requirement)

**Nested List Tests:**
- `test_nested_lists_independent_preserve` - Each nested list independently preserves
  tightness
- `test_nested_lists_loose_outer_tight_inner` - Mixed outer/inner tightness preserved

**Complex Content Tests:**
- `test_list_items_with_code_blocks_preserve` - Code blocks preserve tightness
- `test_list_items_with_code_blocks_loose` - Code blocks with loose mode
- `test_list_items_with_quote_blocks` - Quote blocks preserve tightness

**Spacing Normalization Tests:**
- `test_input_spacing_normalization_loose` - Various input spacings normalize to loose
- `test_input_spacing_normalization_tight` - Various input spacings normalize to tight
- `test_complex_content_with_loose_mode` - Complex content spacing in loose mode
- `test_multi_paragraph_spacing_loose_mode` - Multi-paragraph items in loose mode

**Other Updated Tests:**
- `test_escape_handling.py` - Updated to use `list_spacing="loose"` for escape tests
- `test_filling.py` - Updated to use `list_spacing="loose"` for backward compatibility
- `test_heading_spacing.py` - Updated to use `list_spacing="loose"` where needed

### Integration and End-to-End Testing

- All 172 tests pass (`make test`)
- Linting passes (`make lint`)
- Reference documents (`tests/testdocs/testdoc.expected.*.md`) regenerated for new default
  behavior

## Manual Testing Needed

All core functionality is covered by automated tests. Manual review is only needed for:

### Code Review Items

1. **Help text clarity** - Review `flowmark --help` to confirm the `--list-spacing` option
   description is clear and understandable

2. **Breaking change communication** - Confirm the breaking change (default behavior changed
   from `loose` to `preserve`) is adequately documented in:
   - The commit message
   - The PR description
   - The plan spec

### No Additional Manual Testing Required

The following are all covered by automated tests:
- All three modes (`preserve`, `loose`, `tight`)
- Nested list handling
- Multi-paragraph items
- CLI argument parsing
- File processing (in-place and stdout)
