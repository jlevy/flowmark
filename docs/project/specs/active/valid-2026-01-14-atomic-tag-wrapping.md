# Feature Validation: Atomic Tag Wrapping

## Purpose

This is a validation spec for the `--tags` CLI option that controls how template tags
(Markdoc/Jinja/HTML comments) are handled during line wrapping.

**Feature Plan:** [plan-2026-01-14-atomic-tag-wrapping.md](plan-2026-01-14-atomic-tag-wrapping.md)

## Stage 4: Validation Stage

## Automated Validation (Testing Performed)

### Unit Testing

All 160 tests pass. Key test coverage:

**Tag Formatting Tests (26 tests in `test_tag_formatting.py`):**

- `test_smart_quotes_not_applied_in_tag_attributes` - Quotes inside tags preserved
- `test_tag_with_array_spanning_lines` - Multi-line array attributes handled
- `test_tag_with_object_spanning_lines` - Multi-line object attributes handled
- `test_multiline_tag_with_surrounding_text` - Tags with surrounding prose
- `test_pipeline_preserves_tag_quotes` - Full pipeline preserves tag content
- `test_tag_newlines_preserved_in_pipeline` - Newlines around tags preserved
- `test_word_splitter_handles_multiline_tags` - Word splitter handles complex tags
- `test_line_wrapper_preserves_multiline_tags` - Line wrapper preserves tag structure
- `test_tag_with_embedded_percent_brace` - Edge case: `%}` inside tag content
- `test_jinja_variable_tags_in_prose` - `{{ variable }}` tags in text
- `test_jinja_comment_tags` - `{# comment #}` tags
- `test_html_comment_tags_with_quotes` - `<!-- comment -->` with quotes
- `test_adjacent_closing_tags` - `{% tag %}{% /tag %}` adjacency
- `test_selection_field_with_task_list` - Tags with Markdown lists inside
- `test_smart_quotes_preserves_*` - Multiple tests for quote preservation in tags
- `test_multiline_opening_tag_closing_on_own_line` - Closing tag placement
- `test_single_line_paired_tags_not_split` - Short paired tags stay together
- `test_multiline_tag_through_pipeline` - Long tags wrap correctly
- `test_html_comment_multiline_closing` - HTML comment multiline handling

### Integration and End-to-End Testing

**Reference Document Tests (`test_ref_docs.py`):**

- Tests full formatting pipeline against comprehensive test document
- Input: `tests/testdocs/testdoc.orig.md` (covers many tag scenarios)
- Expected output: `tests/testdocs/testdoc.expected.*.md` files
- Verifies 4 format modes: plain, semantic, cleaned, auto
- All expected files match actual output (no changes needed)

**CLI Parameter Threading:**

- `TagWrapping` enum added to `cli.py`, `reformat_api.py`, `markdown_filling.py`
- Parameter flows through: CLI -> reformat_files -> fill_markdown -> line_wrappers
- Default is `atomic` mode

### Linting

- `make lint` passes with 0 errors, 0 warnings
- Type checking (basedpyright) passes
- Code formatting (ruff) passes

## Manual Testing Needed

The following manual validation steps are recommended for engineering review:

### 1. CLI Option Verification

Verify the `--tags` option appears in help and works:

```bash
# Check help shows new option
flowmark --help | grep -A2 tags

# Test atomic mode (default) with a long tag
echo '{% field kind="string" id="name" label="Full Name" required=true %}{% /field %}' | flowmark -s

# Test wrap mode explicitly
echo '{% field kind="string" id="name" label="Full Name" required=true %}{% /field %}' | flowmark -s --tags=wrap
```

Expected: Both modes should produce similar output (long tags wrap at internal
whitespace, closing tags on own line).

### 2. Verify Testdoc Output

Spot-check the testdoc output for tag formatting:

```bash
# Run the actual formatter on the test document
flowmark -s tests/testdocs/testdoc.orig.md > /tmp/output.md

# Check a specific tag section (around line 1700)
sed -n '1700,1720p' /tmp/output.md
```

Expected: Long tags like `{% field kind="number" id="age" ... %}` should:
- Wrap at internal whitespace if too long
- Have closing tag `{% /field %}` on its own line

### 3. Backward Compatibility Check

If you have existing Markdown files with Markdoc tags, verify they format correctly:

```bash
# Format a real file and review the diff
flowmark -s your-file.md | diff - your-file.md
```

Expected: Tags should format consistently without breaking.

## Open Questions

None - the implementation matches the expected behavior documented in the plan spec.
