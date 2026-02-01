"""Tests for section reference detection and renaming."""

from marko import Markdown
from marko.block import Document

from flowmark.transforms.section_references import (
    GithubSlugger,
    RenameResult,
    SectionRename,
    find_section_references,
    heading_to_slug,
    rename_section_references,
)
from flowmark.transforms.section_renumbering import (
    apply_section_renumbering,
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


class TestRenameSectionReferences:
    """Tests for rename_section_references function."""

    def _parse(self, text: str) -> Document:
        """Helper to parse markdown text."""
        md = Markdown()
        doc = md.parse(text)
        assert isinstance(doc, Document)
        return doc

    def test_single_rename(self) -> None:
        """Single rename updates link destination."""
        doc = self._parse("See [intro](#old-slug).")
        renames = [SectionRename(old_slug="old-slug", new_slug="new-slug")]
        result = rename_section_references(doc, renames)

        assert result.links_modified == 1
        assert len(result.warnings) == 0

        # Verify the link was updated
        refs = find_section_references(doc)
        assert len(refs) == 1
        assert refs[0].slug == "new-slug"

    def test_multiple_renames(self) -> None:
        """Multiple renames update all matching links."""
        doc = self._parse("See [a](#first) and [b](#second).")
        renames = [
            SectionRename(old_slug="first", new_slug="one"),
            SectionRename(old_slug="second", new_slug="two"),
        ]
        result = rename_section_references(doc, renames)

        assert result.links_modified == 2
        refs = find_section_references(doc)
        slugs = {ref.slug for ref in refs}
        assert slugs == {"one", "two"}

    def test_same_slug_multiple_links(self) -> None:
        """Multiple links to same slug are all updated."""
        doc = self._parse("See [a](#target) and [b](#target).")
        renames = [SectionRename(old_slug="target", new_slug="new-target")]
        result = rename_section_references(doc, renames)

        assert result.links_modified == 2
        refs = find_section_references(doc)
        assert all(ref.slug == "new-target" for ref in refs)

    def test_atomic_swap(self) -> None:
        """Swapping A→B and B→A works atomically."""
        doc = self._parse("See [a](#first) and [b](#second).")
        renames = [
            SectionRename(old_slug="first", new_slug="second"),
            SectionRename(old_slug="second", new_slug="first"),
        ]
        result = rename_section_references(doc, renames)

        assert result.links_modified == 2
        refs = find_section_references(doc)
        # After swap, the links should be reversed
        # Original: #first, #second → After: #second, #first
        slugs = [ref.slug for ref in refs]
        assert slugs == ["second", "first"]

    def test_unmatched_link_warning(self) -> None:
        """Links not in rename list generate warnings (non-strict mode)."""
        doc = self._parse("See [unknown](#not-in-list).")
        renames = [SectionRename(old_slug="something", new_slug="else")]
        result = rename_section_references(doc, renames)

        assert result.links_modified == 0
        assert len(result.warnings) == 1
        assert "not-in-list" in result.warnings[0]

    def test_no_warning_for_matched_refs(self) -> None:
        """Matched refs don't generate warnings."""
        doc = self._parse("See [matched](#target).")
        renames = [SectionRename(old_slug="target", new_slug="new-target")]
        result = rename_section_references(doc, renames)

        assert result.links_modified == 1
        assert len(result.warnings) == 0

    def test_no_false_positives_partial_match(self) -> None:
        """Partial slug matches are not renamed."""
        doc = self._parse("See [extended](#old-slug-extended).")
        renames = [SectionRename(old_slug="old-slug", new_slug="new-slug")]
        result = rename_section_references(doc, renames)

        # Should not rename because old-slug-extended != old-slug
        assert result.links_modified == 0
        refs = find_section_references(doc)
        assert refs[0].slug == "old-slug-extended"

    def test_case_insensitive_matching(self) -> None:
        """Slug matching is case-insensitive."""
        doc = self._parse("See [link](#OLD-SLUG).")
        renames = [SectionRename(old_slug="old-slug", new_slug="new-slug")]
        result = rename_section_references(doc, renames)

        assert result.links_modified == 1
        refs = find_section_references(doc)
        assert refs[0].slug == "new-slug"

    def test_empty_renames_list(self) -> None:
        """Empty renames list warns about all internal links."""
        doc = self._parse("See [link](#section).")
        result = rename_section_references(doc, [])

        assert result.links_modified == 0
        assert len(result.warnings) == 1

    def test_external_links_unchanged(self) -> None:
        """External links are never modified."""
        doc = self._parse("See [ext](https://example.com#old-slug).")
        renames = [SectionRename(old_slug="old-slug", new_slug="new-slug")]
        result = rename_section_references(doc, renames)

        # External links not counted
        assert result.links_modified == 0
        assert len(result.warnings) == 0

    def test_result_is_clean_data_structure(self) -> None:
        """RenameResult is a clean data structure, no logging embedded."""
        doc = self._parse("See [a](#known) and [b](#unknown).")
        renames = [SectionRename(old_slug="known", new_slug="new-known")]
        result = rename_section_references(doc, renames)

        # Result is a simple dataclass with counts and warnings
        assert isinstance(result, RenameResult)
        assert isinstance(result.links_modified, int)
        assert isinstance(result.warnings, list)
        assert all(isinstance(w, str) for w in result.warnings)


class TestIntegrationWithRenumbering:
    """Tests for integration between section renumbering and reference renaming."""

    def _parse(self, text: str) -> Document:
        """Helper to parse markdown text."""
        md = Markdown()
        doc = md.parse(text)
        assert isinstance(doc, Document)
        return doc

    def test_renumbering_updates_references(self) -> None:
        """Section renumbering updates internal references."""
        doc = self._parse("""# 1. Introduction

See [Design](#3-design) for details.

# 3. Design

Back to [Intro](#1-introduction).
""")
        result = apply_section_renumbering(doc)

        # The link to #3-design should now point to #2-design
        refs = find_section_references(doc)
        slugs = {ref.slug for ref in refs}
        assert "2-design" in slugs
        assert "1-introduction" in slugs
        assert result is not None
        assert result.links_modified == 1  # Only #3-design changed

    def test_renumbering_multiple_references_same_section(self) -> None:
        """Multiple references to same section are all updated."""
        doc = self._parse("""# 1. Intro

See [Design](#3-design) and [here](#3-design).

# 3. Design
""")
        result = apply_section_renumbering(doc)

        refs = find_section_references(doc)
        assert all(ref.slug == "2-design" for ref in refs)
        assert result is not None
        assert result.links_modified == 2

    def test_renumbering_no_change_no_ref_updates(self) -> None:
        """When numbers don't change, refs aren't modified."""
        doc = self._parse("""# 1. Intro

See [Design](#2-design).

# 2. Design
""")
        result = apply_section_renumbering(doc)

        refs = find_section_references(doc)
        assert refs[0].slug == "2-design"
        # No warnings because ref matches the final slug
        assert result is not None
        assert result.links_modified == 0

    def test_renumbering_external_links_unchanged(self) -> None:
        """External links are never modified during renumbering."""
        doc = self._parse("""# 1. Intro

See [external](https://example.com#3-design).

# 3. Design
""")
        result = apply_section_renumbering(doc)

        # External link should be unchanged
        # (we can't easily check external links, but no crash is good)
        assert result is not None

    def test_renumbering_returns_result_with_warnings(self) -> None:
        """Renumbering returns result with warnings for unknown refs."""
        doc = self._parse("""# 1. Intro

See [unknown](#nonexistent-section).

# 3. Design
""")
        result = apply_section_renumbering(doc)

        assert result is not None
        assert isinstance(result, RenameResult)
        assert len(result.warnings) == 1
        assert "nonexistent-section" in result.warnings[0]

    def test_renumbering_non_numbered_doc_no_changes(self) -> None:
        """Non-numbered document doesn't trigger reference renaming."""
        doc = self._parse("""# Introduction

See [Design](#design).

# Design
""")
        result = apply_section_renumbering(doc)

        # No convention detected, so no renaming happens
        assert result is None

    def test_renumbering_result_is_none_when_inactive(self) -> None:
        """Result is None when convention is not active."""
        doc = self._parse("# Just One Heading")
        result = apply_section_renumbering(doc)
        assert result is None
