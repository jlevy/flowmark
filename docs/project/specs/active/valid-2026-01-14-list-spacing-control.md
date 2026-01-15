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

### CLI Validation

Please validate the following CLI commands work correctly:

1. **Default (preserve) mode - tight input:**
   ```shell
   echo "- one
   - two
   - three" | flowmark -
   ```
   **Expected:** Output should remain tight (no blank lines between items)

2. **Default (preserve) mode - loose input:**
   ```shell
   echo "- one

   - two

   - three" | flowmark -
   ```
   **Expected:** Output should remain loose (blank lines between items)

3. **Loose mode:**
   ```shell
   echo "- one
   - two
   - three" | flowmark --list-spacing=loose -
   ```
   **Expected:** Output should be loose (blank lines added between items)

4. **Tight mode:**
   ```shell
   echo "- one

   - two

   - three" | flowmark --list-spacing=tight -
   ```
   **Expected:** Output should be tight (blank lines removed)

5. **Help text:**
   ```shell
   flowmark --help
   ```
   **Expected:** Should show `--list-spacing` option with description

### File Processing Validation

1. **In-place processing with preserve mode:**
   ```shell
   # Create a test file with tight list
   echo "- item1
   - item2" > /tmp/test.md
   flowmark --inplace /tmp/test.md
   cat /tmp/test.md
   ```
   **Expected:** File should remain with tight list

2. **In-place processing with loose mode:**
   ```shell
   echo "- item1
   - item2" > /tmp/test.md
   flowmark --inplace --list-spacing=loose /tmp/test.md
   cat /tmp/test.md
   ```
   **Expected:** File should have blank lines between items

### Breaking Change Awareness

- **IMPORTANT**: The default behavior has changed from always making lists loose to
  preserving the original tight/loose formatting
- Users who relied on the previous behavior (lists always becoming loose) should use
  `--list-spacing=loose` to restore it
- Verify that the `--auto` flag still works as expected with the new default
