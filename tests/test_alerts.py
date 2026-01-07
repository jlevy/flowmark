"""
Test GitHub alert/callout block handling.

This test documents the expected behavior for GitHub-flavored Markdown alerts
(callouts) like > [!NOTE], > [!TIP], etc.

Critical robustness requirement: Quote formatting must NEVER be stripped,
even for misspelled or unknown alert types. Unknown types should fall back
to regular quote handling, preserving all content.
"""

from textwrap import dedent

from flowmark.linewrapping.markdown_filling import fill_markdown


def test_basic_note_alert():
    """Test that NOTE alerts are preserved correctly."""
    input_doc = dedent(
        """
        > [!NOTE]
        > This is a note alert.
        """
    ).strip()

    expected_doc = (
        dedent(
            """
            > [!NOTE]
            > This is a note alert.
            """
        ).strip()
        + "\n"
    )

    normalized_doc = fill_markdown(input_doc, semantic=True)
    assert normalized_doc == expected_doc


def test_all_valid_alert_types():
    """Test all five valid GitHub alert types are preserved."""
    alert_types = ["NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"]

    for alert_type in alert_types:
        input_doc = f"> [!{alert_type}]\n> Content for {alert_type.lower()} alert."
        normalized_doc = fill_markdown(input_doc, semantic=True)

        # Verify alert header is preserved
        assert f"> [!{alert_type}]" in normalized_doc, f"Alert type {alert_type} was not preserved"
        # Verify content is preserved
        assert f"{alert_type.lower()} alert" in normalized_doc, f"Content for {alert_type} was lost"
        # Verify quote formatting is preserved
        assert normalized_doc.startswith(">"), f"Quote formatting lost for {alert_type}"


def test_lowercase_alert_normalized_to_uppercase():
    """Test that lowercase alert types are normalized to uppercase."""
    input_doc = dedent(
        """
        > [!note]
        > This lowercase alert should be normalized.
        """
    ).strip()

    normalized_doc = fill_markdown(input_doc, semantic=True)

    # Should be normalized to uppercase
    assert "> [!NOTE]" in normalized_doc
    assert "> [!note]" not in normalized_doc
    # Content preserved
    assert "normalized" in normalized_doc


def test_misspelled_alert_preserves_quote():
    """
    CRITICAL: Misspelled alert types must NOT cause quote formatting to be stripped.
    They should fall back to regular quote handling.
    """
    test_cases = [
        ("> [!NOOT]\n> Content here", "[!NOOT]"),
        ("> [!WARNNG]\n> Content here", "[!WARNNG]"),  # Missing 'I'
        ("> [!WARNUNG]\n> Content here", "[!WARNUNG]"),
        ("> [!NOTEE]\n> Content here", "[!NOTEE]"),
        ("> [!HINT]\n> Content here", "[!HINT]"),
    ]

    for input_doc, misspelled_type in test_cases:
        normalized_doc = fill_markdown(input_doc, semantic=True)

        # Quote formatting MUST be preserved
        assert normalized_doc.startswith(">"), f"Quote formatting lost for {misspelled_type}"
        # Content must be preserved (the misspelled type becomes part of the content)
        assert misspelled_type in normalized_doc, f"Content lost for {misspelled_type}"
        assert "Content here" in normalized_doc, f"Body content lost for {misspelled_type}"


def test_unknown_alert_types_preserve_quote():
    """
    CRITICAL: Unknown/custom alert types must NOT cause quote formatting to be stripped.
    """
    test_cases = [
        "> [!FOO]\n> Foo type",
        "> [!CUSTOM]\n> Custom type",
        "> [!INFO]\n> Info type",
        "> [!DANGER]\n> Danger type",
        "> [!SUCCESS]\n> Success type",
    ]

    for input_doc in test_cases:
        normalized_doc = fill_markdown(input_doc, semantic=True)

        # Quote formatting MUST be preserved
        assert normalized_doc.startswith(">"), f"Quote formatting lost for: {input_doc[:20]}"
        # All content must be preserved
        lines = input_doc.split("\n")
        for line in lines:
            # The content should be in the output (possibly reformatted)
            content = line.lstrip("> ")
            assert content in normalized_doc, f"Content '{content}' was lost"


def test_empty_alert_type_preserves_quote():
    """Empty alert brackets should not cause quote formatting to be stripped."""
    input_doc = "> [!]\n> Some content"
    normalized_doc = fill_markdown(input_doc, semantic=True)

    assert normalized_doc.startswith(">"), "Quote formatting lost for empty alert type"
    assert "Some content" in normalized_doc


