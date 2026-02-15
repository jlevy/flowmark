# Feature Validation: Fix Smart Quoting in Containers and Across Inline Elements

## Purpose

This is a validation spec for the smart quoting bugfix, listing automated testing
performed and remaining manual validation needed.

**Feature Plan:**
[plan-2026-02-14-fix-smart-quoting-containers.md](plan-2026-02-14-fix-smart-quoting-containers.md)

## Automated Validation (Testing Performed)

### Unit Testing

14 new integration-level tests were added to `tests/test_smartquotes.py` covering all
affected scenarios. All 202 project tests pass.

**Table cell tests (Issue 1 \u2014 missing container types):**

- `test_smart_quotes_in_table_cells` \u2014 Basic double quotes inside table cells
- `test_smart_quotes_apostrophes_in_table_cells` \u2014 Apostrophes/contractions in cells
- `test_smart_quotes_in_table_preserve_code_spans` \u2014 Code spans inside table cells are
  NOT modified while prose quotes in the same row ARE converted
- `test_smart_quotes_in_table_with_bold` \u2014 Quotes in cells containing bold text
- `test_smart_quotes_complex_table` \u2014 The exact table from the bug report (prose quotes
  converted, code span quotes preserved)

**Strikethrough tests (Issue 1):**

- `test_smart_quotes_in_strikethrough` \u2014 Quotes and apostrophes inside `~~text~~`

**Cross-inline element tests (Issue 2 \u2014 quotes spanning inline elements):**

- `test_smart_quotes_spanning_code_span` \u2014 `"text \`code\` text."` in a paragraph
- `test_smart_quotes_spanning_code_span_in_blockquote` \u2014 Same, inside a blockquote
- `test_smart_quotes_spanning_emphasis` \u2014 `"text *emphasis* text."`
- `test_smart_quotes_spanning_strong_emphasis` \u2014 `"text **bold** text."`
- `test_smart_quotes_spanning_link` \u2014 `"text [link](url) text."`
- `test_smart_quotes_not_modifying_code_content` \u2014 Code span containing quotes
  (`\`x="value"\``) is NEVER modified
- `test_smart_quotes_apostrophe_spanning_code_span` \u2014 Apostrophes around code spans
- `test_smart_quotes_blockquote_multiline_with_code_span` \u2014 The exact blockquote from
  the bug report (multi-line, with bold, code span, and apostrophes)

**Safety / no-false-positives tests (pre-existing, all still pass):**

- `test_technical_content_unchanged` \u2014 `function("param")`, `array['key']`, etc.
- `test_complex_cases_unchanged` \u2014 Nested quotes, doubled quotes, code-like patterns
- `test_patterns_left_unchanged` \u2014 `x="foo"`, escaped quotes, etc.
- All 17 template tag tests in `test_tag_formatting.py` still pass

### Integration and End-to-End Testing

**Reference document tests (`test_ref_docs.py`):**

- The reference test document (`testdoc.orig.md`) was updated with a new
  "Smart Quoting in Containers" section containing:
  - Table cells with quotes and code spans
  - Blockquote with quotes spanning code spans
  - Strikethrough with quotes
  - Quotes spanning emphasis and links
- All four expected output variants (plain, semantic, cleaned, auto) were regenerated
  and verified
- The auto variant correctly shows smart quotes in all new container contexts

**Changes to expected reference output (`testdoc.expected.auto.md`):**

The only changes to previously-expected output are 5 lines where quotes spanning across
`[link](url)` elements are now correctly converted. These were previously left as straight
quotes because the old per-node approach couldn't see across inline boundaries. The new
output is correct.

### Manual Testing Needed

1. **Spot-check the CLI** on the two examples from the bug report to confirm correct
   output visually:

   ```bash
   echo '> **Tell the user:** "First, I'\''ll make sure Markform is installed.
   > Markform is a CLI tool for creating structured forms that agents can fill via tool
   > calls. I'\''ll install it globally so we can use the `markform` command."' | flowmark --auto
   ```

   Expected: outer `"..."` converted to \u201c\u2026\u201d, apostrophes in `I'll` converted, code
   span `\`markform\`` preserved.

   ```bash
   echo '| User Says | You (the Agent) Run |
   | --- | --- |
   | **Issues/Beads** |  |
   | "There'\''s a bug where ..." | `tbd create "..." --type=bug` |
   | "Create a task/feature for ..." | `tbd create "..." --type=task` or `--type=feature` |' | flowmark --auto
   ```

   Expected: prose quotes in first column converted to smart quotes, code span quotes in
   second column preserved exactly.

2. **Run on a real-world document** containing tables with prose quotes and blockquotes
   with code spans to confirm no unexpected conversions occur.

3. **Review the reference test diff** in `testdoc.expected.auto.md` to confirm the 5
   changed lines (quotes spanning links) are correct improvements, not regressions.

## Open Questions

None.
