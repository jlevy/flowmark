from __future__ import annotations

import re
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, NamedTuple, cast

from marko import Markdown, Renderer, block, inline
from marko.block import HTMLBlock
from marko.ext import footnote
from marko.ext.gfm import GFM
from marko.ext.gfm import elements as gfm_elements
from marko.helpers import partition_by_spaces
from marko.parser import Parser
from marko.source import Source
from typing_extensions import override

from flowmark.linewrapping.line_wrappers import (
    LineWrapper,
    line_wrap_by_sentence,
    line_wrap_to_width,
)
from flowmark.linewrapping.text_filling import DEFAULT_WRAP_WIDTH


def _normalize_title_quotes(title: str) -> str:
    """
    Normalize title quotes.
    """
    escaped = title.strip('"').replace('"', '\\"')
    return f'"{escaped}"'


def _min_fence_length(code_content: str, fence_char: str = "`") -> int:
    """
    Calculate the minimum fence length needed for code content.

    Scans the content for sequences of the fence character at the start of lines
    and returns one more than the longest sequence found (minimum 3).

    Per CommonMark spec, the closing fence must have at least as many fence
    characters as the opening fence. Sequences only matter at the start of
    lines (with up to 3 spaces of indentation).
    """
    max_len = 0
    # Find all sequences of 3+ fence chars at start of line (with optional indent)
    pattern = rf"^[ ]{{0,3}}({re.escape(fence_char)}{{3,}})"
    for match in re.finditer(pattern, code_content, re.MULTILINE):
        fence = match.group(1)
        max_len = max(max_len, len(fence))

    # Need at least one more than the longest found, minimum 3
    return max(3, max_len + 1)


# XXX Turn off Marko's parsing of block HTML.
# Block parsing with comments or block elements has some counterintuitive issues:
# https://github.com/frostming/marko/issues/202
# Another solution might be to always put a newline after a closing block tag during
# normalization, to avoid this confusion?
# For now, just ignoring block tags.
class CustomHTMLBlock(HTMLBlock):
    @override
    @classmethod
    def match(cls, source: Source) -> int | bool:
        return False


class ExtendedParseInfo(NamedTuple):
    """Extended parse info that includes fence character and length."""

    prefix: str
    leading: str
    lang: str
    extra: str
    fence_char: str
    fence_len: int


class CustomFencedCode(block.FencedCode):
    """
    Extended FencedCode that preserves the fence character and length.

    This allows us to preserve the original fence style (backticks vs tildes)
    and length (3+ characters) when normalizing markdown.
    """

    lang: str
    extra: str
    children: list[inline.RawText]
    fence_char: str = "`"
    fence_len: int = 3

    def __init__(  # pyright: ignore[reportMissingSuperCall]
        self, match: tuple[str, str, str, str, int]
    ) -> None:
        # We intentionally don't call super().__init__ because we need a different
        # tuple format that includes fence_char and fence_len
        self.lang = inline.Literal.strip_backslash(match[0])
        self.extra = match[1]
        self.children = [inline.RawText(match[2], False)]
        self.fence_char = match[3]
        self.fence_len = match[4]

    @override
    @classmethod
    def match(cls, source: Source) -> re.Match[str] | None:
        m = source.expect_re(cls.pattern)
        if not m:
            return None
        prefix, leading, info = m.groups()
        if leading[0] == "`" and "`" in info:
            return None
        lang, _, extra = partition_by_spaces(info)
        # Store extended info including fence_char and fence_len
        fence_char = leading[0]
        fence_len = len(leading)
        source.context.code_info = ExtendedParseInfo(
            prefix, leading, lang, extra, fence_char, fence_len
        )
        return m

    @override
    @classmethod
    def parse(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, source: Source
    ) -> tuple[str, str, str, str, int]:
        # We intentionally return a different tuple format than the parent class
        # to include fence_char and fence_len
        source.next_line()
        source.consume()
        lines: list[str] = []
        parse_info: ExtendedParseInfo = source.context.code_info
        while not source.exhausted:
            line = source.next_line()
            if line is None:  # pyright: ignore[reportUnnecessaryComparison]
                break
            source.consume()
            m = re.match(r" {,3}(~+|`+)[^\n\S]*$", line, flags=re.M)
            if m and parse_info.leading in m.group(1):
                break

            prefix_len = source.match_prefix(parse_info.prefix, line)
            if prefix_len >= 0:
                line = line[prefix_len:]
            else:
                line = line.lstrip()
            lines.append(line)
        return (
            parse_info.lang,
            parse_info.extra,
            "".join(lines),
            parse_info.fence_char,
            parse_info.fence_len,
        )


