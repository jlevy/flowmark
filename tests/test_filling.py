from textwrap import dedent

import marko

from flowmark.formats.flowmark_markdown import ListSpacing
from flowmark.linewrapping.markdown_filling import fill_markdown

_original_doc = dedent(
    """
# This is a header

This is sentence one. This is sentence two.
This is sentence three.
This is sentence four. This is sentence 5. This is sentence six.
Seven. Eight. Nine. Ten.
A [link](https://example.com). Some *emphasis* and **strong emphasis** and `code`.
And a     super-super-super-super-super-super-super-hyphenated veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery long word.
This is a sentence with many words and words and words and words and words and words and words and words.
And another with words and
words and words split across a line.

A second paragraph.


- This is a list item
- This is another list item
    - A sub item
        - A sub sub item
- This is a third list item with many words and words and words and words and words and words and words and words

    - A sub item
    - Another sub item

    
    - Another sub item (after a line break)

- This is a nice [Markdown auto-formatter](https://github.com/jlevy/kmd/blob/main/kmd/text_formatting/markdown_normalization.py),
  so text documents are saved in a normalized form that can be diffed consistently.

A third paragraph.

## Sub-heading

1. This is a numbered list item
2. This is another numbered list item

<!--window-br-->

<!--window-br--> Words and words and words and words and words and <span data-foo="bar">some HTML</span> and words and words and words and words and words and words.

<span data-foo="bar">Inline HTML.</span> And some following words and words and words and words and words and words.

<h1 data-foo="bar">Block HTML.</h1> And some following words.

<div class="foo">
Some more HTML. Words and words and words and words and    words and <span data-foo="bar">more HTML</span> and words and words and words and words and words and words.</div>

> This is a quote block. With a couple sentences. Note we have a `>` on this line.
>
> - Quotes can also contain lists.
> - With items. Like this. And these items may have long sentences in them.

```python
def hello_world():
    print("Hello, World!")

# End of code
```


```
more code
```


Indented code:

    more code here

    and more

- **Intelligent:** Kmd understands itself. It reads its own code and docs and gives you assistance!


<p style="max-width: 450px;">
“*Simple should be simple.
Complex should be possible.*” —Alan Kay
</p>

### Building

1. Lorem ipsum dolor sit amet, consectetur adipiscing elit. [Fork](https://github.com/jlevy/kmd/fork) this repo
   (having your own fork
   will make it
   easier to contribute actions, add models, etc.).

2. [Check out](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
   the code. Lorem [another link](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).

3. Install the package dependencies:

   ```shell
   poetry install
   ```
    """
).lstrip()

_expected_doc = dedent(
    """
# This is a header

This is sentence one.
This is sentence two.
This is sentence three.
This is sentence four.
This is sentence 5. This is sentence six.
Seven. Eight. Nine. Ten.
A [link](https://example.com).
Some *emphasis* and **strong emphasis** and `code`. And a
super-super-super-super-super-super-super-hyphenated
veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery
long word.
This is a sentence with many words and words and words and words and words and
words and words and words.
And another with words and words and words split across a line.

A second paragraph.

- This is a list item

- This is another list item

  - A sub item

    - A sub sub item

- This is a third list item with many words and words and words and words and words and
  words and words and words

  - A sub item

  - Another sub item

  - Another sub item (after a line break)

- This is a nice
  [Markdown auto-formatter](https://github.com/jlevy/kmd/blob/main/kmd/text_formatting/markdown_normalization.py),
  so text documents are saved in a normalized form that can be diffed consistently.

A third paragraph.

## Sub-heading

1. This is a numbered list item

2. This is another numbered list item

<!--window-br-->

<!--window-br--> Words and words and words and words and words and
<span data-foo="bar">some HTML</span> and words and words and words and words and words
and words.

<span data-foo="bar">Inline HTML.</span> And some following words and words and words
and words and words and words.

<h1 data-foo="bar">Block HTML.</h1> And some following words.

<div class="foo"> Some more HTML. Words and words and words and words and words and
<span data-foo="bar">more HTML</span> and words and words and words and words and words
and words.</div>

> This is a quote block.
> With a couple sentences.
> Note we have a `>` on this line.
> 
> - Quotes can also contain lists.
>
> - With items. Like this.
>   And these items may have long sentences in them.

```python
def hello_world():
    print("Hello, World!")

# End of code
```

```
more code
```

Indented code:

```
more code here

and more
```

- **Intelligent:** Kmd understands itself.
  It reads its own code and docs and gives you assistance!

<p style="max-width: 450px;"> “*Simple should be simple.
Complex should be possible.*” —Alan Kay </p>

### Building

1. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
   [Fork](https://github.com/jlevy/kmd/fork) this repo (having your own fork will make
   it easier to contribute actions, add models, etc.).

2. [Check out](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
   the code. Lorem
   [another link](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).

3. Install the package dependencies:

   ```shell
   poetry install
   ```
    """
).lstrip()


