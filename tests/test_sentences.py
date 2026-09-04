from flowmark import first_sentence, split_sentences_regex

LONG_TEXT = """
End of sentence must be two letters or more,
with the last letter lowercase, followed by a period, exclamation point,
question mark. A final or preceding parenthesis or quote is allowed.
Does not break on colon or semicolon as that seems to have false
positives too often with code or other syntax.
"""

FIRST_SENTENCE = "End of sentence must be two letters or more, with the last letter lowercase, followed by a period, exclamation point, question mark."


def test_split_sentences():
    assert split_sentences_regex("test!") == ["test!"]
    assert split_sentences_regex("test! random words") == ["test! random words"]

    split_sentences = split_sentences_regex(LONG_TEXT)
    print(split_sentences)
    assert len(split_sentences) == 3
    assert split_sentences[0] == FIRST_SENTENCE


def test_first_sentence():
    assert first_sentence(LONG_TEXT) == FIRST_SENTENCE

    assert first_sentence("") == ""
    assert first_sentence(" ") == " "
    assert first_sentence("hello") == "hello"
    assert first_sentence(" hello\n") == "hello"


def test_split_sentences_ends_with_inline_code():
    """Regression for #68: a sentence may end in a code span terminated by punctuation."""
    text = (
        "The first part of this text is long enough here. Now run the deploy `deploy.sh`. "
        "Then we verify the results together."
    )
    sentences = split_sentences_regex(text)
    assert len(sentences) == 3
    assert sentences[1] == "Now run the deploy `deploy.sh`."
    assert sentences[2] == "Then we verify the results together."


def test_split_sentences_ends_with_emphasis():
    """Regression for #68: bold/italic/strikethrough delimiters right after the terminator."""
    text = (
        "The first part of this text is long enough here. In the end this is *very important*. "
        "So we should keep it in mind."
    )
    sentences = split_sentences_regex(text)
    assert len(sentences) == 3
    assert sentences[1] == "In the end this is *very important*."

    text2 = "The first part of this text is long enough here. Just ~~do it~~. And then move along now."
    sentences2 = split_sentences_regex(text2)
    assert len(sentences2) == 3
    assert sentences2[1] == "Just ~~do it~~."


def test_sentence_break_with_trailing_asterisk():
    """A lone asterisk after a terminator still allows the break (#68)."""
    text = "The first part of this text is long enough here. This little trick works.* And the rest goes on here."
    sentences = split_sentences_regex(text)
    assert len(sentences) == 3
    assert sentences[1] == "This little trick works.*"
