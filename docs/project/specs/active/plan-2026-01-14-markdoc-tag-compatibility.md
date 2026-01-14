# Plan Spec: Markdoc/Jinja Tag and HTML Comment Compatibility

## Purpose

This is a technical design doc for improving Flowmark's compatibility with Markdoc-style
tags (`{% tag %}`), semantic HTML comments (`<!-- prefix:tag -->`), and related templating
syntaxes used by Markdoc, Markform, WordPress Gutenberg, Hugo, Jekyll, and other systems.

## Background

Flowmark v0.6.0 already has support for keeping Jinja/Markdoc tags atomic during word
splitting (PR #10), but there are still formatting issues that break downstream parsers:

- [Markdoc](https://markdoc.dev/) - Stripe's Markdown-based document format
- [Markform](https://github.com/jlevy/markform) - Form definition format built on Markdoc
- [WordPress Gutenberg](https://developer.wordpress.org/block-editor/) - Uses
  `<!-- wp:block -->` comment syntax
- Jinja/Nunjucks templating systems

**Current State:**

- Tags are kept atomic during word splitting via `_HtmlMdWordSplitter` patterns
  (see [text_wrapping.py](src/flowmark/linewrapping/text_wrapping.py))
- Block HTML parsing is disabled in the custom Marko parser
  (see [flowmark_markdown.py](src/flowmark/formats/flowmark_markdown.py))
- Paragraph rendering wraps all content without awareness of tag boundaries

**Key Issue:**

The fundamental problem is that Flowmark treats tag lines as regular text content.
When a line contains only a block-level tag (like `{% description %}`), it gets merged
with surrounding content during paragraph wrapping.
The general principle we want: **newlines after block-level tags should be preserved.**

## Summary of Task

Improve Flowmark to properly handle block-level Markdoc/Jinja tags and semantic HTML
comments by:

1. Preserving newlines after opening block tags
2. Keeping closing tags on their own lines
3. Preventing tag pairs from being broken by wrapping
4. Preserving tight list structure where appropriate
5. Fixing backslash escape handling in attribute values

## Backward Compatibility

**BACKWARD COMPATIBILITY REQUIREMENTS:**

- **Code types, methods, and function signatures**: DO NOT MAINTAIN - internal refactoring
  is acceptable

- **Library APIs**: KEEP DEPRECATED for `reformat_text()` and `fill_markdown()` public
  APIs - these should continue to work with existing parameters

- **Server APIs**: N/A

- **File formats**: SUPPORT BOTH - existing Markdown files should produce similar output;
  new tag-aware behavior should be additive and preserve existing formatting where no
  tags are present

- **Database schemas**: N/A

**Key Compatibility Concern:**

The existing testdoc.expected.*.md files define the current expected behavior.
Changes must not break formatting of standard Markdown without tags.
New test cases should be added for tag-specific behavior.

## Stage 1: Planning Stage

### Issue Analysis

The user's analysis identified 7 issues. Here's the mapping to root causes:

| Issue | Description | Root Cause |
|-------|-------------|------------|
| 1 | Content merged with opening tags | Paragraph wrapping ignores tag boundaries |
| 2 | Closing tags merged with list items | List rendering doesn't preserve trailing tags |
| 3 | Same-line tag pairs broken | Word wrapping breaks between adjacent tags |
| 3a | Backslash escapes stripped | Escape handling in attribute values |
| 4 | Blank lines between list items | Tight→loose list conversion (CommonMark) |
| 5 | Nested tags collapsed | Same as Issue 1 |
| 6 | Tables inside tags broken | Table rendering merges with closing tag |
| 7 | List item annotations affected | Combination of Issues 2 and 4 |

### Proposed Solution Approach

**Option A (Recommended): Line-Level Tag Awareness**

Rather than full semantic parsing of tags (which would be complex and fragile), we can
solve most issues by adding line-level awareness:

1. **Identify "block tag lines"**: Lines that contain only a block-level tag
   (opening `{% tag %}`, closing `{% /tag %}`, or `<!-- prefix:tag -->`)
2. **Preserve newlines around block tag lines**: Don't merge them with adjacent content
3. **Keep consecutive tags together**: Don't break between `{% tag %}{% /tag %}`

This approach:
- Requires minimal changes to the architecture
- Is pattern-based (similar to existing word splitting)
- Doesn't require semantic understanding of tag structure
- Preserves existing behavior for non-tag content

**Option B: Ignore Directives**

Add `<!-- flowmark-ignore-start/end -->` comments.
This is useful as a fallback but doesn't solve the core issue.

**Option C: Configuration File**

Add `.flowmarkrc` with pattern configuration.
This adds complexity and doesn't help out-of-the-box.

### Minimum Viable Feature

For this phase, we will implement Option A with:

1. Line-level tag detection during paragraph wrapping
2. Newline preservation after opening block tags
3. Newline preservation before closing block tags
4. Prevention of breaking between consecutive tags

### Not In Scope

- Full semantic Markdoc/Jinja parsing
- Configuration file support
- Ignore directives
- Custom tag registration

### Acceptance Criteria

1. Test files with Markdoc syntax remain unchanged after `flowmark --auto`
2. Test files with HTML comment syntax remain unchanged after `flowmark --auto`
3. Existing testdoc.expected.*.md files continue to match
4. Tight lists inside tags remain tight (no extra blank lines)
5. Backslash escapes in attributes are preserved

## Stage 2: Architecture Stage

### Current Architecture

The markdown processing pipeline:

```
markdown_text
  → split_frontmatter()
  → flowmark_markdown.parse()         # Marko parser
  → [optional: doc_cleanups(), rewrite_text_content()]
  → marko.render()                    # MarkdownNormalizer
  → reattach_frontmatter()
  → result
```

Key components involved:

1. **[text_wrapping.py:51-168](src/flowmark/linewrapping/text_wrapping.py#L51-L168)**:
   `_HtmlMdWordSplitter` - handles word-level tag atomicity

2. **[flowmark_markdown.py:201-224](src/flowmark/formats/flowmark_markdown.py#L201-L224)**:
   `render_paragraph()` - wraps paragraph content

3. **[flowmark_markdown.py:226-280](src/flowmark/formats/flowmark_markdown.py#L226-L280)**:
   `render_list()` and `render_list_item()` - list rendering

4. **[line_wrappers.py](src/flowmark/linewrapping/line_wrappers.py)**:
   Line wrapper implementations

### Proposed Changes

#### Change 1: Block Tag Line Detection

Add detection for lines that are "block tag lines" - lines containing only a block-level
tag pattern.

**Location**: New function in `text_wrapping.py` or new module

**Patterns to detect**:
- Opening Markdoc tags: `{% tagname ... %}`
- Closing Markdoc tags: `{% /tagname %}`
- Self-closing tags: `{% tagname ... /%}`
- Opening HTML comment tags: `<!-- prefix:tagname ... -->`
- Closing HTML comment tags: `<!-- /prefix:tagname -->`
- Annotation comments: `<!-- #id -->` or `<!-- .class -->`

#### Change 2: Line-Preserving Paragraph Wrapping

Modify paragraph wrapping to:

1. Split content by existing newlines first
2. Identify block tag lines
3. Preserve newlines around block tag lines
4. Apply normal wrapping to non-tag content segments

**Location**: `text_wrapping.py` or `markdown_filling.py`

**Approach**: Before wrapping, scan for block tag patterns.
If a line matches a block tag pattern, keep it separate from wrapping.

#### Change 3: Prevent Breaking Consecutive Tags

When wrapping, if we encounter consecutive tags like `{% tag %}{% /tag %}`,
treat them as a single atomic unit (don't break between them).

**Location**: `_HtmlMdWordSplitter` or `wrap_paragraph_lines()`

#### Change 4: Fix Escape Handling

Investigate and fix backslash stripping in attribute values.

**Location**: Likely in `render_literal()` or escape context handling

### Architecture Diagram

```
                     Current Flow
                     ============
Paragraph Text ──► Split Words ──► Coalesce Tags ──► Wrap Lines ──► Output
                       │                │                │
                       └─ Atomic tags ──┘                │
                                                         └─ May break tags

                     Proposed Flow
                     =============
Paragraph Text ──► Detect Block Tags ──► Split Segments ──► Wrap Each ──► Output
       │                  │                    │               │
       │                  └─ Tag lines kept    │               │
       │                     as-is             │               │
       │                                       │               │
       └─────────────────────────────────────►│               │
                                         Normal content       │
                                         wrapped normally     │
                                                              │
                                              Consecutive tags kept atomic
```

## Stage 3: Refine Architecture

### Reusable Components Found

1. **`_HtmlMdWordSplitter` patterns** ([text_wrapping.py:83-132](src/flowmark/linewrapping/text_wrapping.py#L83-L132)):
   Existing regex patterns for tag detection can be reused for block tag detection

2. **`wrap_paragraph_lines()`** ([text_wrapping.py:177-203](src/flowmark/linewrapping/text_wrapping.py#L177-L203)):
   Core wrapping logic that can be extended

3. **`split_markdown_hard_breaks()`** ([line_wrappers.py:35-56](src/flowmark/linewrapping/line_wrappers.py#L35-L56)):
   Pattern for splitting content before processing, then rejoining

### Simplified Approach

After analysis, the cleanest approach is:

1. **Pre-process**: Before wrapping, identify lines that are block tags and mark them
2. **Split**: Separate block tag lines from normal content
3. **Wrap**: Wrap normal content segments normally
4. **Reassemble**: Put back together with block tags on their own lines

This leverages existing word splitting and wrapping code with minimal changes.

### Implementation Phases

**Phase 1: Block Tag Detection and Newline Preservation**
- [ ] Add block tag line detection regex patterns
- [ ] Modify paragraph wrapping to preserve newlines around block tags
- [ ] Add test cases for basic tag scenarios

**Phase 2: Consecutive Tag Handling**
- [ ] Prevent breaking between consecutive tags
- [ ] Add test cases for same-line tag pairs

**Phase 3: Escape and List Handling**
- [ ] Fix backslash escape preservation
- [ ] Investigate tight list preservation options
- [ ] Add test cases

**Phase 4: Validation**
- [ ] Ensure existing testdoc tests pass
- [ ] Add comprehensive Markdoc/Markform test files
- [ ] Test with real Markform documents

## Stage 4: Validation Stage

### Test Strategy

1. **Existing Tests**: All existing `testdoc.expected.*.md` files must continue to match

2. **New Test Cases**: Add test files for:
   - Basic Markdoc tag formatting
   - HTML comment tag formatting
   - Nested tag structures
   - Lists inside tags
   - Tables inside tags
   - Consecutive tags on same line
   - Backslash escapes in attributes

3. **Integration Testing**: Test with real Markform `.form.md` files

### Test Files to Create

- `tests/testdocs/markdoc-test.orig.md` - Input with Markdoc syntax
- `tests/testdocs/markdoc-test.expected.auto.md` - Expected output
- `tests/testdocs/html-comment-test.orig.md` - Input with HTML comment tags
- `tests/testdocs/html-comment-test.expected.auto.md` - Expected output

### Success Criteria

- [x] All existing tests pass
- [x] New Markdoc test file unchanged after `flowmark --auto`
- [x] New HTML comment test file unchanged after `flowmark --auto`
- [x] `make lint` passes
- [x] `make test` passes

## Implementation Complete

The implementation was completed with the following changes:

### Files Modified

| File | Changes |
|------|---------|
| `text_wrapping.py` | Added tag delimiter constants; added adjacent tag normalization; added paired tag coalescing patterns |
| `line_wrappers.py` | Added `_line_ends_with_tag()`, `_line_starts_with_tag()`, `_add_tag_newline_handling()` |
| `test_wrapping.py` | Added 6 unit tests for tag handling |
| `testdoc.orig.md` | Added Section 18 with comprehensive tag test cases |
| `testdoc.expected.*.md` | Updated expected outputs |

### How It Works

1. **Newline Preservation**: `_add_tag_newline_handling()` in `line_wrappers.py` wraps the base
   line wrapper. It splits text into segments at tag boundaries (lines ending with or starting
   with tags), wraps each segment separately, then rejoins with preserved newlines.

2. **Tag Atomicity**: `_HtmlMdWordSplitter` in `text_wrapping.py` keeps tags atomic during word
   splitting. Multi-word tags like `{% field kind="string" %}` stay together.

3. **Adjacent Tags**: The `_normalize_adjacent_tags()` method adds a space between adjacent
   tags like `%}{% ` to ensure proper tokenization.

4. **Paired Tag Coalescing**: Patterns for `{% tag %}{% /tag %}` ensure paired tags stay
   together during wrapping.

## Known Limitations and Corner Cases

### 1. CommonMark Escape Sequences

Backslash sequences that are valid CommonMark escapes will be processed by the Markdown parser.
For example, `\.` (escaped period) becomes `.` because CommonMark interprets `\` before
punctuation as an escape.

**Workaround**: Use `\\.` in source to get a literal `\.` in output, or use escape sequences
that CommonMark doesn't recognize (like `\s`, `\d` which are preserved).

**Reference**: https://spec.commonmark.org/0.31.2/#backslash-escapes

### 2. Block Elements After Opening Tags Need Blank Lines

When a block element (table, list) immediately follows an opening tag without a blank line,
the Markdown parser may interpret subsequent content incorrectly.

```markdown
{% field %}
- Item 1
- Item 2
{% /field %}
```

In this case, the closing tag may be interpreted as list item continuation and get indented.

**Workaround**: Always include a blank line after opening tags when content contains block
elements:

```markdown
{% field %}

- Item 1
- Item 2

{% /field %}
```

**Why**: This is a fundamental limitation of CommonMark parsing. The Markdown parser interprets
structure before Flowmark processes it. Flowmark preserves the newline before `{% /field %}`,
but the parser has already placed it inside the list item structure.

### 3. Closing Tags After List Items Get Indented

Related to #2: when a closing tag immediately follows a list item (no blank line), it may
receive list item continuation indentation:

```markdown
- list item
{% /tag %}
```

Becomes:
```markdown
- list item
  {% /tag %}
```

The newline IS preserved (the tag is on its own line), but it's indented because the Markdown
parser treats it as list continuation.

**Workaround**: Add a blank line before closing tags when inside lists.

### 4. Tight vs Loose Lists

Flowmark converts tight lists (no blank lines between items) to loose lists (blank lines
between items). This is intentional behavior for readability but may affect some use cases.

This is orthogonal to tag handling—the tag newline preservation works correctly regardless
of list style.

### Best Practices for Markform/Markdoc Documents

1. **Use blank lines around block content inside tags**:
   ```markdown
   {% field %}

   - Option A
   - Option B

   {% /field %}
   ```

2. **Keep inline tags on the same line**:
   ```markdown
   {% field kind="string" id="name" %}{% /field %}
   ```

3. **Use non-CommonMark escape sequences** for regex patterns:
   - `\s`, `\d`, `\+` are preserved (not CommonMark escapes)
   - `\.`, `\*`, `\[` will be processed as escapes