def test_normalize_markdown():
    parsed = marko.parse(_original_doc)
    print("---Parsed")
    print(parsed)

    normalized_doc = fill_markdown(_original_doc, semantic=True, list_spacing=ListSpacing.loose)

    print("---Before")
    print(_original_doc)
    print("---After")
    print(normalized_doc)

    assert normalized_doc == _expected_doc


def test_multi_paragraph_list_items():
    # Test that multi-paragraph list items get proper spacing between them.
    input_doc = dedent(
        """
    - **`make_parent_dirs(path: str | Path, mode: int = 0o777) -> Path`**

      Ensures that the parent directories for a file exist, creating them if necessary.
    - **`rmtree_or_file(path: str | Path, ignore_errors: bool = False)`**

      Removes the target even if it's a file, directory, or symlink.
    """
    ).strip()

    # The normalized output includes a trailing newline
    expected_doc = (
        dedent(
            """
    - **`make_parent_dirs(path: str | Path, mode: int = 0o777) -> Path`**

      Ensures that the parent directories for a file exist, creating them if necessary.

    - **`rmtree_or_file(path: str | Path, ignore_errors: bool = False)`**

      Removes the target even if it's a file, directory, or symlink.
    """
        ).strip()
        + "\n"
    )

    normalized_doc = fill_markdown(input_doc, semantic=True)

    print("---Input")
    print(input_doc)
    print("---Expected")
    print(expected_doc)
    print("---Output")
    print(normalized_doc)

    assert normalized_doc == expected_doc


def test_wide_table_adjacent_to_paragraph():
    """
    Test that a wide table row immediately following paragraph text (no blank line)
    is preserved on a single line by fill_markdown.

    This is the reproduction case from GitHub issue #36: Marko's GFM parser does not
    recognize a table when it directly follows paragraph text without a blank line.
    The table rows get parsed as part of the paragraph and were previously broken
    by the line wrapper.
    """
    # Table directly after paragraph (no blank line) — Marko parses as paragraph
    input_doc = dedent(
        """\
    Some paragraph text here.
    | Quarter | Revenue ($M) | YoY % | QoQ % | Segment A % | Segment B % | Geo: US % | Geo: Intl % |
    |---------|-------------|-------|-------|-------------|-------------|-----------|-------------|
    | Q1 2025 | 125.3 | +12% | +3% | 45% | 55% | 60% | 40% |
    """
    )

    for semantic in (True, False):
        result = fill_markdown(input_doc, semantic=semantic)

        # Every table row must remain on its own single line
        assert "| Quarter | Revenue ($M) | YoY % | QoQ % | Segment A % | Segment B % | Geo: US % | Geo: Intl % |" in result
        assert "| Q1 2025 | 125.3 | +12% | +3% | 45% | 55% | 60% | 40% |" in result

        # Verify rows are each on their own line (not merged with text)
        result_lines = result.strip().split("\n")
        table_lines = [l for l in result_lines if l.startswith("|")]
        assert len(table_lines) == 3, f"Expected 3 table lines, got {len(table_lines)} in {semantic=}"


def test_standalone_wide_table():
    """
    Test that a standalone wide table (properly parsed by GFM) continues to work.
    This is a regression guard — tables that GFM recognizes should not be affected.
    """
    input_doc = dedent(
        """\
    | Quarter | Revenue ($M) | YoY % | QoQ % | Segment A % | Segment B % | Geo: US % | Geo: Intl % |
    |---------|-------------|-------|-------|-------------|-------------|-----------|-------------|
    | Q1 2025 | 125.3 | +12% | +3% | 45% | 55% | 60% | 40% |
    | Q2 2025 | 131.7 | +15% | +5% | 46% | 54% | 58% | 42% |
    """
    )

    result = fill_markdown(input_doc, semantic=True)

    # All rows preserved
    assert "| Quarter | Revenue ($M) |" in result
    assert "| Q1 2025 |" in result
    assert "| Q2 2025 |" in result

    # Each row on its own line
    result_lines = result.strip().split("\n")
    table_lines = [l for l in result_lines if l.startswith("|")]
    assert len(table_lines) == 4  # header + separator + 2 data rows
