"""
Test list spacing behavior with different modes: preserve, loose, and tight.

This test documents the expected behavior for blank line spacing in markdown lists,
with control over tight vs loose list formatting.

- preserve: Keep lists tight or loose as authored (default)
- loose: Convert all lists to loose format (blank lines between items)
- tight: Convert all lists to tight format where possible
"""

from textwrap import dedent

from flowmark.formats.flowmark_markdown import ListSpacing
from flowmark.linewrapping.markdown_filling import fill_markdown

# --- Tests for preserve mode (default) ---


def test_tight_list_preserved():
    """Tight lists stay tight in preserve mode."""
    input_doc = "- one\n- two\n- three\n"
    output = fill_markdown(input_doc, list_spacing=ListSpacing.preserve)
    assert output == "- one\n- two\n- three\n"


def test_loose_list_preserved():
    """Loose lists stay loose in preserve mode."""
    input_doc = "- one\n\n- two\n\n- three\n"
    output = fill_markdown(input_doc, list_spacing=ListSpacing.preserve)
    assert output == "- one\n\n- two\n\n- three\n"


def test_preserve_is_default():
    """Preserve is the default mode."""
    input_tight = "- one\n- two\n- three\n"
    input_loose = "- one\n\n- two\n\n- three\n"

    # Without explicit list_spacing, tight stays tight
    assert fill_markdown(input_tight) == "- one\n- two\n- three\n"
    # Without explicit list_spacing, loose stays loose
    assert fill_markdown(input_loose) == "- one\n\n- two\n\n- three\n"


def test_numbered_list_preserve():
    """Numbered lists preserve their tightness."""
    input_tight = "1. one\n2. two\n3. three\n"
    input_loose = "1. one\n\n2. two\n\n3. three\n"

    assert (
        fill_markdown(input_tight, list_spacing=ListSpacing.preserve)
        == "1. one\n2. two\n3. three\n"
    )
    assert (
        fill_markdown(input_loose, list_spacing=ListSpacing.preserve)
        == "1. one\n\n2. two\n\n3. three\n"
    )


# --- Tests for loose mode ---


def test_tight_list_to_loose():
    """Tight lists become loose in loose mode."""
    input_doc = "- one\n- two\n- three\n"
    output = fill_markdown(input_doc, list_spacing=ListSpacing.loose)
    assert output == "- one\n\n- two\n\n- three\n"


def test_loose_list_stays_loose():
    """Loose lists stay loose in loose mode."""
    input_doc = "- one\n\n- two\n\n- three\n"
    output = fill_markdown(input_doc, list_spacing=ListSpacing.loose)
    assert output == "- one\n\n- two\n\n- three\n"


def test_numbered_list_to_loose():
    """Numbered lists become loose in loose mode."""
    input_doc = "1. one\n2. two\n3. three\n"
    output = fill_markdown(input_doc, list_spacing=ListSpacing.loose)
    assert output == "1. one\n\n2. two\n\n3. three\n"


# --- Tests for tight mode ---


def test_loose_list_to_tight():
    """Loose lists become tight in tight mode."""
    input_doc = "- one\n\n- two\n\n- three\n"
    output = fill_markdown(input_doc, list_spacing=ListSpacing.tight)
    assert output == "- one\n- two\n- three\n"


def test_tight_list_stays_tight():
    """Tight lists stay tight in tight mode."""
    input_doc = "- one\n- two\n- three\n"
    output = fill_markdown(input_doc, list_spacing=ListSpacing.tight)
    assert output == "- one\n- two\n- three\n"


def test_multi_para_stays_loose_in_tight_mode():
    """Multi-paragraph items stay loose even in tight mode (CommonMark requirement)."""
    input_doc = (
        dedent(
            """
        - para1

          para2
        - item2
        """
        ).strip()
        + "\n"
    )

    output = fill_markdown(input_doc, list_spacing=ListSpacing.tight)
    # Item with multiple paragraphs forces loose
    assert "\n\n" in output


# --- Tests for nested lists ---


def test_nested_lists_independent_preserve():
    """Each nested list independently preserves its tightness."""
    input_doc = (
        dedent(
            """
        - outer tight
          - inner tight
          - inner tight
        - outer tight
        """
        ).strip()
        + "\n"
    )

    output = fill_markdown(input_doc, list_spacing=ListSpacing.preserve)
    # Both outer and inner should remain tight
    expected = (
        dedent(
            """
        - outer tight
          - inner tight
          - inner tight
        - outer tight
        """
        ).strip()
        + "\n"
    )
    assert output == expected


def test_nested_lists_loose_outer_tight_inner():
    """Loose outer list with tight inner list."""
    input_doc = (
        dedent(
            """
        - outer loose

          - inner tight
          - inner tight

        - outer loose
        """
        ).strip()
        + "\n"
    )

    output = fill_markdown(input_doc, list_spacing=ListSpacing.preserve)
    # Outer should be loose, inner should be tight
    expected = (
        dedent(
            """
        - outer loose

          - inner tight
          - inner tight

        - outer loose
        """
        ).strip()
        + "\n"
    )
    assert output == expected


# --- Tests for complex content (code blocks, quotes) ---


