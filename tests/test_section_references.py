"""Tests for section reference detection and renaming."""

from marko import Markdown
from marko.block import Document

from flowmark.transforms.section_references import (
    GithubSlugger,
    find_section_references,
    heading_to_slug,
)


class TestHeadingToSlug:
    """Tests for the heading_to_slug function."""

    def test_basic_lowercase(self) -> None:
        """Basic heading is lowercased."""
        assert heading_to_slug("Introduction") == "introduction"

    def test_with_numbers(self) -> None:
        """Numbers are preserved in slug."""
        assert heading_to_slug("1. Design") == "1-design"

    def test_multiple_numbers(self) -> None:
        """Multiple number components work correctly."""
        assert heading_to_slug("1.2 Details") == "12-details"

    def test_special_chars_removed(self) -> None:
        """Special characters like apostrophes and question marks are removed."""
        assert heading_to_slug("What's New?") == "whats-new"

    def test_spaces_to_hyphens(self) -> None:
        """Spaces become hyphens."""
        assert heading_to_slug("Design Overview") == "design-overview"

    def test_multiple_spaces(self) -> None:
        """Multiple spaces become single hyphen."""
        assert heading_to_slug("Design   Overview") == "design-overview"

    def test_leading_trailing_spaces(self) -> None:
        """Leading and trailing spaces/hyphens are removed."""
        assert heading_to_slug("  Spaces  Around  ") == "spaces-around"

    def test_uppercase_preserved_as_lower(self) -> None:
        """Uppercase is converted to lowercase."""
        assert heading_to_slug("UPPERCASE") == "uppercase"

    def test_mixed_case(self) -> None:
        """Mixed case is lowercased."""
        assert heading_to_slug("Mixed-Case") == "mixed-case"

    def test_numbers_in_text(self) -> None:
        """Numbers within text are preserved."""
        assert heading_to_slug("Numbers 123 Here") == "numbers-123-here"

    def test_unicode_letters_preserved(self) -> None:
        """Unicode letters are preserved."""
        assert heading_to_slug("Привет World") == "привет-world"

    def test_parentheses_removed(self) -> None:
        """Parentheses are removed."""
        assert heading_to_slug("Method (deprecated)") == "method-deprecated"

    def test_brackets_removed(self) -> None:
        """Brackets are removed."""
        assert heading_to_slug("Array[0]") == "array0"

    def test_colons_removed(self) -> None:
        """Colons are removed."""
        assert heading_to_slug("Note: Important") == "note-important"

    def test_roman_numerals(self) -> None:
        """Roman numeral headings work."""
        assert heading_to_slug("I.A Background") == "ia-background"

    def test_empty_after_strip(self) -> None:
        """Edge case: heading that becomes empty returns empty string."""
        assert heading_to_slug("???") == ""

    def test_only_numbers(self) -> None:
        """Heading with only numbers."""
        assert heading_to_slug("123") == "123"

    def test_hyphen_preserved(self) -> None:
        """Existing hyphens are preserved."""
        assert heading_to_slug("pre-existing-hyphen") == "pre-existing-hyphen"


class TestGithubSlugger:
    """Tests for the GithubSlugger class that tracks duplicates."""

    def test_first_slug_no_suffix(self) -> None:
        """First occurrence has no suffix."""
        slugger = GithubSlugger()
        assert slugger.slug("Introduction") == "introduction"

    def test_duplicate_gets_suffix(self) -> None:
        """Second occurrence of same heading gets -1 suffix."""
        slugger = GithubSlugger()
        assert slugger.slug("Foo") == "foo"
        assert slugger.slug("Foo") == "foo-1"

    def test_triple_duplicate(self) -> None:
        """Third occurrence gets -2 suffix."""
        slugger = GithubSlugger()
        assert slugger.slug("Bar") == "bar"
        assert slugger.slug("Bar") == "bar-1"
        assert slugger.slug("Bar") == "bar-2"

    def test_different_headings_no_conflict(self) -> None:
        """Different headings don't conflict."""
        slugger = GithubSlugger()
        assert slugger.slug("Intro") == "intro"
        assert slugger.slug("Design") == "design"
        assert slugger.slug("Intro") == "intro-1"

    def test_reset_clears_tracking(self) -> None:
        """Reset clears duplicate tracking."""
        slugger = GithubSlugger()
        assert slugger.slug("Test") == "test"
        assert slugger.slug("Test") == "test-1"
        slugger.reset()
        assert slugger.slug("Test") == "test"

    def test_case_insensitive_duplicates(self) -> None:
        """Different cases are treated as duplicates (slugs are lowercase)."""
        slugger = GithubSlugger()
        assert slugger.slug("Test") == "test"
        assert slugger.slug("TEST") == "test-1"
        assert slugger.slug("test") == "test-2"

    def test_numbered_headings_unique(self) -> None:
        """Numbered headings are naturally unique due to different numbers."""
        slugger = GithubSlugger()
        assert slugger.slug("1. Overview") == "1-overview"
        assert slugger.slug("2. Overview") == "2-overview"


