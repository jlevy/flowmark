# Bugfix Spec: Smart Quoting Not Applied in Tables, Blockquote Inline Spans

## Purpose

Fix smart quote conversion so it works correctly inside all container types (tables,
strikethrough) and when quotes span across inline elements (code spans, emphasis, strong
emphasis, links) within a paragraph or other inline scope.

## Background

The `flowmark` smart quoting feature converts straight ASCII quotes (`"`, `'`) to
typographic/oriented quotes (\u201c \u201d, \u2018 \u2019) and apostrophes (\u2019).
This is implemented via AST tree traversal in `doc_transforms.py`, which walks through
`ContainerElement` types and applies `smart_quotes()` to each `RawText` node
independently.

Two issues have been identified where smart quotes fail to convert when expected.

## Bug Template

1. **In what scenarios does this bug apply?**

   - Quotes inside GFM table cells are never converted
   - Quotes inside strikethrough text are never converted
   - Quotes that span across inline elements (e.g., opening `"` before a code span and
     closing `"` after it) within any container type are not converted

2. **What is the current behavior?**

   - Table cell text: `| "Hello" |` stays as straight quotes
   - Strikethrough text: `~~"Hello"~~` stays as straight quotes
   - Cross-inline quotes in blockquotes:
     `> "First, ... \`command\`."` stays as straight quotes because the opening and
     closing `"` are in different `RawText` nodes (separated by the `CodeSpan`)

3. **What is the desired behavior?**

   - Table cell text: `| "Hello" |` \u2192 `| \u201cHello\u201d |`
   - Strikethrough text: `~~"Hello"~~` \u2192 `~~\u201cHello\u201d~~`
   - Cross-inline quotes: `> "First, ... \`command\`."` \u2192
     `> \u201cFirst, ... \`command\`.\u201d`
   - Code spans, fenced code, and other code content must NEVER be modified
   - Template tag content must NEVER be modified

4. **Is it reproducible?**

   Yes. Minimal reproductions:

   ```python
   # Issue 1: Tables
   fill_markdown('| "Hello" |\n| --- |\n', smartquotes=True)
   # Returns: '| "Hello" |\n| --- |\n'  (unchanged - BUG)
   # Expected: '| \u201cHello\u201d |\n| --- |\n'

   # Issue 2: Cross-inline quotes
   fill_markdown('**Bold:** "Start `code` end."\n', smartquotes=True)
   # Returns: '**Bold:** "Start `code` end."\n'  (unchanged - BUG)
   # Expected: '**Bold:** \u201cStart `code` end.\u201d\n'
   ```

5. **Could this bug appear in other situations?**

   Yes. Any inline element (emphasis, strong emphasis, links, images, strikethrough)
   that interrupts a quoted span would trigger issue 2. Issue 1 also affects
   strikethrough content.

6. **Should this be a complete, more systematic fix or a faster, lower-risk patch?**

   Complete systematic fix. The root cause is architectural:
   - Issue 1: `ContainerElement` tuple missing table/strikethrough types
   - Issue 2: Smart quotes applied per-`RawText`-node instead of per-inline-scope

7. **Should we make a deployment plan?**

   No special deployment needed. Standard release.

## Stage 1: Root Cause Analysis

### Issue 1: Missing Container Types

`ContainerElement` in `doc_transforms.py:10-21` does not include:
- `gfm_elements.Table`
- `gfm_elements.TableRow`
- `gfm_elements.TableCell`
- `gfm_elements.Strikethrough`

The `transform_tree()` function only recurses into `ContainerElement` types. Since
tables and strikethrough are not listed, their children are never visited, and `RawText`
nodes inside them are never processed.

### Issue 2: Per-Node Processing

`rewrite_text_content()` in `doc_transforms.py:97-125` applies the rewrite function to
each `RawText` node independently. When quotes span across inline elements (e.g.,
`"text \`code\` more text."`), the opening and closing `"` are in different `RawText`
nodes. The `QUOTE_PATTERN` regex in `smartquotes.py` needs to see both quotes in the
same string to match them as a pair.

## Stage 2: Fix Design

### Approach

1. **Add missing types to `ContainerElement`**: Add `gfm_elements.Table`,
   `gfm_elements.TableRow`, `gfm_elements.TableCell`, and `gfm_elements.Strikethrough`
   so the tree walker visits their children.

2. **Cross-inline rewriting**: Create a new function `rewrite_text_across_inlines()` that:
   a. Walks the tree looking for "inline scope" nodes (Paragraph, Heading, TableCell)
   b. For each scope, collects all inline content into segments, tracking which are
      from `RawText` nodes (mutable) vs other nodes (immutable context)
   c. Concatenates all segments into a composite string
   d. Applies `smart_quotes()` to the composite string
   e. Maps changes back only to `RawText` segments (since smart quotes is
      length-preserving, this is a simple positional mapping)

3. **Key invariant**: `smart_quotes()` is length-preserving (each ASCII quote character
   maps to exactly one Unicode character), so the positional mapping from composite text
   back to individual `RawText` nodes is exact.

### Safety Guarantees

- `CodeSpan` content is collected for context but marked immutable \u2014 never modified
- `FencedCode`/`CodeBlock` are not traversed at all (not in `ContainerElement`)
- Template tags are protected by `smart_quotes()` itself (splits on `TEMPLATE_TAG_PATTERN`)
- Code-like patterns (`x="foo"`) aren't matched by `QUOTE_PATTERN` (no whitespace before quote)

### Files to Modify

- `src/flowmark/transforms/doc_transforms.py` \u2014 Add container types, add cross-inline
  rewriting function
- `src/flowmark/linewrapping/markdown_filling.py` \u2014 Use new function for smart quotes
- `tests/test_smartquotes.py` \u2014 Add unit tests for new scenarios
- `tests/testdocs/testdoc.orig.md` \u2014 Add table/cross-inline test cases
- `tests/testdocs/testdoc.expected.auto.md` \u2014 Add expected smart-quoted output

## Stage 3: Implementation (TDD)

### Phase 1: Add Container Types + Cross-Inline Rewriting

- [x] Write failing tests for table smart quoting
- [x] Write failing tests for strikethrough smart quoting
- [x] Write failing tests for cross-inline quote spanning
- [x] Add missing types to `ContainerElement`
- [x] Implement `_collect_inline_segments()` helper
- [x] Implement `rewrite_text_across_inlines()` function
- [x] Update `fill_markdown()` to use new function for smart quotes
- [x] Verify all tests pass (202/202)
- [x] Update reference test documents

### Status

**Complete.** All tasks done, all 202 tests passing.

### Open Questions

- None

## Assumptions

- Smart quotes conversion is always length-preserving (verified by code inspection)
- `SetextHeading` is converted to `Heading` during parsing and doesn't need separate
  handling in `InlineScope`
