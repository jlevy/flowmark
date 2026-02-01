"""Tests for section reference detection and renaming."""

from flowmark.transforms.section_references import (
    GithubSlugger,
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