def test_malformed_alert_preserves_quote():
    """Malformed alert syntax should not cause quote formatting to be stripped."""
    test_cases = [
        "> [NOTE]\n> Missing exclamation mark",
        "> [!NOTE\n> Missing closing bracket",
        "> ![NOTE]\n> Wrong order of symbols",
        "> [! NOTE]\n> Space after exclamation",
    ]

    for input_doc in test_cases:
        normalized_doc = fill_markdown(input_doc, semantic=True)
        # Quote formatting MUST be preserved
        assert normalized_doc.startswith(">"), f"Quote formatting lost for: {input_doc[:30]}"


def test_alert_with_multiline_content():
    """Test alerts with multiple lines of content."""
    input_doc = dedent(
        """
        > [!NOTE]
        > First line of content.
        > Second line of content.
        > Third line of content.
        """
    ).strip()

    normalized_doc = fill_markdown(input_doc, semantic=True)

    assert "> [!NOTE]" in normalized_doc
    # Content should be wrapped but preserved
    assert "First line" in normalized_doc
    assert "content" in normalized_doc


def test_alert_with_multiple_paragraphs():
    """Test alerts with multiple paragraphs separated by blank quote lines."""
    input_doc = dedent(
        """
        > [!TIP]
        > First paragraph.
        >
        > Second paragraph.
        """
    ).strip()

    # Note: blank lines in quotes are rendered as "> " (with trailing space)
    expected_doc = "> [!TIP]\n> First paragraph.\n> \n> Second paragraph.\n"

    normalized_doc = fill_markdown(input_doc, semantic=True)
    assert normalized_doc == expected_doc


def test_alert_with_code_block():
    """Test alerts containing fenced code blocks."""
    input_doc = dedent(
        """
        > [!WARNING]
        > Be careful with this code:
        >
        > ```python
        > dangerous_operation()
        > ```
        """
    ).strip()

    normalized_doc = fill_markdown(input_doc, semantic=True)

    assert "> [!WARNING]" in normalized_doc
    assert "```python" in normalized_doc
    assert "dangerous_operation()" in normalized_doc


def test_alert_with_list():
    """Test alerts containing bullet lists."""
    input_doc = dedent(
        """
        > [!IMPORTANT]
        > Remember:
        >
        > - First item
        > - Second item
        """
    ).strip()

    normalized_doc = fill_markdown(input_doc, semantic=True)

    assert "> [!IMPORTANT]" in normalized_doc
    assert "First item" in normalized_doc
    assert "Second item" in normalized_doc


def test_multiple_alerts_in_document():
    """Test multiple alerts in the same document."""
    input_doc = dedent(
        """
        > [!NOTE]
        > First note.

        Some text between.

        > [!WARNING]
        > A warning.
        """
    ).strip()

    normalized_doc = fill_markdown(input_doc, semantic=True)

    assert "> [!NOTE]" in normalized_doc
    assert "> [!WARNING]" in normalized_doc
    assert "First note" in normalized_doc
    assert "A warning" in normalized_doc
    assert "Some text between" in normalized_doc


def test_alert_after_heading():
    """Test alert immediately after a heading."""
    input_doc = dedent(
        """
        ## Section Title

        > [!NOTE]
        > Important note for this section.
        """
    ).strip()

    normalized_doc = fill_markdown(input_doc, semantic=True)

    assert "## Section Title" in normalized_doc
    assert "> [!NOTE]" in normalized_doc
    assert "Important note" in normalized_doc


def test_regular_quote_still_works():
    """Ensure regular quotes without alert syntax still work correctly."""
    input_doc = dedent(
        """
        > This is a regular quote.
        > It has multiple lines.
        """
    ).strip()

    normalized_doc = fill_markdown(input_doc, semantic=True)

    assert normalized_doc.startswith(">")
    assert "regular quote" in normalized_doc


def test_quote_with_link_like_content():
    """Test quote with content that looks like but isn't an alert."""
    input_doc = dedent(
        """
        > Check out [!this link](https://example.com) for more info.
        """
    ).strip()

    normalized_doc = fill_markdown(input_doc, semantic=True)

    assert normalized_doc.startswith(">")
    assert "[!this link]" in normalized_doc or "this link" in normalized_doc
