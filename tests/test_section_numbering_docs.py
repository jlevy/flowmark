"""End-to-end document tests for section numbering and reference renaming."""

from pathlib import Path

from marko import Markdown

from flowmark.linewrapping.markdown_filling import fill_markdown
from flowmark.transforms.section_references import RenameResult
from flowmark.transforms.section_renumbering import apply_section_renumbering

testdoc_dir = Path("tests/testdocs")


def test_section_numbering_document():
    """
    End-to-end test for section renumbering with reference updates.

    Tests:
    - Headings are renumbered (3->2, 5->3, 7->4)
    - Internal references are updated (#3-design -> #2-design)
    - Cross-file references are NOT modified
    - External URLs are NOT modified
    - Unknown references generate warnings
    """
    orig_path = testdoc_dir / "section_numbering.orig.md"
    expected_path = testdoc_dir / "section_numbering.expected.md"

    assert orig_path.exists(), f"Original test document not found at {orig_path}"
    assert expected_path.exists(), f"Expected test document not found at {expected_path}"

    orig_content = orig_path.read_text()
    expected_content = expected_path.read_text()

    # Test with renumber_sections=True (includes reference renaming by default)
    actual = fill_markdown(orig_content, renumber_sections=True, rename_references=True)

    if actual != expected_content:
        actual_path = testdoc_dir / "section_numbering.actual.md"
        print("Actual was different from expected!")
        print(f"Saving actual to: {actual_path}")
        actual_path.write_text(actual)

    assert actual == expected_content


def test_section_numbering_without_reference_renaming():
    """
    Test that --no-rename-references disables reference updates.

    Headings should still be renumbered, but links should NOT be updated.
    """
    orig_path = testdoc_dir / "section_numbering.orig.md"
    orig_content = orig_path.read_text()

    # Test with rename_references=False
    actual = fill_markdown(orig_content, renumber_sections=True, rename_references=False)

    # Headings should be renumbered
    assert "# 2. Design" in actual
    assert "# 3. Implementation" in actual
    assert "# 4. Conclusion" in actual

    # But links should NOT be updated (still point to old slugs)
    assert "#3-design" in actual  # Old slug preserved
    assert "#5-implementation" in actual  # Old slug preserved


def test_rename_result_warnings_collected():
    """
    Test that RenameResult collects warnings for unknown references.

    The warning should be collected in the result data structure,
    NOT logged dynamically during processing.
    """
    md = Markdown()
    doc = md.parse("""# 1. Introduction

See [missing](#nonexistent-section).

# 3. Design
""")

    result = apply_section_renumbering(doc, rename_references=True)

    # Result should be a clean data structure
    assert isinstance(result, RenameResult)

    # Should have warning for unknown reference
    assert len(result.warnings) == 1
    assert "nonexistent-section" in result.warnings[0]


def test_rename_result_is_clean_data_structure():
    """
    Verify RenameResult is a clean data structure with expected fields.

    The result should contain:
    - links_modified: count of updated links
    - warnings: list of warning strings

    No logging should occur during rename_section_references() execution.
    """
    md = Markdown()
    doc = md.parse("""# 1. Introduction

See [Design](#3-design) and [unknown](#missing).

# 3. Design
""")

    result = apply_section_renumbering(doc, rename_references=True)

    # Verify it's a RenameResult
    assert isinstance(result, RenameResult)

    # Verify expected attributes exist and have correct types
    assert hasattr(result, "links_modified")
    assert hasattr(result, "warnings")
    assert isinstance(result.links_modified, int)
    assert isinstance(result.warnings, list)

    # links_modified should be 1 (#3-design -> #2-design)
    assert result.links_modified == 1

    # warnings should contain the unknown reference
    assert len(result.warnings) == 1
    assert all(isinstance(w, str) for w in result.warnings)