def test_list_items_with_code_blocks_preserve():
    """List items with code blocks preserve tightness in preserve mode."""
    input_doc = (
        dedent(
            """
        - Use `z` (zoxide) instead of `cd`.

          ```shell
          z ~/some/long/path/to/foo
          ```

        - Use `eza` instead of `ls`.
        """
        ).strip()
        + "\n"
    )

    expected_doc = (
        dedent(
            """
        - Use `z` (zoxide) instead of `cd`.

          ```shell
          z ~/some/long/path/to/foo
          ```

        - Use `eza` instead of `ls`.
        """
        ).strip()
        + "\n"
    )

    # This is loose in the input, should stay loose
    normalized_doc = fill_markdown(input_doc, semantic=True, list_spacing=ListSpacing.preserve)
    assert normalized_doc == expected_doc


def test_list_items_with_code_blocks_loose():
    """List items with code blocks get proper spacing in loose mode."""
    input_doc = (
        dedent(
            """
        - Use `z` (zoxide) instead of `cd`.

          ```shell
          z ~/some/long/path/to/foo
          ```

        - Use `eza` instead of `ls`. It has color support.
        """
        ).strip()
        + "\n"
    )

    expected_doc = (
        dedent(
            """
        - Use `z` (zoxide) instead of `cd`.

          ```shell
          z ~/some/long/path/to/foo
          ```

        - Use `eza` instead of `ls`. It has color support.
        """
        ).strip()
        + "\n"
    )

    normalized_doc = fill_markdown(input_doc, semantic=True, list_spacing=ListSpacing.loose)
    assert normalized_doc == expected_doc


def test_list_items_with_quote_blocks():
    """Test that list items with quote blocks get proper spacing."""
    input_doc = (
        dedent(
            """
        - First item with a quote.

          > This is a quote block.
          > With multiple lines.

        - Second item without quotes.
        """
        ).strip()
        + "\n"
    )

    expected_doc = (
        dedent(
            """
        - First item with a quote.

          > This is a quote block.
          > With multiple lines.

        - Second item without quotes.
        """
        ).strip()
        + "\n"
    )

    # This is loose in the input (has multi-block items)
    normalized_doc = fill_markdown(input_doc, semantic=True, list_spacing=ListSpacing.preserve)
    assert normalized_doc == expected_doc


# --- Tests for spacing normalization with loose mode ---


def test_input_spacing_normalization_loose():
    """Test that various input spacings normalize to loose output in loose mode."""
    # One newline between items (tight markdown)
    input_tight = "- First item\n- Second item\n- Third item\n"

    # Two newlines between items (loose)
    input_loose = "- First item\n\n- Second item\n\n- Third item\n"

    # Three newlines between items (extra spacing)
    input_extra = "- First item\n\n\n- Second item\n\n\n- Third item\n"

    # All should normalize to loose output
    expected_output = "- First item\n\n- Second item\n\n- Third item\n"

    assert fill_markdown(input_tight, list_spacing=ListSpacing.loose) == expected_output
    assert fill_markdown(input_loose, list_spacing=ListSpacing.loose) == expected_output
    assert fill_markdown(input_extra, list_spacing=ListSpacing.loose) == expected_output


def test_input_spacing_normalization_tight():
    """Test that various input spacings normalize to tight output in tight mode."""
    # One newline between items (tight markdown)
    input_tight = "- First item\n- Second item\n- Third item\n"

    # Two newlines between items (loose)
    input_loose = "- First item\n\n- Second item\n\n- Third item\n"

    # Three newlines between items (extra spacing)
    input_extra = "- First item\n\n\n- Second item\n\n\n- Third item\n"

    # All should normalize to tight output
    expected_output = "- First item\n- Second item\n- Third item\n"

    assert fill_markdown(input_tight, list_spacing=ListSpacing.tight) == expected_output
    assert fill_markdown(input_loose, list_spacing=ListSpacing.tight) == expected_output
    assert fill_markdown(input_extra, list_spacing=ListSpacing.tight) == expected_output


def test_complex_content_with_loose_mode():
    """Test that complex content gets proper spacing in loose mode."""
    input_doc = (
        dedent(
            """
        - Item before code
        - Item with code

          ```shell
          echo "test"
          ```
        - Item after code
        """
        ).strip()
        + "\n"
    )

    expected_output = (
        dedent(
            """
        - Item before code

        - Item with code

          ```shell
          echo "test"
          ```

        - Item after code
        """
        ).strip()
        + "\n"
    )

    assert (
        fill_markdown(input_doc, semantic=True, list_spacing=ListSpacing.loose) == expected_output
    )


def test_multi_paragraph_spacing_loose_mode():
    """Test that multi-paragraph items get consistent spacing in loose mode."""
    input_doc = (
        dedent(
            """
        - Simple item
        - Multi-paragraph item

          Second paragraph
        - Another simple item
        """
        ).strip()
        + "\n"
    )

    expected_output = (
        dedent(
            """
        - Simple item

        - Multi-paragraph item

          Second paragraph

        - Another simple item
        """
        ).strip()
        + "\n"
    )

    assert (
        fill_markdown(input_doc, semantic=True, list_spacing=ListSpacing.loose) == expected_output
    )
