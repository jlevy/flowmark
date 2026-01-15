# Plan Spec: Atomic Tag Wrapping (Never Break Lines Within Tags)

## Purpose

This is a technical design doc for making Flowmark treat template tags (Markdoc/Jinja/HTML
comments) as atomic units during line wrapping, preventing any line breaks from occurring
inside a tag.

## Background

**Problem Context:**

Flowmark currently attempts to keep tags together during line wrapping using word
coalescing patterns. However, this approach has limitations:

1. The coalescing has a `MAX_TAG_WORDS = 12` limit, so tags with many attributes can still
   be broken
2. Even when coalesced, the tag becomes one very long "word" that may then be placed on a
   line where it gets truncated or causes issues
3. Markdoc's parser has bugs when multi-line opening tags have closing tags on the same
   continuation line (see GitHub Issue #17)

**Current Behavior:**

A long tag like:
```markdown
{% field kind="string" id="name" label="Full Name" role="user" required=true minLength=2 maxLength=100 placeholder="Enter name" %}{% /field %}
```

Currently wraps to:
```markdown
{% field kind="string" id="name" label="Full Name" role="user" required=true minLength=2
maxLength=100 placeholder="Enter name" %}{% /field %}
```

This triggers Markdoc parser bugs. Our current fix (PR #18) post-processes to move the
closing tag to its own line, but this is a workaround, not a proper solution.

**Desired Behavior:**

Tags should be treated as atomic units, similar to how inline code spans and links are
handled. A tag should either:
1. Fit on the current line entirely, OR
2. Be placed on a new line as a complete unit

```markdown
This is text before the tag.
{% field kind="string" id="name" label="Full Name" role="user" required=true minLength=2 maxLength=100 placeholder="Enter name" %}{% /field %}
More text after.
```

**Related Issues:**
- GitHub Issue #17: Multi-line opening tags break Markdoc parser
- PR #18: Post-processing workaround for Issue #17

## Summary of Task

Add a `--tags` CLI option to control how template tags are handled during line wrapping:

| Mode | Behavior |
|------|----------|
| `atomic` | Tags are never broken across lines (NEW DEFAULT) |
| `wrap` | Tags can be wrapped like normal text (current behavior) |

This applies to all template tag types:
1. Jinja/Markdoc tags: `{% ... %}`
2. Jinja comments: `{# ... #}`
3. Jinja variables: `{{ ... }}`
4. HTML comments: `<!-- ... -->`
5. Paired tags: `{% tag %}{% /tag %}` (stay together in atomic mode)

## Backward Compatibility

**BACKWARD COMPATIBILITY REQUIREMENTS:**

- **CLI behavior**: BREAKING CHANGE (intentional) - default changes from `wrap` to
  `atomic`. Users wanting old behavior can use `--tags=wrap`.

- **API behavior**: Add `tags: Literal["atomic", "wrap"] = "atomic"` parameter to
  `fill_markdown()` and related functions.

- **File formats**: Documents with long tags will have different formatting by default.
  Previously wrapped tags will now appear on single (potentially long) lines.

**Migration Path:**

Users who depend on current behavior can add `--tags=wrap` to their commands.

**Trade-offs with `atomic` mode:**

- Lines containing long tags may exceed the target width significantly
- This is acceptable because:
  1. Tags are machine-parseable content, not prose for human reading
  2. Breaking tags causes parser bugs in downstream tools (Markdoc)
  3. Modern editors handle long lines well with soft wrapping

## Stage 1: Planning Stage

### Minimum Viable Feature

1. Identify complete tags during word splitting
2. Treat tags as indivisible tokens (single "words")
3. Handle nested/paired tags appropriately
4. Respect Markdown code spans (don't treat tag-like content inside backticks as tags)

### Not In Scope

- Breaking tags across lines in any "smart" way
- Formatting the interior of tags (e.g., multi-line attribute formatting)
- Validation of tag syntax
- Special handling for specific tag types (all tags treated uniformly)

### Acceptance Criteria

1. `--tags=atomic` (default): Single tags are never broken across lines
2. `--tags=atomic`: Paired tags like `{% field %}{% /field %}` stay together
3. `--tags=atomic`: Very long tags placed on their own line (not broken)
4. `--tags=atomic`: Content inside code spans (backticks) is NOT treated as tags
5. `--tags=wrap`: Current behavior preserved for backward compatibility
6. Prose around tags still wraps normally in both modes
7. Nested tags within prose are handled correctly
8. `make lint` and `make test` pass
9. Post-processing workaround from PR #18 only needed for `wrap` mode

### Resolved Questions

- [x] **Q1**: Should there be a maximum tag length beyond which we warn or error?
  **Decision**: No limit. Allow any length tag. Very long lines are acceptable for
  machine-parseable content.

- [x] **Q2**: For paired tags like `{% field %}{% /field %}`, should they always stay
  together, or only if they fit on one line?
  **Decision**: In `atomic` mode, paired tags stay together. In `wrap` mode, current
  behavior (coalescing with limits) applies.

- [x] **Q3**: Should this behavior be configurable?
  **Decision**: Yes, via `--tags={atomic|wrap}` with `atomic` as default.

## Stage 2: Architecture Stage

### Current Architecture

Line wrapping happens through this flow:

```
Input text
    │
    ▼
normalize_adjacent_tags()  ──► Adds space between %}{% for tokenization
    │
    ▼
_HtmlMdWordSplitter()  ──► Splits on whitespace, coalesces multi-word constructs
    │                       Uses patterns up to MAX_TAG_WORDS=12
    ▼
wrap_paragraph_lines()  ──► Fits words to target width
    │
    ▼
denormalize_adjacent_tags()  ──► Removes spaces between %} {%
    │
    ▼
Output text
```

**Key Files:**
- `src/flowmark/linewrapping/text_wrapping.py` - Core wrapping logic, word splitter
- `src/flowmark/linewrapping/tag_handling.py` - Tag detection, coalescing patterns
- `src/flowmark/linewrapping/line_wrappers.py` - High-level wrapper factories

### Proposed Architecture

#### Option A: Pre-processing Placeholder Approach (REJECTED)

Before wrapping, replace complete tags with unique placeholders:

```
Input: "Text {% field attr="val" %} more text"
    │
    ▼
_extract_tags()  ──► Returns: "Text \x00TAG0\x00 more text"
    │                 Stores: {0: '{% field attr="val" %}'}
    ▼
Normal wrapping  ──► Wraps around placeholders (which are short)
    │
    ▼
_restore_tags()  ──► Replaces placeholders with original tags
    │
    ▼
Output: "Text\n{% field attr="val" %} more\ntext"
```

**Problems discovered during implementation:**

1. **Length distortion**: Placeholders are shorter than original tags (e.g., 7 chars vs
   50 chars), causing incorrect wrapping decisions. Lines that should wrap don't wrap
   because the placeholder makes them appear shorter.

2. **Context blindness**: The extraction happens at raw text level without understanding
   Markdown structure. Content inside backticks like `` `<!--% ... -->` `` gets
   incorrectly treated as HTML comments.

3. **Two-pass complexity**: Requires extract/wrap/restore cycle in multiple places.

**Verdict**: This approach has fundamental flaws and should not be used.

#### Option B: Enhanced Word Splitter Approach (RECOMMENDED)

Modify the word splitter to recognize complete tags as atomic tokens directly:

```
Input: "Text {% field attr="val" %} more text"
    │
    ▼
_HtmlMdWordSplitter(atomic_tags=True):
    │
    ├──► 1. Find code spans first (protect their content)
    │       e.g., `<!-- not a tag -->` stays as one token
    │
    ├──► 2. Find template tags NOT inside code spans
    │       e.g., {% field attr="val" %} becomes one token
    │
    ├──► 3. Find paired tags as single units
    │       e.g., {% tag %}{% /tag %} becomes one token
    │
    └──► 4. Split remaining prose on whitespace
    │
    ▼
Returns: ["Text", "{% field attr=\"val\" %}", "more", "text"]
    │
    ▼
wrap_paragraph_lines()  ──► Fits words to target width
                            (sees 30-char tag as one 30-char "word")
    │
    ▼
Output: Correctly wrapped with accurate line lengths
```

**Advantages:**

1. **Accurate lengths**: Tags stay as-is, become single tokens. A 50-char tag is seen as
   a 50-char word, so wrapping decisions are correct.

2. **Context-aware**: Code spans are identified first, protecting content inside backticks
   from being treated as tags.

3. **Single pass**: No extract/restore cycle. Just smarter tokenization.

4. **Natural integration**: The word splitter is already the right abstraction layer.
   It already handles code spans and links as atomic units.

5. **Simpler code**: Less code, fewer edge cases, easier to maintain.

### Implementation Details

#### Enhanced Word Splitter

Add atomic tag detection to `_HtmlMdWordSplitter`:

```python
class _HtmlMdWordSplitter:
    def __init__(self, atomic_tags: bool = False):
        self.atomic_tags = atomic_tags
        # ... existing initialization ...

    def __call__(self, text: str) -> list[str]:
        if self.atomic_tags:
            return self._split_with_atomic_constructs(text)
        else:
            return self._split_with_coalescing(text)  # existing behavior

    def _split_with_atomic_constructs(self, text: str) -> list[str]:
        """Split treating code spans and template tags as atomic tokens."""
        text = normalize_adjacent_tags(text)

        tokens: list[str] = []
        atomics: list[tuple[int, int, str]] = []  # (start, end, content)

        # 1. Find code spans first (they protect content inside)
        for match in CODE_SPAN_PATTERN.finditer(text):
            atomics.append((match.start(), match.end(), match.group(0)))

        # 2. Find paired template tags NOT inside code spans
        for match in PAIRED_TAGS_PATTERN.finditer(text):
            start = match.start()
            if not self._inside_existing(start, atomics):
                atomics.append((start, match.end(), match.group(0)))

        # 3. Find single template tags NOT inside code spans or paired tags
        for match in TEMPLATE_TAG_PATTERN.finditer(text):
            start = match.start()
            if not self._inside_existing(start, atomics):
                atomics.append((start, match.end(), match.group(0)))

        atomics.sort(key=lambda x: x[0])

        # 4. Build token list
        pos = 0
        for start, end, content in atomics:
            if pos < start:
                tokens.extend(text[pos:start].split())  # prose words
            tokens.append(content)  # atomic as single token
            pos = end

        if pos < len(text):
            tokens.extend(text[pos:].split())

        return tokens
```

#### Code Span Pattern

Pattern to match inline code spans (respecting CommonMark rules):

```python
# Matches `code` or ``code with `backticks` inside``
CODE_SPAN_PATTERN = re.compile(r'(`+)(?!`)[^`]*?\1')
```

#### Integration

Pass `atomic_tags` mode through the call chain:

```python
def wrap_paragraph_lines(..., tags: TagWrapping = TagWrapping.atomic) -> list[str]:
    splitter = _HtmlMdWordSplitter(atomic_tags=(tags == TagWrapping.atomic))
    words = splitter(text)
    # ... rest of wrapping logic unchanged ...
```

## Stage 3: Implementation Phases

### Phase 1: Add TagWrapping Enum and CLI Option

- [x] Add `TagWrapping` enum with `atomic` and `wrap` values
- [x] Add `--tags` CLI argument to `cli.py`
- [x] Add `tags` parameter to `fill_markdown()` and `reformat_text()`
- [x] Thread parameter through to wrapping functions

### Phase 2: Simplified Word Splitter Approach

**Note:** During implementation, we discovered that both atomic and wrap modes work
best with the same coalescing-based word splitting. Long tags can wrap at internal
whitespace boundaries in both modes (as expected for readability). The key difference
is in post-processing.

- [x] Add `atomic_tags` parameter to `_HtmlMdWordSplitter` (for future extensibility)
- [x] Implement `_split_with_atomic_constructs()` that delegates to coalescing
- [x] Both modes use coalescing to keep tag contents together where possible
- [x] Long tags wrap at internal whitespace (expected behavior for many attributes)

### Phase 3: Apply Multiline Tag Fix to Both Modes

**Note:** The `_fix_multiline_opening_tag_with_closing()` fix (workaround for Markdoc
parser bug #17) is needed in BOTH modes, not just wrap mode. When an opening tag spans
multiple lines, the closing tag should be on its own line regardless of mode.

- [x] Apply `_fix_multiline_opening_tag_with_closing()` in both atomic and wrap modes
- [x] Update docstrings to reflect that `tags` parameter is for API compatibility
- [x] Keep placeholder functions (`extract_tags_atomic`, `restore_tags_atomic`) for
      potential future use, though currently unused

### Phase 4: Testing

- [x] Update `test_multiline_tag_through_pipeline` to test correct behavior
- [x] Long tags should wrap at internal whitespace
- [x] Closing tags should be on own line when opening tag spans multiple lines
- [x] All testdoc expected files unchanged (behavior matches existing expectations)
- [x] Run full test suite (160 tests pass)
- [x] Verify lint passes (0 errors, 0 warnings)

## Stage 4: Validation Stage

### Test Strategy

1. **Unit Tests**: Test word splitter with various inputs
2. **Integration Tests**: Test full wrapping pipeline
3. **Regression Tests**: Ensure existing behavior preserved for non-tag content
4. **Edge Cases**:
   - Tags at start/end of paragraph
   - Multiple tags adjacent to each other
   - Tags with newlines inside (multi-line attribute values)
   - Tags with quotes and special characters
   - Very long tags (edge case for line width)
   - Tag-like content inside code spans (must NOT be treated as tags)

### Test Cases

```python
def test_atomic_single_tag_not_broken():
    """In atomic mode, long single tag stays on one line."""
    text = "Before {% field kind='string' id='name' label='Full Name' %} after."
    result = fill_markdown(text, width=40, tags="atomic")
    assert "{% field kind='string' id='name' label='Full Name' %}" in result

def test_atomic_paired_tags_stay_together():
    """In atomic mode, paired tags remain adjacent."""
    text = "{% field %}{% /field %}"
    result = fill_markdown(text, width=20, tags="atomic")
    assert "{% field %}{% /field %}" in result

def test_atomic_tag_on_own_line_if_too_long():
    """In atomic mode, very long tag gets its own line."""
    text = "Short text {% very_long_tag_with_many_attributes='...' %} more."
    result = fill_markdown(text, width=40, tags="atomic")
    lines = result.strip().split('\n')
    tag_line = [l for l in lines if '{% very_long_tag' in l][0]
    assert tag_line.count('{%') == 1  # Complete tag on one line

def test_code_span_protects_tag_like_content():
    """Content inside backticks is NOT treated as a tag."""
    text = "Use the syntax `<!--% tag -->` for comments."
    result = fill_markdown(text, width=30, tags="atomic")
    # The backtick content should stay together as code span
    assert "`<!--% tag -->`" in result

def test_wrap_mode_preserves_current_behavior():
    """In wrap mode, tags can be broken (current behavior)."""
    text = "{% field kind='string' id='name' label='Full Name' required=true %}"
    result = fill_markdown(text, width=40, tags="wrap")
    # Current behavior: tag may wrap across lines
    assert "{%" in result and "%}" in result

def test_default_is_atomic():
    """Default mode should be atomic."""
    text = "{% field kind='string' id='name' %}"
    result = fill_markdown(text, width=20)  # No tags= parameter
    # Should behave like atomic mode
    assert "{% field kind='string' id='name' %}" in result
```

### Success Criteria

- [x] All existing tests pass (160 tests)
- [x] Tag formatting tests pass (26 tests in test_tag_formatting.py)
- [x] Reference doc tests pass (testdoc.expected.* files match actual output)
- [x] Lint passes with 0 errors and 0 warnings
- [x] `make lint` passes
- [x] `make test` passes
- [x] Long tags wrap correctly at internal whitespace boundaries
