# Bugfix Validation: Fix Tilde Doubling Near Parentheses

## Purpose

This is a validation spec for the tilde-in-parentheses bugfix, listing automated testing
performed and remaining manual validation needed.

## Bug Description

When a `~number` appears near parentheses (e.g., `~100 (~200)`), the tilde gets doubled
to `~~100 (~~200)` because the marko parser incorrectly matches `~100 (~` as a
strikethrough span. The `(` before the closing `~` is punctuation, and per the GFM spec
it should not qualify as a right-flanking delimiter when followed by a word character.

**Root Cause:** The `CustomStrikethrough` regex enforced GFM whitespace-based flanking
rules but missed the punctuation-based flanking rules. Specifically, a closing `~`
preceded by punctuation (like `(`) is only right-flanking if followed by whitespace,
punctuation, or end of string.

**Fix:** Override the `find()` method in `CustomStrikethrough` to add full GFM punctuation
flanking checks that filter out regex matches where:

- The opening delimiter is followed by punctuation but NOT preceded by whitespace,
  punctuation, or start of string (not left-flanking)
- The closing delimiter is preceded by punctuation but NOT followed by whitespace,
  punctuation, or end of string (not right-flanking)

## Automated Validation (Testing Performed)

### Unit Testing

10 new tests were added to `tests/test_strikethrough.py` covering the
tilde-in-parentheses bug and GFM punctuation flanking rules. All 295 project tests pass.

**Tilde-in-parentheses bug tests:**

- `test_tilde_before_and_inside_parens` — The core bug: `~100 (~200)` must stay as-is
- `test_tilde_before_and_inside_parens_fill` — Same bug through the full `fill_markdown`
  pipeline
- `test_tilde_only_inside_parens` — `100 (~200)` stays literal
- `test_tilde_inside_parens_with_text` — `~100 (x ~200)` stays literal
- `test_tilde_in_parens_then_outside` — `(~200) ~100` stays literal
- `test_tilde_before_parens_no_tilde_inside` — `~100 (200)` stays literal
- `test_tilde_in_brackets` — `~100 [~200]` stays literal (same flanking logic with `[`)

**Valid strikethrough near punctuation (no false negatives):**

- `test_strikethrough_inside_parens` — `(~~text~~) end` preserves valid strikethrough
- `test_strikethrough_after_punctuation` — `"~~text~~" end` preserves valid strikethrough
- `test_strikethrough_with_punctuation_content` — `~~hello!~~ end` preserves valid
  strikethrough

**Pre-existing tests (all still pass):**

- `test_literal_tildes_before_numbers` — `~60 seconds, ~130 words` stays literal
- `test_double_tilde_strikethrough` — `~~strikethrough~~` preserved
- `test_single_tilde_strikethrough` — `~text~` normalized to `~~text~~`
- `test_multiple_strikethroughs` — Multiple `~one~ and ~two~` preserved
- `test_single_tilde_no_closer` — `~50%` stays literal
- `test_tildes_with_space_before_closer` — `~100 to ~200` stays literal
- `test_tilde_space_after_opener` / `test_tilde_space_before_closer` — Whitespace flanking
- `test_escaped_tildes_preserved` — `\~60` stays escaped
- `test_strikethrough_in_paragraph` — Mixed strikethrough and literal tildes in paragraphs

### Code Changes

- `src/flowmark/formats/flowmark_markdown.py` — Added `_is_unicode_punctuation()` helper
  and `find()` override to `CustomStrikethrough`
- `tests/test_strikethrough.py` — Added 10 new test cases

### Manual Testing Needed

1. **Spot-check the CLI** on the reproduction case from the bug report:

   ```bash
   echo '~100 (~200)' | flowmark -
   ```

   Expected output: `~100 (~200)` (tildes NOT doubled)

2. **Verify valid strikethrough still works:**

   ```bash
   echo '~~deleted~~ text' | flowmark -
   ```

   Expected output: `~~deleted~~ text`

## Open Questions

None.
