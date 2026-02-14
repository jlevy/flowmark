from flowmark.linewrapping.markdown_filling import fill_markdown
from flowmark.typography.smartquotes import smart_quotes


def test_basic_double_quotes():
    """Test basic double quote conversion."""
    assert smart_quotes('I\'m there with "George"') == "I\u2019m there with \u201cGeorge\u201d"
    assert smart_quotes('"Hello," he said.') == "\u201cHello,\u201d he said."
    assert smart_quotes('"I know!"') == "\u201cI know!\u201d"


def test_basic_single_quotes():
    """Test basic single quote conversion."""
    assert (
        smart_quotes("Words in 'single quotes' work too")
        == "Words in \u2018single quotes\u2019 work too"
    )
    assert smart_quotes("X is 'foo'") == "X is \u2018foo\u2019"


def test_apostrophes_and_contractions():
    """Test apostrophe and contraction conversion."""
    assert smart_quotes("I'm there") == "I\u2019m there"
    assert smart_quotes("I'll be there, don't worry") == "I\u2019ll be there, don\u2019t worry"
    assert smart_quotes("Jill's") == "Jill\u2019s"
    assert smart_quotes("James'") == "James\u2019"


def test_possessives_at_end_of_words():
    """Test possessives at the end of words ending in s."""
    assert smart_quotes("James'") == "James\u2019"
    assert smart_quotes("The students' books") == "The students\u2019 books"
    assert smart_quotes("Mr. Jones' house") == "Mr. Jones\u2019 house"
    assert smart_quotes("The cats' toys") == "The cats\u2019 toys"
    assert smart_quotes("Jesus' disciples") == "Jesus\u2019 disciples"
    assert smart_quotes("The class' performance") == "The class\u2019 performance"


def test_patterns_left_unchanged():
    """Test patterns that should remain unchanged."""
    assert smart_quotes("In the '60s") == "In the '60s"  # not worth special casing
    assert smart_quotes('x="foo"') == 'x="foo"'
    assert smart_quotes("x='foo'") == "x='foo'"
    assert smart_quotes("Blah'blah'blah") == "Blah'blah'blah"
    assert smart_quotes('""quotes"s') == '""quotes"s'
    assert smart_quotes('\\"escaped\\"') == '\\"escaped\\"'
    assert smart_quotes("'apos'trophes") == "'apos'trophes"


def test_quotes_with_punctuation():
    """Test quotes followed by various punctuation marks."""
    assert smart_quotes('"Hello,"') == "\u201cHello,\u201d"
    assert smart_quotes('"Wait;"') == "\u201cWait;\u201d"
    assert smart_quotes('"Stop:"') == "\u201cStop:\u201d"
    assert smart_quotes('"Really?"') == "\u201cReally?\u201d"
    assert smart_quotes('"Yes!"') == "\u201cYes!\u201d"
    assert smart_quotes('"End."') == "\u201cEnd.\u201d"
    assert smart_quotes('"Em dash"—') == "\u201cEm dash\u201d—"
    assert smart_quotes('"Parenthesis")') == "\u201cParenthesis\u201d)"
    assert smart_quotes("'Single em dash'—") == "\u2018Single em dash\u2019—"
    assert smart_quotes("'Single parenthesis')") == "\u2018Single parenthesis\u2019)"


def test_quotes_at_boundaries():
    """Test quotes at sentence boundaries."""
    assert smart_quotes('"Start of sentence"') == "\u201cStart of sentence\u201d"
    assert (
        smart_quotes('He said "middle of sentence" and continued')
        == "He said \u201cmiddle of sentence\u201d and continued"
    )


def test_mixed_quotes_and_apostrophes():
    """Test text with both quotes and apostrophes."""
    assert (
        smart_quotes('I\'m reading "The Great Gatsby" today')
        == "I\u2019m reading \u201cThe Great Gatsby\u201d today"
    )
    assert (
        smart_quotes('She said "I can\'t believe it!"')
        == "She said \u201cI can\u2019t believe it!\u201d"
    )


def test_edge_cases():
    """Test edge cases."""
    assert smart_quotes("") == ""
    assert smart_quotes("No quotes here") == "No quotes here"
    assert smart_quotes('Just "quotes"') == "Just \u201cquotes\u201d"
    assert smart_quotes("'Single'") == "\u2018Single\u2019"


def test_multiple_quotes_in_text():
    """Test text with multiple separate quoted sections."""
    assert (
        smart_quotes('He said "hello" and she said "goodbye"')
        == "He said \u201chello\u201d and she said \u201cgoodbye\u201d"
    )
    assert (
        smart_quotes("The words 'yes' and 'no' are opposites")
        == "The words \u2018yes\u2019 and \u2018no\u2019 are opposites"
    )


def test_complex_sentences():
    """Test more complex real-world sentences."""
    text = "John said \"I can't believe it's not butter!\" at the store."
    expected = "John said \u201cI can\u2019t believe it\u2019s not butter!\u201d at the store."
    assert smart_quotes(text) == expected


