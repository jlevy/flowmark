"""
Test that empty lines in code blocks don't get trailing whitespace.
"""

from textwrap import dedent

from flowmark.linewrapping.markdown_filling import fill_markdown


def test_empty_lines_in_code_blocks_no_whitespace():
    """Test that empty lines in code blocks remain truly empty."""
    input_doc = dedent(
        """
        ```bash
        # Install uv globally via pipx (recommended)
        pipx install uv

        # Or via the official installer
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```
        """
    ).strip()

    result = fill_markdown(input_doc, semantic=True)

    # Split into lines
    lines = result.split('\n')

    # The empty line should be at index 3 (after "pipx install uv")
    # It should be completely empty, no whitespace
    assert lines[3] == "", f"Empty line in code block should have no whitespace, got: {repr(lines[3])}"


def test_empty_lines_in_nested_code_blocks():
    """Test empty lines in code blocks inside list items."""
    input_doc = dedent(
        """
        - Example:

          ```python
          def foo():
              pass

          def bar():
              pass
          ```
        """
    ).strip()

    result = fill_markdown(input_doc, semantic=True)
    lines = result.split('\n')

    # Find the empty line inside the code block (after "pass")
    # It should be truly empty, even though the code block is indented in a list
    for i, line in enumerate(lines):
        if i > 0 and lines[i-1].strip() == "pass" and i < len(lines) - 1 and lines[i+1].strip().startswith("def bar"):
            assert line == "", f"Empty line in nested code block should have no whitespace, got: {repr(line)}"
            break
    else:
        # If we didn't find the expected pattern, fail
        assert False, "Could not find empty line pattern in output"


def test_code_block_with_multiple_empty_lines():
    """Test code blocks with multiple consecutive empty lines."""
    input_doc = dedent(
        """
        ```python
        line1


        line2
        ```
        """
    ).strip()

    result = fill_markdown(input_doc, semantic=True)
    lines = result.split('\n')

    # Lines 2 and 3 should be empty (indices 2, 3)
    assert lines[2] == "", f"First empty line should have no whitespace, got: {repr(lines[2])}"
    assert lines[3] == "", f"Second empty line should have no whitespace, got: {repr(lines[3])}"
