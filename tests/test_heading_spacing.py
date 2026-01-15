"""
Test heading spacing behavior.

This test documents the expected behavior for blank line spacing around headings,
including the corner case where headings end with hard breaks.
"""

from textwrap import dedent

from flowmark.formats.flowmark_markdown import ListSpacing
from flowmark.linewrapping.markdown_filling import fill_markdown


def test_heading_spacing_basic():
    """Test that headings have exactly one blank line after them."""
    input_doc = dedent(
        """
        ## Heading One
        First paragraph.

        ### Heading Two
        Second paragraph.
        """
    ).strip()

    expected_doc = (
        dedent(
            """
            ## Heading One

            First paragraph.

            ### Heading Two

            Second paragraph.
            """
        ).strip()
        + "\n"
    )

    normalized_doc = fill_markdown(input_doc, semantic=True)
    assert normalized_doc == expected_doc


def test_heading_spacing_before_list():
    """Test that headings have exactly one blank line before list items."""
    input_doc = dedent(
        """
        ## Section Title
        - First item
        - Second item
        """
    ).strip()

    expected_doc = (
        dedent(
            """
            ## Section Title

            - First item

            - Second item
            """
        ).strip()
        + "\n"
    )

    normalized_doc = fill_markdown(input_doc, semantic=True, list_spacing=ListSpacing.loose)
    assert normalized_doc == expected_doc


def test_heading_spacing_before_quote():
    """Test that headings have exactly one blank line before quote blocks."""
    input_doc = dedent(
        """
        ## Section Title
        > This is a quote.
        """
    ).strip()

    expected_doc = (
        dedent(
            """
            ## Section Title

            > This is a quote.
            """
        ).strip()
        + "\n"
    )

    normalized_doc = fill_markdown(input_doc, semantic=True)
    assert normalized_doc == expected_doc


def test_heading_spacing_before_code():
    """Test that headings have exactly one blank line before code blocks."""
    input_doc = dedent(
        """
        ## Section Title
        ```python
        print("hello")
        ```
        """
    ).strip()

    expected_doc = (
        dedent(
            """
            ## Section Title

            ```python
            print("hello")
            ```
            """
        ).strip()
        + "\n"
    )

    normalized_doc = fill_markdown(input_doc, semantic=True)
    assert normalized_doc == expected_doc


def test_heading_with_hard_break():
    """
    Test that headings ending with hard breaks don't add extra blank lines.

    This is an important corner case: when a heading ends with a backslash
    (Markdown hard break), the content continues on the next line, so we
    should NOT add an extra blank line after the heading.
    """
    input_doc = r"""# Comment before\
code()
# Another comment\
more_code()"""

    expected_doc = r"""# Comment before\
code()
# Another comment\
more_code()
"""

    normalized_doc = fill_markdown(input_doc, semantic=True, dedent_input=False)
    assert normalized_doc == expected_doc


def test_heading_with_hard_break_in_list():
    """Test hard breaks in headings within list items."""
    input_doc = dedent(
        r"""
        - Item with heading and hard break:
          ## Heading\
          continuation text
        """
    ).strip()

    expected_doc = (
        dedent(
            r"""
            - Item with heading and hard break:
              ## Heading\
              continuation text
            """
        ).strip()
        + "\n"
    )

    normalized_doc = fill_markdown(input_doc, semantic=True)
    assert normalized_doc == expected_doc


def test_hard_breaks_in_paragraphs():
    """Test that hard breaks in regular paragraphs are preserved without extra spacing."""
    input_doc = r"""First line\
second line\
third line"""

    expected_doc = r"""First line\
second line\
third line
"""

    normalized_doc = fill_markdown(input_doc, semantic=True, dedent_input=False)
    assert normalized_doc == expected_doc


def test_hard_breaks_after_comments():
    """
    Test hard breaks after comment lines are preserved correctly.

    This tests the specific case found in code examples where comment lines
    ending with hard breaks should not have blank lines inserted after them.
    """
    input_doc = r"""# Write data\
temp_file.write(...)
# Ensure data is on disk\
temp_file.flush()
# Close the file\
temp_file.close()"""

    expected_doc = r"""# Write data\
temp_file.write(...)
# Ensure data is on disk\
temp_file.flush()
# Close the file\
temp_file.close()
"""

    normalized_doc = fill_markdown(input_doc, semantic=True, dedent_input=False)
    assert normalized_doc == expected_doc


def test_hard_breaks_in_list_items():
    """Test hard breaks within list items."""
    input_doc = dedent(
        r"""
        - First line of item\
          second line of item\
          third line of item
        """
    ).strip()

    expected_doc = (
        dedent(
            r"""
            - First line of item\
              second line of item\
              third line of item
            """
        ).strip()
        + "\n"
    )

    normalized_doc = fill_markdown(input_doc, semantic=True)
    assert normalized_doc == expected_doc