def test_technical_content_unchanged():
    """Test that technical content is not modified."""
    assert smart_quotes('function("param")') == 'function("param")'
    assert smart_quotes("array['key']") == "array['key']"
    assert smart_quotes('height="100px"') == 'height="100px"'
    assert smart_quotes("class='my-class'") == "class='my-class'"


def test_complex_cases_unchanged():
    """Test that nested or complex quote patterns are left alone."""
    assert smart_quotes('quote"in"quote') == 'quote"in"quote'
    assert smart_quotes('""nested""') == '""nested""'
    assert smart_quotes("''nested''") == "''nested''"
    assert smart_quotes('""nested"') == '""nested"'
    assert smart_quotes("'nested''") == "'nested''"
    assert smart_quotes('x="foo"') == 'x="foo"'
    assert smart_quotes("x='foo'") == "x='foo'"
    assert smart_quotes("Blah'blah'blah") == "Blah'blah'blah"
    assert smart_quotes('""quotes"s') == '""quotes"s'
    assert smart_quotes('\\"escaped\\"') == '\\"escaped\\"'
    assert smart_quotes("'apos") == "'apos"
    assert smart_quotes("'apos'trophes") == "'apos'trophes"
    assert smart_quotes("$James'") == "$James'"


def test_quotes_with_newlines():
    """Test quotes that contain newlines."""
    # Double quotes with newlines
    assert smart_quotes('"Hello\nWorld"') == "\u201cHello\nWorld\u201d"
    assert smart_quotes('He said "Hello\nWorld" today') == "He said \u201cHello\nWorld\u201d today"
    assert (
        smart_quotes('"First line\nSecond line\nThird line"')
        == "\u201cFirst line\nSecond line\nThird line\u201d"
    )

    # Single quotes with newlines
    assert smart_quotes("'Hello\nWorld'") == "\u2018Hello\nWorld\u2019"
    assert (
        smart_quotes("She said 'Hello\nWorld' today") == "She said \u2018Hello\nWorld\u2019 today"
    )
    assert (
        smart_quotes("'First line\nSecond line\nThird line'")
        == "\u2018First line\nSecond line\nThird line\u2019"
    )

    # With punctuation after newline quotes
    assert smart_quotes('"Hello\nWorld".') == "\u201cHello\nWorld\u201d."
    assert smart_quotes('"Hello\nWorld"!') == "\u201cHello\nWorld\u201d!"
    assert smart_quotes("'Hello\nWorld'?") == "\u2018Hello\nWorld\u2019?"

    # Mixed with contractions
    assert (
        smart_quotes('I\'m reading "Hello\nWorld" today')
        == "I\u2019m reading \u201cHello\nWorld\u201d today"
    )

    # Multiple paragraphs in quotes should NOT be converted
    text = '"This is paragraph one.\n\nThis is paragraph two."'
    expected = '"This is paragraph one.\n\nThis is paragraph two."'  # Unchanged
    assert smart_quotes(text) == expected

    # Quotes at start and end of lines
    text = '"Start of text\nMiddle line\nEnd of text"'
    expected = "\u201cStart of text\nMiddle line\nEnd of text\u201d"
    assert smart_quotes(text) == expected

    # Basic paragraph break
    assert smart_quotes('"Para 1.\n\nPara 2."') == '"Para 1.\n\nPara 2."'
    assert smart_quotes("'Para 1.\n\nPara 2.'") == "'Para 1.\n\nPara 2.'"

    # Paragraph break with spaces
    assert smart_quotes('"Para 1.\n \nPara 2."') == '"Para 1.\n \nPara 2."'
    assert smart_quotes('"Para 1.\n  \nPara 2."') == '"Para 1.\n  \nPara 2."'
    assert smart_quotes('"Para 1.\n\t\nPara 2."') == '"Para 1.\n\t\nPara 2."'

    # Multiple paragraph breaks
    assert smart_quotes('"Para 1.\n\nPara 2.\n\nPara 3."') == '"Para 1.\n\nPara 2.\n\nPara 3."'

    # Paragraph break in context
    text = 'He said "Para 1.\n\nPara 2." yesterday.'
    expected = 'He said "Para 1.\n\nPara 2." yesterday.'
    assert smart_quotes(text) == expected

    # Mixed: some with paragraph breaks, some without
    text = 'She said "Hello world" and he said "Para 1.\n\nPara 2." today.'
    expected = 'She said \u201cHello world\u201d and he said "Para 1.\n\nPara 2." today.'
    assert smart_quotes(text) == expected


# ---- Integration tests: smart quoting in container types ----


def test_smart_quotes_in_table_cells():
    """Test that smart quotes are applied inside GFM table cells."""
    text = '| User Says | Response |\n| --- | --- |\n| "Hello there" | "Goodbye" |\n'
    result = fill_markdown(text, smartquotes=True)
    assert "\u201cHello there\u201d" in result
    assert "\u201cGoodbye\u201d" in result


