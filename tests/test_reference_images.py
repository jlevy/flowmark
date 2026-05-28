"""Test reference-style image rendering.

Reference images (``![alt][label]``, ``![alt][]``, ``![alt]``) are part of
CommonMark and `render_image` handles them via `LinkRefDef` lookup, but they
were previously uncovered by tests. `render_image` always emits the inline
form ``![alt](url{title})`` regardless of source syntax — these tests pin
that contract.

Background: the gap was surfaced by a port-side review during a Python →
Rust sync (see https://github.com/jlevy/flowmark/issues/50 and
https://github.com/jlevy/flowmark-rs/pull/59). Three latent parity bugs in
the Rust port traced back to the same root cause: faithfully mirroring
upstream tests inherits upstream blind spots. Closing the gap upstream
fixes it everywhere.

`render_link_ref_def` uses ``element.label`` which marko normalizes to
lowercase, so the rendered def line uses the lowercase label even when the
source label was uppercase.
"""

from flowmark.formats.flowmark_markdown import flowmark_markdown

# -----------------------------------------------------------------------------
# Reference images — every syntactic form inlines to ![alt](url).
# -----------------------------------------------------------------------------


def test_full_ref_image_inlined():
    """![alt][img] with a matching def → ![alt](url)."""
    md = flowmark_markdown()
    src = "![alt][img]\n\n[img]: https://example.com/img.png\n"
    expected = "![alt](https://example.com/img.png)\n\n[img]: https://example.com/img.png\n"
    assert md(src) == expected


def test_collapsed_ref_image_inlined():
    """![alt][] with a matching def for label=alt → ![alt](url)."""
    md = flowmark_markdown()
    src = "![alt][]\n\n[alt]: https://example.com/img.png\n"
    expected = "![alt](https://example.com/img.png)\n\n[alt]: https://example.com/img.png\n"
    assert md(src) == expected


def test_shortcut_ref_image_inlined():
    """![alt] (shortcut) with a matching def → ![alt](url)."""
    md = flowmark_markdown()
    src = "![alt]\n\n[alt]: https://example.com/img.png\n"
    expected = "![alt](https://example.com/img.png)\n\n[alt]: https://example.com/img.png\n"
    assert md(src) == expected


def test_full_ref_image_with_title():
    """Title from the def is included in the rendered inline form."""
    md = flowmark_markdown()
    src = '![alt][img]\n\n[img]: https://example.com/img.png "My title"\n'
    expected = (
        '![alt](https://example.com/img.png "My title")\n\n'
        '[img]: https://example.com/img.png "My title"\n'
    )
    assert md(src) == expected


def test_full_ref_image_label_with_spaces():
    """Labels with internal whitespace resolve correctly."""
    md = flowmark_markdown()
    src = "![Logo][company logo]\n\n[company logo]: https://example.com/logo.png\n"
    expected = (
        "![Logo](https://example.com/logo.png)\n\n[company logo]: https://example.com/logo.png\n"
    )
    assert md(src) == expected


def test_full_ref_image_label_case_insensitive():
    """marko normalizes labels to lowercase; the def line is emitted lowercase."""
    md = flowmark_markdown()
    src = "![alt][IMG]\n\n[Img]: https://example.com/img.png\n"
    expected = "![alt](https://example.com/img.png)\n\n[img]: https://example.com/img.png\n"
    assert md(src) == expected


def test_full_ref_image_empty_alt():
    """Empty alt text round-trips."""
    md = flowmark_markdown()
    src = "![][img]\n\n[img]: https://example.com/img.png\n"
    expected = "![](https://example.com/img.png)\n\n[img]: https://example.com/img.png\n"
    assert md(src) == expected


# -----------------------------------------------------------------------------
# Badge pattern — image nested inside a reference link, the canonical
# GitHub-badge shape.
# -----------------------------------------------------------------------------


def test_badge_full_ref_image_in_full_ref_link():
    """[![alt][img]][url] inlines the image; outer ref link is preserved."""
    md = flowmark_markdown()
    src = (
        "[![alt][img]][url]\n\n"
        "[img]: https://example.com/img.png\n"
        "[url]: https://example.com/page\n"
    )
    expected = (
        "[![alt](https://example.com/img.png)][url]\n\n"
        "[img]: https://example.com/img.png\n"
        "[url]: https://example.com/page\n"
    )
    assert md(src) == expected


def test_badge_collapsed_ref_image_in_full_ref_link():
    """[![alt][]][url] — collapsed-image variant of the badge pattern."""
    md = flowmark_markdown()
    src = "[![alt][]][url]\n\n[alt]: https://example.com/img.png\n[url]: https://example.com/page\n"
    expected = (
        "[![alt](https://example.com/img.png)][url]\n\n"
        "[alt]: https://example.com/img.png\n"
        "[url]: https://example.com/page\n"
    )
    assert md(src) == expected


def test_badge_shortcut_ref_image_in_full_ref_link():
    """[![alt]][url] — shortcut-image variant of the badge pattern."""
    md = flowmark_markdown()
    src = "[![alt]][url]\n\n[alt]: https://example.com/img.png\n[url]: https://example.com/page\n"
    expected = (
        "[![alt](https://example.com/img.png)][url]\n\n"
        "[alt]: https://example.com/img.png\n"
        "[url]: https://example.com/page\n"
    )
    assert md(src) == expected


def test_badge_inline_image_in_full_ref_link():
    """[![alt](url)][label] — fully inlined image inside an outer ref link."""
    md = flowmark_markdown()
    src = "[![alt](https://example.com/img.png)][url]\n\n[url]: https://example.com/page\n"
    expected = "[![alt](https://example.com/img.png)][url]\n\n[url]: https://example.com/page\n"
    assert md(src) == expected


# -----------------------------------------------------------------------------
# Idempotence — a second pass over the rendered output must produce no change.
# -----------------------------------------------------------------------------


def test_full_ref_image_idempotent():
    """Formatting reference images is stable across a second pass."""
    md = flowmark_markdown()
    src = "![alt][img]\n\n[img]: https://example.com/img.png\n"
    once = md(src)
    assert md(once) == once


def test_badge_full_ref_image_in_full_ref_link_idempotent():
    """The badge pattern's rendered output is a fixed point."""
    md = flowmark_markdown()
    src = (
        "[![alt][img]][url]\n\n"
        "[img]: https://example.com/img.png\n"
        "[url]: https://example.com/page\n"
    )
    once = md(src)
    assert md(once) == once