class CustomParser(Parser):
    def __init__(self) -> None:
        super().__init__()
        self.block_elements["HTMLBlock"] = CustomHTMLBlock
        self.block_elements["FencedCode"] = CustomFencedCode


class MarkdownNormalizer(Renderer):
    """
    Render Markdown in normalized form. This is the internal implementation
    which overrides most of `MarkdownRenderer`.

    You likely want to use `normalize_markdown()` instead.

    Based on:
    https://github.com/frostming/marko/blob/master/marko/md_renderer.py
    https://github.com/frostming/marko/blob/master/marko/ext/gfm/renderer.py
    """

    def __init__(self, line_wrapper: LineWrapper) -> None:
        super().__init__()
        self._prefix: str = ""  # The prefix on the first line, with a bullet, such as `  - `.
        self._second_prefix: str = ""  # The prefix on subsequent lines, such as `    `.
        self._suppress_item_break: bool = True
        self._line_wrapper: LineWrapper = line_wrapper
        self._skip_next_blank_line: bool = False  # Skip blank line following heading
        self._current_inline_text: str = ""  # Track accumulated inline text for escape context
        self._in_heading: bool = False  # Track if we're rendering a heading

    @override
    def __enter__(self) -> MarkdownNormalizer:
        self._prefix = ""
        self._second_prefix = ""
        return super().__enter__()

    @contextmanager
    def container(self, prefix: str, second_prefix: str = "") -> Generator[None, None, None]:
        old_prefix, old_second_prefix = self._prefix, self._second_prefix
        self._prefix += prefix
        self._second_prefix += second_prefix
        yield
        self._prefix, self._second_prefix = old_prefix, old_second_prefix

    def render_paragraph(self, element: block.Paragraph) -> str:
        # Reset the skip flag since we're not rendering a blank line
        self._skip_next_blank_line = False
        # After rendering a paragraph, don't suppress the next item break
        # This ensures proper spacing before list items that follow paragraphs
        self._suppress_item_break = False

        # Reset inline text tracking for this paragraph
        self._current_inline_text = ""
        children: Any = self.render_children(element)

        # GFM checkbox support.
        if hasattr(element, "checked"):
            children = f"[{'x' if element.checked else ' '}] {children}"  # pyright: ignore

        # Wrap the text.
        wrapped_text = self._line_wrapper(
            children,
            self._prefix,
            self._second_prefix,
        )
        self._prefix = self._second_prefix
        self._current_inline_text = ""
        return wrapped_text + "\n"

    def render_list(self, element: block.List) -> str:
        # Reset the skip flag since we're not rendering a blank line
        self._skip_next_blank_line = False

        result: list[str] = []

        for i, child in enumerate(element.children):
            # Configure the appropriate prefix based on list type
            if element.ordered:
                num = i + element.start
                prefix = f"{num}. "
                subsequent_indent = " " * (len(str(num)) + 2)
            else:
                prefix = f"{element.bullet} "
                subsequent_indent = "  "

            with self.container(prefix, subsequent_indent):
                rendered_item = self.render(child)
                result.append(rendered_item)

        self._prefix = self._second_prefix
        return "".join(result)

    def render_list_item(self, element: block.ListItem) -> str:
        result = ""
        # We want all list items to have two newlines between them.
        if self._suppress_item_break:
            self._suppress_item_break = False
        else:
            # Add the newline between paragraphs. Normally this would be an empty line but
            # within a quote block it would be the secondary prefix, like `> `.
            result += self._second_prefix.strip() + "\n"

        result += self.render_children(element)

        return result

    def render_quote(self, element: block.Quote) -> str:
        # Reset the skip flag since we're not rendering a blank line
        self._skip_next_blank_line = False

        with self.container("> ", "> "):
            result = self.render_children(element).rstrip("\n")
        self._prefix = self._second_prefix
        # After rendering a quote block, don't suppress the next item break
        # This ensures proper spacing after list items with quote blocks
        self._suppress_item_break = False
        return f"{result}\n"

    def _render_code(self, element: block.CodeBlock | block.FencedCode | CustomFencedCode) -> str:
        # Reset the skip flag since we're not rendering a blank line
        self._skip_next_blank_line = False

        # Preserve code content without reformatting.
        code_child = cast(inline.RawText, element.children[0])
        code_content = code_child.children.rstrip("\n")
        lang = element.lang if isinstance(element, block.FencedCode) else ""
        extra = element.extra if isinstance(element, block.FencedCode) else ""
        extra_text = f" {extra}" if extra else ""
        lang_text = f"{lang}{extra_text}" if lang else ""

        # Get fence character and length from CustomFencedCode, or use defaults
        if isinstance(element, CustomFencedCode):
            fence_char = element.fence_char
            original_fence_len = element.fence_len
        else:
            fence_char = "`"
            original_fence_len = 3

        # Calculate minimum fence length needed based on content
        # (must be longer than any fence-like sequences in the content)
        min_fence_len = _min_fence_length(code_content, fence_char)

        # Use the maximum of original and minimum fence lengths
        fence_len = max(original_fence_len, min_fence_len)
        fence = fence_char * fence_len

        lines = [f"{self._prefix}{fence}{lang_text}"]
        lines.extend(f"{self._second_prefix}{line}" for line in code_content.splitlines())
        lines.append(f"{self._second_prefix}{fence}")
        self._prefix = self._second_prefix
        # After rendering a code block, don't suppress the next item break
        # This ensures proper spacing after list items with code blocks
        self._suppress_item_break = False
        return "\n".join(lines) + "\n"

    def render_fenced_code(self, element: block.FencedCode) -> str:
        return self._render_code(element)

    def render_custom_fenced_code(self, element: CustomFencedCode) -> str:
        return self._render_code(element)

    def render_code_block(self, element: block.CodeBlock) -> str:
        # Convert indented code blocks to fenced code blocks.
        return self._render_code(element)

    def render_html_block(self, element: block.HTMLBlock) -> str:
        result = f"{self._prefix}{element.body}"
        self._prefix = self._second_prefix
        return result

    def render_thematic_break(self, _element: block.ThematicBreak) -> str:
        result = f"{self._prefix}* * *\n"
        self._prefix = self._second_prefix
        return result

    def render_heading(self, element: block.Heading) -> str:
        self._in_heading = True
        self._current_inline_text = ""
        children_content = self.render_children(element)
        self._in_heading = False
        self._current_inline_text = ""
        # If heading ends with hard break, don't add extra newline
        if children_content.endswith("\\"):
            result = f"{self._prefix}{'#' * element.level} {children_content}\n"
            self._prefix = self._second_prefix
            # Don't skip next blank line or suppress item break for hard breaks
            return result
        else:
            result = f"{self._prefix}{'#' * element.level} {children_content}\n\n"
            self._prefix = self._second_prefix
            # Skip the next blank line since we already added one
            self._skip_next_blank_line = True
            # Suppress the next item break since the heading already added spacing
            self._suppress_item_break = True
            return result

    def render_setext_heading(self, element: block.SetextHeading) -> str:
        return self.render_heading(cast(block.Heading, element))  # pyright: ignore

    def render_blank_line(self, _element: block.BlankLine) -> str:
        if self._skip_next_blank_line:
            self._skip_next_blank_line = False
            return ""
        if self._prefix.strip():
            result = f"{self._prefix}\n"
        else:
            result = "\n"
        self._suppress_item_break = True
        self._prefix = self._second_prefix
        return result

    def render_link_ref_def(self, element: block.LinkRefDef) -> str:
        """Render a standard link reference definition:
        [label]: url "title"
        """
        link_text = element.dest
        if element.title:
            link_text += f" {_normalize_title_quotes(element.title)}"
        result = f"{self._prefix}[{element.label}]: {link_text}\n"
        self._prefix = self._second_prefix
        self._suppress_item_break = True
        return result

    def render_emphasis(self, element: inline.Emphasis) -> str:
        return f"*{self.render_children(element)}*"

    def render_strong_emphasis(self, element: inline.StrongEmphasis) -> str:
        return f"**{self.render_children(element)}**"

    def render_inline_html(self, element: inline.InlineHTML) -> str:
        return cast(str, element.children)

    def render_link(self, element: inline.Link) -> str:
        link_text = self.render_children(element)
        link_title = _normalize_title_quotes(element.title) if element.title else None
        assert self.root_node
        label = next(
            (k for k, v in self.root_node.link_ref_defs.items() if v == (element.dest, link_title)),
            None,
        )
        if label is not None:
            if label == link_text:
                return f"[{label}]"
            return f"[{link_text}][{label}]"
        title = f" {link_title}" if link_title is not None else ""
        return f"[{link_text}]({element.dest}{title})"

    def render_auto_link(self, element: inline.AutoLink) -> str:
        return f"<{element.dest}>"

    def render_image(self, element: inline.Image) -> str:
        template = "![{}]({}{})"
        title = f" {_normalize_title_quotes(element.title)}" if element.title else ""
        return template.format(self.render_children(element), element.dest, title)

    def render_literal(self, element: inline.Literal) -> str:
        """
        Render escaped characters, only preserving the escape when necessary.

        Per CommonMark spec (https://spec.commonmark.org/0.31.2/#backslash-escapes):
        - Any ASCII punctuation character may be backslash-escaped
        - Escapes prevent the character from having its special Markdown meaning
        - See Example 14: "1\\. not a list" - escape needed to prevent list interpretation

        Our approach (smart escaping):
        - Periods: Only escape when needed to prevent list markers (e.g., "1\\." at line start)
          - Remove in headings: "## 1\\." → "## 1." (can't start list in heading)
          - Remove in middle of text: "text 1\\. more" → "text 1. more" (not at line start)
          - Keep at line start: "1\\. not a list" → "1\\. not a list" (prevents list)
        - Other characters (*, #, -, _, etc.): Always preserve escapes
          - These may have meaning in various contexts (emphasis, lists, etc.)
          - Conservative approach: keep escape unless we're certain it's unnecessary

        Related discussions:
        - cmark issue #131: https://github.com/commonmark/cmark/issues/131
          (discusses overly aggressive escaping in renderers)
        """
        # For Literal elements, children is always a string (the escaped character)
        char = cast(str, element.children)

        # Only handle period escapes - leave all other escapes as-is
        # Other punctuation escapes (*, #, -, _, etc.) may be needed for various syntax
        if char != ".":
            self._current_inline_text += f"\\{char}"
            return f"\\{char}"

        # For periods: remove escape in headings
        # Rationale: Can't start a list inside a heading, so period is never special syntax
        if self._in_heading:
            self._current_inline_text += char
            return char

        # For periods: check if this would form a list marker
        # CommonMark requires: 1-9 digits + "." + space to create ordered list
        # Need to escape if:
        # 1. We're at or near the start of a line
        # 2. The accumulated text is just digits (matches list marker pattern: "1.")
        stripped = self._current_inline_text.lstrip()
        if stripped and stripped.isdigit():
            # This is "1\." at line start - preserve escape to prevent list interpretation
            self._current_inline_text += f"\\{char}"
            return f"\\{char}"

        # For all other period cases, the escape is not needed
        self._current_inline_text += char
        return char

    def render_raw_text(self, element: inline.RawText) -> str:
        from marko.ext.pangu import PANGU_RE

        text = re.sub(PANGU_RE, " ", element.children)
        self._current_inline_text += text
        return text

    def render_line_break(self, element: inline.LineBreak) -> str:
        return "\n" if element.soft else "\\\n"

    def render_code_span(self, element: inline.CodeSpan) -> str:
        text = element.children
        if text and (text[0] == "`" or text[-1] == "`"):
            return f"`` {text} ``"
        return f"`{element.children}`"

    # --- GFM Renderer Methods ---

    def render_footnote_ref(self, element: footnote.FootnoteRef) -> str:
        """Render an inline footnote reference like [^label]."""
        return f"[^{element.label}]"

    def render_footnote_def(self, element: footnote.FootnoteDef) -> str:
        """
        Render a GFM footnote definition, handling content wrapping.
        Note multiline footnotes aren't very well specified but we use
        standard 4-space indentation. See:
        https://github.com/micromark/micromark-extension-gfm-footnote
        """
        # Render label and the rest within an indented container.
        label_part = f"[^{element.label}]: "
        with self.container(label_part, "    "):
            content = self.render_children(element)

        # Set up state for the *next* block element using the restored outer secondary prefix.
        self._prefix = self._second_prefix
        self._suppress_item_break = True  # This definition acts as a block separator.

        # Footnote defs should be separated by extra newlines.
        return content.rstrip("\n") + "\n\n"

    def render_strikethrough(self, element: gfm_elements.Strikethrough) -> str:
        return f"~~{self.render_children(element)}~~"

    def render_table(self, element: gfm_elements.Table) -> str:
        """
        Render a GFM table. Does not do whitespace padding and normalizes
        the delimiters to use three dashes consistently.
        """
        lines: list[str] = []
        head, *body = element.children
        lines.append(self.render(head))

        normalized_delimiters: list[str] = []
        for delimiter in element.delimiters:
            if delimiter.startswith(":") and delimiter.endswith(":"):
                # Center alignment
                normalized_delimiter = ":---:"
            elif delimiter.startswith(":"):
                # Left alignment
                normalized_delimiter = ":---"
            elif delimiter.endswith(":"):
                # Right alignment
                normalized_delimiter = "---:"
            else:
                # No alignment
                normalized_delimiter = "---"
            normalized_delimiters.append(normalized_delimiter)

        lines.append(f"| {' | '.join(normalized_delimiters)} |\n")
        for row in body:
            lines.append(self.render(row))
        return "".join(lines)

    def render_table_row(self, element: gfm_elements.TableRow) -> str:
        """Render a row within a GFM table."""
        return f"| {' | '.join(self.render(cell) for cell in element.children)} |\n"

    def render_table_cell(self, element: gfm_elements.TableCell) -> str:
        """Render a cell within a GFM table row."""
        return self.render_children(element).replace("|", "\\|")

    def render_url(self, element: gfm_elements.Url) -> str:
        """For GFM autolink URLs, just output the URL directly."""
        return element.dest