def test_smart_quotes_apostrophes_in_table_cells():
    """Test that apostrophes are converted inside table cells."""
    text = "| User Says |\n| --- |\n| There's a bug |\n"
    result = fill_markdown(text, smartquotes=True)
    assert "There\u2019s" in result


def test_smart_quotes_in_table_preserve_code_spans():
    """Test that code spans inside table cells are not modified."""
    text = '| Description | Command |\n| --- | --- |\n| "Fix a bug" | `tbd create "..." --type=bug` |\n'
    result = fill_markdown(text, smartquotes=True)
    # The prose quotes should be converted
    assert "\u201cFix a bug\u201d" in result
    # The code span should be unchanged
    assert '`tbd create "..." --type=bug`' in result


def test_smart_quotes_in_strikethrough():
    """Test that smart quotes are applied inside strikethrough text."""
    text = '~~"Hello" and don\'t~~ rest of text\n'
    result = fill_markdown(text, smartquotes=True)
    assert "\u201cHello\u201d" in result
    assert "don\u2019t" in result


def test_smart_quotes_spanning_code_span():
    """Test quotes that span across a code span within a paragraph."""
    text = '**Tell the user:** "First, install the `markform` command."\n'
    result = fill_markdown(text, smartquotes=True)
    assert "\u201cFirst," in result
    assert "command.\u201d" in result


def test_smart_quotes_spanning_code_span_in_blockquote():
    """Test quotes spanning a code span inside a blockquote."""
    text = '> **Tell the user:** "First, install the `markform` command."\n'
    result = fill_markdown(text, smartquotes=True)
    assert "\u201cFirst," in result
    assert "command.\u201d" in result


def test_smart_quotes_spanning_emphasis():
    """Test quotes that span across emphasis within a paragraph."""
    text = 'He said "this is *really* important."\n'
    result = fill_markdown(text, smartquotes=True)
    assert "\u201cthis" in result
    assert "important.\u201d" in result


def test_smart_quotes_spanning_strong_emphasis():
    """Test quotes that span across strong emphasis."""
    text = 'She said "this is **very** important."\n'
    result = fill_markdown(text, smartquotes=True)
    assert "\u201cthis" in result
    assert "important.\u201d" in result


def test_smart_quotes_spanning_link():
    """Test quotes that span across a link."""
    text = 'Read "the [documentation](https://example.com) first."\n'
    result = fill_markdown(text, smartquotes=True)
    assert "\u201cthe" in result
    assert "first.\u201d" in result


def test_smart_quotes_not_modifying_code_content():
    """Ensure code spans are never modified even when between smart-quoted text."""
    text = 'Use "the `x="value"` syntax" for this.\n'
    result = fill_markdown(text, smartquotes=True)
    # Code span content must be preserved exactly
    assert '`x="value"`' in result


def test_smart_quotes_apostrophe_spanning_code_span():
    """Test apostrophes in text around code spans."""
    text = "I'll use the `markform` tool and it'll work.\n"
    result = fill_markdown(text, smartquotes=True)
    assert "I\u2019ll" in result
    assert "it\u2019ll" in result


def test_smart_quotes_in_table_with_bold():
    """Test smart quotes in table cells containing bold text."""
    text = '| Column |\n| --- |\n| **Issues/Beads** |\n| "There\'s a bug" |\n'
    result = fill_markdown(text, smartquotes=True)
    assert "\u201cThere\u2019s a bug\u201d" in result


def test_smart_quotes_complex_table():
    """Test the specific table from the bug report."""
    text = (
        "| User Says | You (the Agent) Run |\n"
        "| --- | --- |\n"
        "| **Issues/Beads** |  |\n"
        '| "There\'s a bug where ..." | `tbd create "..." --type=bug` |\n'
        '| "Create a task/feature for ..." | `tbd create "..." --type=task` or `--type=feature` |\n'
    )
    result = fill_markdown(text, smartquotes=True)
    # Prose quotes should be converted
    assert "\u201cThere\u2019s a bug where \u2026\u201d" in result or "\u201cThere\u2019s a bug where ...\u201d" in result
    assert "\u201cCreate a task/feature for \u2026\u201d" in result or "\u201cCreate a task/feature for ...\u201d" in result
    # Code spans should be unchanged
    assert '`tbd create "..." --type=bug`' in result
    assert '`tbd create "..." --type=task`' in result


def test_smart_quotes_blockquote_multiline_with_code_span():
    """Test the specific blockquote from the bug report."""
    text = (
        '> **Tell the user:** "First, I\'ll make sure Markform is installed.\n'
        "> Markform is a CLI tool for creating structured forms that agents can fill via tool\n"
        "> calls. I'll install it globally so we can use the `markform` command.\"\n"
    )
    result = fill_markdown(text, semantic=True, smartquotes=True)
    # The outer quotes should be converted to smart quotes
    assert "\u201cFirst," in result
    assert "command.\u201d" in result
    # Apostrophes should also be converted
    assert "I\u2019ll" in result
    # Code span must be preserved
    assert "`markform`" in result
