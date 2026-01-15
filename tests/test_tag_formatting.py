"""
Tests for Markdoc/Jinja tag formatting edge cases.

These tests verify that:
1. Tags spanning multiple lines are handled correctly
2. Smart quotes do NOT apply inside tag attributes
3. Tags with complex nested structures (arrays, objects) are preserved
4. Various tag formatting styles are supported
"""

from __future__ import annotations

from textwrap import dedent

from flowmark import fill_markdown
from flowmark.linewrapping.line_wrappers import line_wrap_to_width
from flowmark.linewrapping.text_wrapping import _HtmlMdWordSplitter  # pyright: ignore
from flowmark.typography.smartquotes import smart_quotes

# Test 1: Basic attribute wrap at space
TAG_1 = dedent("""
    {% field kind="string" id="name" label="Name" role="user" required=true minLength=2
    maxLength=50 placeholder="Enter your name" %}
    {% /field %}
    """).strip()


# Test 2: Wrap with array spanning lines
TAG_2 = dedent("""
    {% field kind="string" id="colors" label="Colors" examples=["red", "green",
    "blue", "yellow"] %}
    {% /field %}
    """).strip()


# Test 3: Wrap inside array (mid-element)
TAG_3 = dedent("""
    {% field kind="string_list" id="tags" examples=["very long example one",
    "very long example two"] minItems=1 maxItems=5 %}
    {% /field %}
    """).strip()


# Test 4: Object value spanning lines
TAG_4 = dedent("""
    {% field kind="table" id="team" columnTypes=[{type: "string",
    required: true}, "number", "url"] columnIds=["name", "age", "website"] %}
    | Name | Age | Website |
    |------|-----|---------|
    {% /field %}
    """).strip()


# Test 5: Multiple wraps in one tag
TAG_5 = dedent("""
    {% field kind="url_list" id="references" label="References" role="user" minItems=1
    maxItems=5 uniqueItems=true placeholder="https://docs.example.com"
    examples=["https://wikipedia.org/wiki/Example", "https://docs.github.com/en"] %}
    {% /field %}
    """).strip()


# Test 6: Fully vertical formatting (one attr per line)
TAG_6 = dedent("""
    {% field
      kind="number"
      id="score"
      label="Score"
      role="user"
      min=0
      max=100
      required=true
    %}
    {% /field %}
    """).strip()


# Test 7: Indented continuation (common formatting style)
TAG_7 = dedent("""
    {% field kind="table" id="tasks" label="Project Tasks" role="user"
        minRows=0 maxRows=10
        columnIds=["task", "hours", "link"]
        columnTypes=["string", "number", "url"] %}
    | Task | Hours | Link |
    |------|-------|------|
    {% /field %}
    """).strip()


# Test 8: Selection field with wrapped attributes
TAG_8 = dedent("""
    {% field kind="single_select" id="priority" label="Priority" role="user"
    required=true %}
    - [ ] Low {% #low %}
    - [ ] High {% #high %}
    {% /field %}
    """).strip()


# Test 9: String containing %} (must not end tag early)
TAG_9 = dedent("""
    {% field kind="string" id="pattern_test" label="Pattern"
    pattern="test %} not end" required=true %}
    {% /field %}
    """).strip()


# Test 10: String containing newline escape
TAG_10 = dedent(r"""
    {% field kind="string" id="multiline" label="Notes"
    placeholder="Line1\nLine2" maxLength=500 %}
    {% /field %}
    """).strip()


# Test 11: Nested brackets in array
TAG_11 = dedent("""
    {% field kind="table" id="complex" columnTypes=[{type: "string", required: true},
    {type: "number", min: 0, max: 100}] columnIds=["name", "score"] %}
    | Name | Score |
    |------|-------|
    {% /field %}
    """).strip()


# Test 12: Empty/minimal content after wrap
TAG_12 = dedent("""
    {% field kind="string" id="minimal" label="Test" required=true
    %}{% /field %}
    """).strip()


ALL_TAGS = [TAG_1, TAG_2, TAG_3, TAG_4, TAG_5, TAG_6, TAG_7, TAG_8, TAG_9, TAG_10, TAG_11, TAG_12]


def _count_straight_quotes(text: str) -> int:
    """Count straight double quotes in text."""
    return text.count('"')