DEFAULT_SEMANTIC_LINE_WRAPPER = line_wrap_by_sentence(width=DEFAULT_WRAP_WIDTH, is_markdown=True)
"""
Default line wrapper for semantic line wrapping.
"""

DEFAULT_FIXED_LINE_WRAPPER = line_wrap_to_width(width=DEFAULT_WRAP_WIDTH, is_markdown=True)
"""
Default line wrapper for fixed-width line wrapping.
"""


def flowmark_markdown(line_wrapper: LineWrapper = DEFAULT_SEMANTIC_LINE_WRAPPER) -> Markdown:
    """
    Marko Markdown setup for GFM with a few customizations for Flowmark and a new
    renderer that normalizes Markdown according to Flowmark's conventions.
    """

    class CustomRenderer(MarkdownNormalizer):
        def __init__(self) -> None:
            super().__init__(line_wrapper)

    class FlowmarkMarkdown(Markdown):
        """
        Marko Markdown API with Flowmark customizations.
        """

        def __init__(self) -> None:  # pyright: ignore[reportMissingSuperCall]
            pass

        @override
        def _setup_extensions(self) -> None:
            # Using Marko's full extension system is tricky with our customizations so simpler
            # to do this manually.
            custom_parser = CustomParser()
            # Add GFM support.
            for e in GFM.elements:
                assert (
                    e not in custom_parser.block_elements and e not in custom_parser.inline_elements
                )
                custom_parser.add_element(e)
            # Add GFM footnote support.
            footnote_ext = footnote.make_extension()
            for e in footnote_ext.elements:
                assert (
                    e not in custom_parser.block_elements and e not in custom_parser.inline_elements
                )
                custom_parser.add_element(e)
            self.parser: Parser = custom_parser
            self.renderer: Renderer = CustomRenderer()

            self._setup_done: bool = True

    return FlowmarkMarkdown()