class TestFindSectionReferences:
    """Tests for find_section_references function."""

    def _parse(self, text: str) -> Document:
        """Helper to parse markdown text."""
        md = Markdown()
        doc = md.parse(text)
        assert isinstance(doc, Document)
        return doc

    def test_find_inline_internal_link(self) -> None:
        """Find inline internal links with # prefix."""
        doc = self._parse("See [intro](#introduction).")
        refs = find_section_references(doc)
        assert len(refs) == 1
        assert refs[0].slug == "introduction"
        assert refs[0].is_internal is True

    def test_find_multiple_internal_links(self) -> None:
        """Find multiple internal links."""
        doc = self._parse("See [intro](#intro) and [design](#design).")
        refs = find_section_references(doc)
        assert len(refs) == 2
        slugs = {ref.slug for ref in refs}
        assert slugs == {"intro", "design"}

    def test_skip_external_url(self) -> None:
        """External URLs are not section references."""
        doc = self._parse("See [example](https://example.com#section).")
        refs = find_section_references(doc)
        assert len(refs) == 0

    def test_skip_cross_file_reference(self) -> None:
        """Cross-file references are not internal."""
        doc = self._parse("See [other](./other.md#section).")
        refs = find_section_references(doc)
        assert len(refs) == 0

    def test_reference_style_link(self) -> None:
        """Reference-style links are resolved."""
        doc = self._parse("""See [intro][ref].

[ref]: #introduction
""")
        refs = find_section_references(doc)
        assert len(refs) == 1
        assert refs[0].slug == "introduction"

    def test_mixed_links(self) -> None:
        """Mix of internal and external links."""
        doc = self._parse("""
See [intro](#introduction), [external](https://example.com),
and [other file](./docs.md#section).
""")
        refs = find_section_references(doc)
        assert len(refs) == 1
        assert refs[0].slug == "introduction"

    def test_empty_document(self) -> None:
        """Empty document has no references."""
        doc = self._parse("")
        refs = find_section_references(doc)
        assert len(refs) == 0

    def test_document_with_no_links(self) -> None:
        """Document without links has no references."""
        doc = self._parse("# Heading\n\nJust some text.")
        refs = find_section_references(doc)
        assert len(refs) == 0

    def test_preserves_element_reference(self) -> None:
        """SectionRef contains the actual link element."""
        doc = self._parse("See [intro](#introduction).")
        refs = find_section_references(doc)
        assert len(refs) == 1
        assert refs[0].element is not None
        assert refs[0].element.dest == "#introduction"

    def test_link_in_list(self) -> None:
        """Find links inside list items."""
        doc = self._parse("- See [intro](#introduction)")
        refs = find_section_references(doc)
        assert len(refs) == 1
        assert refs[0].slug == "introduction"

    def test_link_in_nested_structure(self) -> None:
        """Find links in nested block structures."""
        doc = self._parse("""
> Quote with [link](#section)

- List with [another](#other)
""")
        refs = find_section_references(doc)
        assert len(refs) == 2
        slugs = {ref.slug for ref in refs}
        assert slugs == {"section", "other"}