def _count_smart_quotes(text: str) -> int:
    """Count smart double quotes in text."""
    return text.count("\u201c") + text.count("\u201d")


def test_smart_quotes_not_applied_in_tag_attributes():
    """
    Verify that smart quotes are NOT applied to quotes inside Markdoc/Jinja tag attributes.

    This is critical because converting quotes like kind="string" to kind="string"
    would break the template syntax.
    """
    for i, tag in enumerate(ALL_TAGS, 1):
        original_straight = _count_straight_quotes(tag)
        result = smart_quotes(tag)
        result_straight = _count_straight_quotes(result)
        result_smart = _count_smart_quotes(result)

        # All straight quotes should be preserved
        assert result_straight == original_straight, (
            f"Test {i}: Straight quotes were converted. "
            f"Original: {original_straight}, Result: {result_straight}, Smart: {result_smart}\n"
            f"Input: {tag[:100]}...\n"
            f"Output: {result[:100]}..."
        )
        assert result_smart == 0, (
            f"Test {i}: Smart quotes were introduced.\n"
            f"Input: {tag[:100]}...\n"
            f"Output: {result[:100]}..."
        )


def test_tag_with_array_spanning_lines():
    """Test that arrays spanning multiple lines inside tags are preserved."""
    # This is a specific regression test for the bug where quotes after newlines
    # inside arrays were converted to smart quotes
    tag = '{% field examples=["one",\n"two", "three"] %}'

    result = smart_quotes(tag)
    assert result == tag, f"Array spanning lines was modified: {result}"


def test_tag_with_object_spanning_lines():
    """Test that objects spanning multiple lines inside tags are preserved."""
    tag = '{% field config={key: "value",\nother: "data"} %}'

    result = smart_quotes(tag)
    assert result == tag, f"Object spanning lines was modified: {result}"


def test_multiline_tag_with_surrounding_text():
    """Test multiline tags with regular text that SHOULD get smart quotes."""
    text = dedent("""
        Here is some "quoted text" that should be converted.

        {% field kind="string" examples=["one",
        "two"] %}
        {% /field %}

        And more "quoted text" here.
        """).strip()

    result = smart_quotes(text)

    # The prose quotes should be converted to smart quotes
    assert "\u201cquoted text\u201d" in result, "Prose quotes should be converted"

    # But tag attribute quotes should NOT be converted
    assert 'kind="string"' in result, "Tag attribute quotes should be preserved"
    assert 'examples=["one",' in result, "Array quotes should be preserved"
    assert '"two"]' in result, "Array quotes on continuation lines should be preserved"


def test_pipeline_preserves_tag_quotes():
    """Test that the full Markdown pipeline preserves tag attribute quotes."""
    for i, tag in enumerate(ALL_TAGS, 1):
        original_straight = _count_straight_quotes(tag)

        # Process through pipeline with smartquotes enabled
        result = fill_markdown(tag, smartquotes=True, semantic=True)

        result_straight = _count_straight_quotes(result)

        # All straight quotes in tags should be preserved
        assert result_straight == original_straight, (
            f"Test {i}: Pipeline converted quotes in tag.\n"
            f"Original straight: {original_straight}, Result straight: {result_straight}\n"
            f"Input:\n{tag}\n\nOutput:\n{result}"
        )


def test_tag_newlines_preserved_in_pipeline():
    """Test that newlines within multiline tags are preserved through the pipeline."""
    # Tag 6 has vertical formatting
    result = fill_markdown(TAG_6, semantic=True)

    # Should preserve the vertical structure
    assert "{% field\n" in result or "{% field " in result
    assert "%}\n{% /field %}" in result or "%}{% /field %}" in result


def test_word_splitter_handles_multiline_tags():
    """Test that the word splitter correctly handles multiline tags."""
    splitter = _HtmlMdWordSplitter()

    # Single line tag - should be kept together
    single = '{% field kind="string" id="name" %}'
    tokens = splitter(single)
    assert single in tokens, f"Single line tag should be atomic: {tokens}"

    # Multi-word tag - should be coalesced
    multi = '{% callout type="warning" title="Note" %}'
    tokens = splitter(multi)
    assert multi in tokens, f"Multi-word tag should be coalesced: {tokens}"


