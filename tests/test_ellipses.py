from flowmark.typography.ellipses import ellipses


def test_ellipses():
    # Basic conversions, adding space only if needed next to a word character
    assert ellipses("word...") == "word …"
    assert ellipses("word ...") == "word …"
    assert ellipses("word  ...") == "word  …"
    assert ellipses("word ... ") == "word … "
    assert ellipses("word  ...  ") == "word  …  "

    assert ellipses("word...word") == "word … word"
    assert ellipses("word ... word") == "word … word"
    assert ellipses("word  ...  word") == "word  …  word"
    assert ellipses("Hello...World") == "Hello … World"

    assert ellipses("...word") == "… word"
    assert ellipses("... word") == "… word"
    assert ellipses(" ... word") == " … word"
    assert ellipses("word...") == "word …"
    assert ellipses("...") == "…"

    assert ellipses("I think... well... maybe...") == "I think … well … maybe …"
    assert ellipses("importtime... > import.log") == "importtime … > import.log"
    assert ellipses("First...second...third") == "First … second … third"
    assert ellipses("Wait... what... really?") == "Wait … what … really?"
    assert (
        ellipses("I was thinking... maybe we should go.") == "I was thinking … maybe we should go."
    )
    assert (
        ellipses("The options are... well... complicated.")
        == "The options are … well … complicated."
    )

    # Punctuation cases.
    assert ellipses("word....") == "word …."
    assert ellipses("word.... ") == "word …. "
    assert ellipses("word....  text") == "word ….  text"
    assert ellipses("word....word") == "word ….word"
    assert ellipses("He said...") == "He said …"
    assert ellipses("Really...?") == "Really …?"
    assert ellipses("Wait...!") == "Wait …!"
    assert ellipses("Well...,") == "Well …,"
    assert ellipses("word .... Another") == "word …. Another"

    assert ellipses("word.....") == "word....."
    assert ellipses("word......") == "word......"

    # Does not apply.
    assert ellipses("..") == ".."  # Only two dots
    assert ellipses(".") == "."  # Single dot
    assert ellipses(". . .") == ". . ."  # Spaced dots
    assert ellipses("$...") == "$..."  # Not preceded by word char or start
    assert ellipses("@...") == "@..."  # Not preceded by word char or start
    assert ellipses("#...") == "#..."  # Not preceded by word char or start
    assert ellipses("...@") == "...@"  # Not followed by word char or end
    assert ellipses("...$") == "...$"  # Not followed by word char or end ($ in pattern)
    assert ellipses("...#") == "...#"  # Not followed by word char or end

    # Multiline cases.
    assert (
        ellipses("First line...\nSecond line... continues\n...starts here")
        == "First line …\nSecond line … continues\n… starts here"
    )
    assert ellipses("Hello....\n") == "Hello ….\n"

    # Edge cases.
    assert ellipses("") == ""
    assert ellipses("No ellipses here") == "No ellipses here"
    assert ellipses("   ") == "   "
    assert ellipses("....") == "…."
    assert ellipses(" ....") == " …."

    # Code-like cases
    assert ellipses("if (x...) {") == "if (x...) {"
    assert ellipses("[...]") == "[...]"
    assert ellipses("{...}") == "{...}"
    assert ellipses("path/to/...") == "path/to/..."

    # Four dots followed by word gets space
    assert ellipses("word....word") == "word ….word"
    assert ellipses("word....123") == "word ….123"

    # Quote cases
    assert ellipses("'...word") == "'… word"
    assert ellipses("'... word") == "'… word"
    assert ellipses('"...word') == '"… word'
    assert ellipses('"... word') == '"… word'
    assert ellipses("'...word'") == "'… word'"
    assert ellipses('"...word"') == '"… word"'
    assert ellipses("'...'") == "'…'"
    assert ellipses('"..."') == '"…"'
    assert ellipses("word...'") == "word …'"
    assert ellipses('word..."') == 'word …"'
    assert ellipses("word...'next") == "word …'next"
    assert ellipses('word..."next') == 'word …"next'
    assert ellipses("He said '...'") == "He said '…'"
    assert ellipses('She said "..."') == 'She said "…"'
    assert ellipses("word...”") == "word …”"
    assert ellipses("word...’") == "word …’"
    assert ellipses("“changes”...") == "“changes”…"
