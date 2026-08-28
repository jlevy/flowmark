from dataclasses import dataclass
from pathlib import Path

import pytest

from flowmark.linewrapping.markdown_filling import fill_markdown

TESTDOC_DIR = Path(__file__).parent / "testdocs"


@dataclass(frozen=True)
class ReferenceCase:
    name: str
    filename: str
    semantic: bool
    cleanups: bool
    smartquotes: bool
    ellipses: bool = False


REFERENCE_CASES = (
    ReferenceCase(
        name="plain",
        filename="testdoc.expected.plain.md",
        semantic=False,
        cleanups=False,
        smartquotes=False,
    ),
    ReferenceCase(
        name="semantic",
        filename="testdoc.expected.semantic.md",
        semantic=True,
        cleanups=False,
        smartquotes=False,
    ),
    ReferenceCase(
        name="cleaned",
        filename="testdoc.expected.cleaned.md",
        semantic=True,
        cleanups=True,
        smartquotes=False,
    ),
    ReferenceCase(
        name="auto",
        filename="testdoc.expected.auto.md",
        semantic=True,
        cleanups=True,
        smartquotes=True,
        ellipses=True,
    ),
)


@pytest.mark.parametrize("case", REFERENCE_CASES, ids=lambda case: case.name)
def test_reference_doc_formats(case: ReferenceCase) -> None:
    """Keep the readable Python integration on the shared reference truth."""
    source = (TESTDOC_DIR / "testdoc.orig.md").read_text(encoding="utf-8")
    expected = (TESTDOC_DIR / case.filename).read_text(encoding="utf-8")

    actual = fill_markdown(
        source,
        semantic=case.semantic,
        cleanups=case.cleanups,
        smartquotes=case.smartquotes,
        ellipses=case.ellipses,
    )

    assert actual == expected, f"reference output differs for {case.name}"