def test_line_wrapper_preserves_multiline_tags():
    """Test that line wrappers preserve structure of multiline tags."""
    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Tag with content that has newlines
    text = '{% field kind="string" %}\nContent here.\n{% /field %}'
    result = wrapper(text, "", "")

    # Newlines around tags should be preserved
    assert "{% field" in result
    assert "{% /field %}" in result


def test_tag_with_embedded_percent_brace():
    """Test that %} inside a string attribute doesn't end the tag early."""
    # This is TAG_9 - pattern contains %}
    result = fill_markdown(TAG_9, semantic=True)

    # The tag should still be properly formatted
    assert "{% field" in result
    assert "{% /field %}" in result
    # The pattern with %} should be preserved in the attribute
    assert 'pattern="test %} not end"' in result or "pattern=" in result


def test_jinja_variable_tags_in_prose():
    """Test that Jinja variable tags {{ }} work correctly."""
    text = 'Hello {{ user.name }}, welcome to "our site".'

    result = smart_quotes(text)

    # The prose quote should be converted
    assert "\u201cour site\u201d" in result
    # The variable tag should be unchanged
    assert "{{ user.name }}" in result


def test_jinja_comment_tags():
    """Test that Jinja comment tags {# #} are handled correctly."""
    text = '{# TODO: fix "this" later #} Some "quoted" text.'

    result = smart_quotes(text)

    # The prose quote should be converted
    assert "\u201cquoted\u201d" in result
    # Quotes inside comment tags should be preserved (ideally)
    # Note: Current implementation may convert these - document the behavior


def test_html_comment_tags_with_quotes():
    """Test that HTML comment tags with quotes are handled."""
    text = '<!-- f:field kind="string" --> Some "quoted" text <!-- /f:field -->'

    result = smart_quotes(text)

    # Prose quotes should be converted
    assert "\u201cquoted\u201d" in result
    # Tag attribute quotes should be preserved
    assert 'kind="string"' in result


def test_adjacent_closing_tags():
    """Test that %}{% stays adjacent (no space inserted)."""
    from flowmark.linewrapping.tag_handling import (
        denormalize_adjacent_tags,
        normalize_adjacent_tags,
    )

    original = "{% field %}{% /field %}"
    normalized = normalize_adjacent_tags(original)
    denormalized = denormalize_adjacent_tags(normalized)

    assert denormalized == original


def test_selection_field_with_task_list():
    """Test selection fields with task list items (TAG_8)."""
    result = fill_markdown(TAG_8, semantic=True)

    # Should preserve the list structure
    assert "- [ ] Low" in result or "- [ ]" in result
    assert "{% #low %}" in result
    assert "{% #high %}" in result
    assert "{% /field %}" in result


def test_smart_quotes_preserves_apostrophe_in_jinja_variable():
    """Test that apostrophes inside {{ }} variable tags are NOT converted."""
    # This is a regression test for the bug where won't was converted to won't
    text = "{{ won't }}"
    result = smart_quotes(text)
    # The apostrophe should remain straight
    assert result == text, f"Apostrophe in variable tag was converted: {result}"


def test_smart_quotes_preserves_double_quotes_in_include():
    """Test that double quotes in {% include %} are NOT converted."""
    text = '{% include "header.html" %}'
    result = smart_quotes(text)
    assert result == text, f"Quotes in include tag were converted: {result}"


def test_smart_quotes_preserves_single_quotes_in_attributes():
    """Test that single quotes in tag attributes are NOT converted."""
    text = "{% field kind='string' label='Name' %}"
    result = smart_quotes(text)
    assert result == text, f"Single quotes in tag were converted: {result}"


def test_smart_quotes_preserves_quotes_in_jinja_comments():
    """Test that quotes inside {# #} comment tags are NOT converted."""
    text = '{# "quoted text" in comment #}'
    result = smart_quotes(text)
    assert result == text, f"Quotes in Jinja comment were converted: {result}"


def test_smart_quotes_preserves_quotes_in_html_comments():
    """Test that quotes inside <!-- --> comment tags are NOT converted."""
    text = '<!-- f:field kind="string" -->'
    result = smart_quotes(text)
    assert result == text, f"Quotes in HTML comment were converted: {result}"


