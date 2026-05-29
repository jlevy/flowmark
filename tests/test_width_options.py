from flowmark.reformat_api import reformat_text


def test_normal_width_wrapping():
    """Test that normal width values work as expected."""
    text = "This is a long line that should definitely be wrapped at narrow widths but fits on one line at wide widths."

    # Test narrow width
    result_40 = reformat_text(text, width=40, plaintext=True)
    lines_40 = result_40.strip().split("\n")
    assert len(lines_40) > 1, "Text should be wrapped at width 40"

    # Test wide width
    result_200 = reformat_text(text, width=200, plaintext=True)
    lines_200 = result_200.strip().split("\n")
    assert len(lines_200) == 1, "Text should fit on one line at width 200"


def test_zero_width_disables_wrapping():
    """Test that width=0 disables wrapping entirely."""
    text = "This is a very long line that would normally be wrapped at any reasonable width setting but should remain as a single line when wrapping is disabled."

    # Width 0 should disable wrapping
    result = reformat_text(text, width=0, plaintext=True)
    lines = result.strip().split("\n")
    assert len(lines) == 1, "Width 0 should disable wrapping and keep text on one line"
    assert result.strip() == text, "Text should be unchanged except for whitespace normalization"


def test_negative_width_disables_wrapping():
    """Test that negative width values disable wrapping entirely."""
    text = "This is a very long line that would normally be wrapped at any reasonable width setting but should remain as a single line when wrapping is disabled."

    # Negative width should disable wrapping
    result = reformat_text(text, width=-1, plaintext=True)
    lines = result.strip().split("\n")
    assert len(lines) == 1, "Negative width should disable wrapping and keep text on one line"
    assert result.strip() == text, "Text should be unchanged except for whitespace normalization"


def test_width_zero_with_semantic():
    """Test that width=0 works correctly with semantic mode."""
    text = "This is sentence one. This is sentence two. This is sentence three."

    # With semantic mode and width 0, should still be one line
    result = reformat_text(text, width=0, plaintext=True, semantic=True)
    lines = result.strip().split("\n")
    assert len(lines) == 1, "Width 0 with semantic should still keep text on one line"


def test_width_zero_with_markdown():
    """Test that width=0 works correctly with markdown mode."""
    text = "This is a long paragraph that would normally be wrapped but should remain on one line when width is 0."

    # Markdown mode with width 0
    result = reformat_text(text, width=0, plaintext=False)
    # Remove trailing newline that markdown mode adds
    content = result.rstrip("\n")
    lines = content.split("\n")
    assert len(lines) == 1, "Width 0 with markdown should keep paragraph on one line"


def test_width_zero_with_markdown_semantic():
    """Test that width=0 works correctly with markdown semantic mode."""
    text = "This is sentence one. This is sentence two. This is sentence three."

    # Markdown semantic mode with width 0
    result = reformat_text(text, width=0, plaintext=False, semantic=True)
    # Remove trailing newline that markdown mode adds
    content = result.rstrip("\n")
    lines = content.split("\n")
    assert len(lines) == 1, "Width 0 with markdown semantic should keep text on one line"


def test_existing_behavior_unchanged():
    """Test that existing default behavior is unchanged."""
    text = "This is a test line that should be wrapped at the default width of 88 characters."

    # Default behavior should be unchanged
    result_default = reformat_text(text, plaintext=True)
    result_88 = reformat_text(text, width=88, plaintext=True)
    assert result_default == result_88, "Default behavior should match explicit width=88"

    # Should wrap at default width (line is longer than 88 chars)
    long_text = "This is a very long line that definitely exceeds 88 characters and should be wrapped when using the default width setting."
    result = reformat_text(long_text, plaintext=True)
    lines = result.strip().split("\n")
    assert len(lines) > 1, "Long text should be wrapped at default width"


def test_task_list_idempotent_semantic_width0():
    """Task list items must not accumulate spaces after the checkbox (issue #42)."""
    text = "- [ ] Unchecked item one\n- [x] Checked item one\n- Normal list item\n"

    once = reformat_text(text, width=0, semantic=True)
    twice = reformat_text(once, width=0, semantic=True)
    assert once == twice
    assert "- [ ] Unchecked item one" in once
    assert "- [x] Checked item one" in once
    assert "]  " not in once  # no double space after the checkbox


def test_task_list_idempotent_semantic_default_width():
    text = "- [ ] First task\n- [x] Second task\n"

    once = reformat_text(text, width=88, semantic=True)
    twice = reformat_text(once, width=88, semantic=True)
    assert once == twice
    assert "]  " not in once