def test_smart_quotes_converts_prose_but_not_tags():
    """Test that prose quotes are converted but tag quotes are preserved."""
    text = 'She said "hello" and {% field label="Name" %} was set.'
    result = smart_quotes(text)

    # Prose quotes should be converted
    assert "\u201chello\u201d" in result, "Prose quotes should be converted"

    # Tag quotes should NOT be converted
    assert 'label="Name"' in result, "Tag attribute quotes should be preserved"


def test_smart_quotes_with_nunjucks_raw_block():
    """Test the specific Nunjucks raw block pattern from testdoc."""
    text = "{% raw %}This {{ won't }} be {% processed %}{% endraw %}"
    result = smart_quotes(text)
    # Everything inside raw blocks should be preserved
    assert result == text, f"Raw block content was modified: {result}"


def test_smart_quotes_multiline_tag_with_prose():
    """Test smart quotes with multiline tag surrounded by prose."""
    text = dedent("""
        He said "yes" to the form.

        {% field kind="string"
        label="Full Name"
        required=true %}
        {% /field %}

        She replied "no" later.
        """).strip()

    result = smart_quotes(text)

    # Prose quotes should be converted
    assert "\u201cyes\u201d" in result
    assert "\u201cno\u201d" in result

    # Tag quotes should NOT be converted
    assert 'kind="string"' in result
    assert 'label="Full Name"' in result


def test_multiline_opening_tag_closing_on_own_line():
    """
    Test that closing tags are placed on their own line after multiline opening tags.

    This is a regression test for GitHub issue #17: When an opening tag spans
    multiple lines, having the closing tag on the same line as the opening tag's
    closing delimiter breaks Markdoc's parser.
    """
    from flowmark.linewrapping.tag_handling import (
        _fix_multiline_opening_tag_with_closing,  # pyright: ignore[reportPrivateUsage]
    )

    # Pattern that triggers Markdoc bug: multi-line opening tag with closing on same line
    problematic = "{% field kind='string'\nrequired=true %}{% /field %}"
    result = _fix_multiline_opening_tag_with_closing(problematic)

    # Closing tag should be on its own line
    assert "%}\n{% /field %}" in result, f"Closing tag not on own line: {result}"


def test_single_line_paired_tags_not_split():
    """
    Test that single-line paired tags like {% field %}{% /field %} are NOT split.

    This is a regression test to ensure the fix for issue #17 doesn't affect
    single-line tags.
    """
    from flowmark.linewrapping.tag_handling import (
        _fix_multiline_opening_tag_with_closing,  # pyright: ignore[reportPrivateUsage]
    )

    # Single-line paired tag - should NOT be split
    single_line = "{% field kind='string' %}{% /field %}"
    result = _fix_multiline_opening_tag_with_closing(single_line)

    # Should remain on single line
    assert result == single_line, f"Single-line tag was incorrectly split: {result}"


def test_multiline_tag_through_pipeline():
    """Test multiline tags with closing on same line through the full pipeline."""
    # Use a tag that's long enough to actually trigger wrapping at width 88
    # This should produce the problematic pattern that triggers the Markdoc bug
    long_tag = (
        '{% field kind="string" id="name" label="Full Name" role="user" '
        'required=true minLength=2 maxLength=100 placeholder="Enter your full name" %}'
        "{% /field %}"
    )

    result = fill_markdown(long_tag, semantic=True, width=88)
    lines = result.strip().split("\n")

    # If the tag wrapped (longer than line width), closing tag should be on its own line
    if len(lines) >= 2:
        # Last line should be the closing tag on its own
        assert lines[-1].strip() == "{% /field %}", (
            f"Last line should be closing tag, got: {lines[-1]}"
        )
        # The line before closing tag should end with %}
        assert lines[-2].strip().endswith("%}"), (
            f"Line before closing should end with %}}, got: {lines[-2]}"
        )


def test_html_comment_multiline_closing():
    """Test HTML comment tags with multi-line opening and closing on same line."""
    from flowmark.linewrapping.tag_handling import (
        _fix_multiline_opening_tag_with_closing,  # pyright: ignore[reportPrivateUsage]
    )

    # HTML comment pattern
    text = "<!-- f:field kind='string'\nlabel='Name' --><!-- /f:field -->"
    result = _fix_multiline_opening_tag_with_closing(text)

    # Closing comment should be on its own line
    assert "-->\n<!-- /f:field -->" in result, f"HTML closing tag not split: {result}"
