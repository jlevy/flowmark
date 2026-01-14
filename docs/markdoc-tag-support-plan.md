# Markdoc/Jinja/Nunjucks Tag Support in Flowmark

## Implementation Status

**✅ Phase 1 Complete** - Template tags are now kept as atomic units during line
wrapping.

Changes implemented:

- Extended `_HtmlMdWordSplitter` with patterns for `{% %}`, `{# #}`, and `{{ }}`

- Added `_generate_tag_patterns()` helper for programmatic pattern generation

- Unified all tag types (HTML, Markdown links, template tags) to use
  `MAX_TAG_WORDS = 12`

- Added unit tests for template tag handling

- Added integration tests in testdoc.orig.md (Section 16: Template Tags)

**✅ HTML Comment & Inline Code Preservation Complete**

Additional changes implemented:

- Added HTML comment patterns (`<!-- -->`) to keep inline comments together

- Added inline code span patterns (`` `code with spaces` ``) to preserve backtick
  content

- Removed `_normalize_html_comments()` function that was forcing all comments to
  separate lines

- Marko parser now handles HTML comments naturally (inline stays inline, block stays
  block)

- Added unit tests: `test_inline_code_with_spaces`,
  `test_inline_code_with_surrounding_punctuation`, `test_html_comments_kept_together`

- Added integration tests in testdoc.orig.md (Section 17: HTML Comments and Inline Code)

**✅ Markdown Link Coalescing Improved**

With the unified `MAX_TAG_WORDS = 12` limit, Markdown links with multi-word text are now
kept together as atomic units.
For example, `[Mark Suster, Upfront Ventures](url)` will not be split across lines.
This prevents awkward line breaks within link text.

Remaining work (future enhancements):

- Phase 2: Tag boundary detection for preventing line joining around block tags

- Phase 4: Block-level tag handling (recognizing block tags at Marko parser level)

## Overview

This document outlines the plan to add support for template-style tags (`{% %}` and
`{# #}`) in Flowmark’s Markdown formatter.
These tags are used by:

- **Markdoc** (Stripe’s documentation tool) -
  [markdoc.dev/docs/syntax](https://markdoc.dev/docs/syntax)

- **Jinja2** (Python templating) -
  [jinja.palletsprojects.com/templates](https://jinja.palletsprojects.com/en/stable/templates/)

- **Nunjucks** (JavaScript templating, Mozilla) -
  [mozilla.github.io/nunjucks/templating](https://mozilla.github.io/nunjucks/templating.html)

## Tag Syntax Summary

### Markdoc Tags

From the [Markdoc spec](https://markdoc.dev/spec):

| Syntax | Description | Example |
| --- | --- | --- |
| `{% tag %}...{% /tag %}` | Opening/closing pair | `{% callout %}Note{% /callout %}` |
| `{% tag /%}` | Self-closing tag | `{% partial file="x.md" /%}` |
| `{% tag attr="value" %}` | Tag with attributes | `{% if $showBeta %}` |

**Block vs Inline Rules:**

- Block-level: Opening and closing markers each appear on a line by themselves

- Inline: Tags appear within a paragraph on the same line as other content

### Jinja2/Nunjucks Tags

| Syntax | Description | Example |
| --- | --- | --- |
| `{% tag %}...{% endtag %}` | Block tags | `{% if x %}...{% endif %}` |
| `{# comment #}` | Comments | `{# TODO: fix this #}` |
| `{{ variable }}` | Variable interpolation | `{{ user.name }}` |

Common block tags: `if/elif/else/endif`, `for/endfor`, `block/endblock`,
`macro/endmacro`, `extends`, `include`, `raw/endraw`

### Key Differences

| Feature | Markdoc | Jinja2/Nunjucks |
| --- | --- | --- |
| Closing syntax | `{% /tag %}` | `{% endtag %}` |
| Self-closing | `{% tag /%}` | N/A |
| Comments | HTML `<!-- -->` | `{# ... #}` |
| Variables | `$variable` | `{{ variable }}` |

## Current Flowmark Architecture

### XML/HTML Tag Handling

The current implementation in `text_wrapping.py` uses `_HtmlMdWordSplitter` with
dynamically generated patterns via `_generate_tag_patterns()`:

```python
MAX_TAG_WORDS = 12  # Maximum words to coalesce into a single token

class _HtmlMdWordSplitter:
    def __init__(self):
        self.patterns: list[tuple[str, ...]] = [
            # Inline code spans: `content with spaces`
            *_generate_tag_patterns(start=r"[^\s]*`[^`]*", end=r"[^`]*`[^\s]*", middle=r"[^`]+"),
            # HTML comments: <!-- comment text -->
            *_generate_tag_patterns(start=r"<!--.*", end=r".*-->", middle=r".+"),
            # HTML/XML tags: <tag attr="value">content</tag>
            *_generate_tag_patterns(start=r"<[^>]+", end=r"[^<>]+>[^<>]*", middle=r"[^<>]+"),
            # Markdown links: [text](url) or [text][ref]
            *_generate_tag_patterns(start=r"\[", end=r"[^\[\]]+\][^\[\]]*", middle=r"[^\[\]]+"),
            # Template tags {% ... %}, {# ... #}, {{ ... }}
            *_generate_tag_patterns(start=r"\{%", end=r".*%\}", middle=r".+"),
            *_generate_tag_patterns(start=r"\{#", end=r".*#\}", middle=r".+"),
            *_generate_tag_patterns(start=r"\{\{", end=r".*\}\}", middle=r".+"),
        ]
```

This keeps HTML tags, template tags, inline code, and HTML comments as atomic tokens
during word splitting, preventing line breaks inside these constructs.

### Current Behavior on Template Tags

**After implementation**, Flowmark keeps template tags as atomic tokens:

- Words inside tags like `{% tag attr="value" %}` stay together

- Template comments `{# comment #}` and variables `{{ var }}` are preserved

- Tag attributes are never broken across lines

## Requirements

Based on user requirements:

1. **Do NOT wrap inside template tags** - `{% tag attr="value" %}` must stay as one unit

2. **DO wrap markdown between tags** - Content between `{% tag %}` and `{% /tag %}`
   should wrap

3. **Do NOT join lines onto template tags** - Preserve line structure around tags

4. **Reuse XML tag logic** - Extend the existing `_HtmlMdWordSplitter` pattern approach

5. **Unified behavior** - Same rules for HTML/XML tags and template tags

6. **Backward compatible** - No new line breaking/joining around existing tag types

## Implementation Plan

### Phase 1: Extend Word Splitter for Template Tags

**File: `src/flowmark/linewrapping/text_wrapping.py`**

Add patterns for template-style tags to `_HtmlMdWordSplitter`:

```python
class _HtmlMdWordSplitter:
    patterns: list[tuple[str, ...]] = [
        # HTML tags (existing)
        (r"<[^>]+", r"[^<>]+>[^<>]*"),
        (r"<[^>]+", r"[^<>]+", r"[^<>]+>[^<>]*"),

        # Template tags: {% ... %} (Markdoc/Jinja/Nunjucks)
        # Single word tag: {% tag %}
        (r"\{%[^%]*%\}",),  # Single token pattern for simple tags
        # Multi-word tags that span whitespace
        (r"\{%[^%]*", r"[^%]+%\}[^{]*"),
        (r"\{%[^%]*", r"[^%]+", r"[^%]+%\}[^{]*"),

        # Template comments: {# ... #} (Jinja/Nunjucks)
        (r"\{#[^#]*#\}",),  # Single token
        (r"\{#[^#]*", r"[^#]+#\}[^{]*"),
        (r"\{#[^#]*", r"[^#]+", r"[^#]+#\}[^{]*"),

        # Template variables: {{ ... }} (Jinja/Nunjucks)
        (r"\{\{[^}]*\}\}",),  # Single token
        (r"\{\{[^}]*", r"[^}]+\}\}[^{]*"),

        # Markdown links (existing)
        (r"\[", r"[^\[\]]+\][^\[\]]*"),
        (r"\[", r"[^\[\]]+", r"[^\[\]]+\][^\[\]]*"),
    ]
```

### Phase 2: Tag-Aware Line Break Prevention

The current word splitter keeps tags atomic, but we also need to prevent:

1. Joining lines when a template tag is at line start/end

2. Breaking lines immediately before/after template tags in certain contexts

**Approach: Tag Boundary Detection**

Add helper functions to detect template tag boundaries:

```python
# Patterns for detecting tag boundaries
TEMPLATE_TAG_START = re.compile(r'^(\{%|\{#|\{\{)')
TEMPLATE_TAG_END = re.compile(r'(%\}|#\}|\}\})$')
HTML_TAG_START = re.compile(r'^<[a-zA-Z/!]')
HTML_TAG_END = re.compile(r'>$')

def starts_with_tag(word: str) -> bool:
    """Check if word starts with an HTML or template tag."""
    return bool(TEMPLATE_TAG_START.match(word) or HTML_TAG_START.match(word))

def ends_with_tag(word: str) -> bool:
    """Check if word ends with an HTML or template tag."""
    return bool(TEMPLATE_TAG_END.search(word) or HTML_TAG_END.search(word))
```

### Phase 3: Sentence Splitting Awareness

**File: `src/flowmark/linewrapping/sentence_split_regex.py`**

Template tags should not trigger sentence breaks.
The current heuristic looks for sentence-ending punctuation, which shouldn’t match
inside `{% %}` or `{# #}`.

However, we should verify that:

- `%}` is not treated as sentence-ending

- `#}` is not treated as sentence-ending

- `}}` is not treated as sentence-ending

The current regex `([.?!]['\"'")]?|['\"'")][.?!])` should be safe, but we should add
test cases.

### Phase 4: Block-Level Tag Handling (Future Enhancement)

For full Markdoc support, block-level tags (tags on their own lines) may need special
handling:

```markdown
{% if $showFeature %}

This content should be wrapped normally.

{% /if %}
```

The current Marko parser integration doesn’t recognize Markdoc as special syntax.
Options:

1. **Minimal approach (recommended for now):** Treat block tags as regular paragraphs,
   just ensure they’re not broken or joined improperly

2. **Full integration (future):** Add Marko extension to recognize Markdoc block
   elements

### Phase 5: Testing

**Add test cases to `tests/testdocs/testdoc.orig.md`:**

```markdown
## Template Tag Tests

### Inline Template Tags

This paragraph contains {% if $condition %} inline template tags {% endif %} that should stay intact.

A Jinja comment {# this is a comment #} should not be split.

Variable interpolation like {{ user.name }} should stay together.

### Block Template Tags

{% callout type="warning" %}
This is a callout block.
The content inside should wrap normally.
{% /callout %}

{% if $showAdvanced %}

This conditional content is between block tags.
It should be wrapped but the tags themselves should stay on their own lines.

{% /if %}

### Mixed Content

Some text with {% partial file="snippet.md" /%} self-closing tags inline.

Complex attributes {% city name="San Francisco" coordinates=[37.7749, -122.4194] %} should stay atomic.

### Edge Cases

Long tag: {% very_long_tag_name with="many" attributes="here" and="more" values="too" /%}

Nested templates: {% if $a %}{% if $b %}nested{% /if %}{% /if %}
```

## Implementation Order

1. **Phase 1** - Extend word splitter patterns (~1 hour)

   - Add template tag patterns to `_HtmlMdWordSplitter`

   - Ensure patterns handle edge cases (nested braces, attributes with quotes)

2. **Phase 2** - Add tag boundary detection (~30 min)

   - Create helper functions for tag detection

   - Integrate with wrapping logic if needed

3. **Phase 3** - Verify sentence splitting (~30 min)

   - Confirm template tags don’t trigger false sentence breaks

   - Add test cases

4. **Phase 4** - Testing (~1 hour)

   - Add comprehensive test cases to testdoc.orig.md

   - Generate expected outputs

   - Verify behavior matches requirements

5. **Phase 5** - Documentation (~30 min)

   - Update README if needed

   - Document any limitations

## Potential Issues and Mitigations

### Issue 1: Nested Braces

Template tags can contain nested structures:
```
{% if items.length > 0 %}
{% set data = {"key": "value"} %}
```

**Mitigation:** The regex patterns should match from `{%` to the first `%}`, which
handles most cases. Complex nesting inside attributes is edge-case territory.

### Issue 2: Multi-line Tags

Markdoc allows tags to span multiple lines:
```
{% table
   columns=[{label: "Name"}, {label: "Age"}]
%}
```

**Mitigation:** Multi-line tags within a single paragraph block are unusual.
If needed, we could add a preprocessing step, but this is likely rare enough to defer.

### Issue 3: Code Blocks

Template tags inside fenced code blocks should be ignored (already handled since code
blocks preserve content exactly).

### Issue 4: Escaped Braces

Some templates allow escaping: `\{%` or `{{'{%'}}`

**Mitigation:** These are rare.
Document as a known limitation if issues arise.

## Success Criteria

1. Template tags `{% %}`, `{# #}`, `{{ }}` are never split across lines

2. Content between template tags wraps normally

3. Lines aren’t joined improperly across tag boundaries

4. Existing HTML/XML tag behavior is unchanged

5. All existing tests continue to pass

6. New test cases pass

## References

- Markdoc Syntax: https://markdoc.dev/docs/syntax

- Markdoc Spec: https://markdoc.dev/spec

- Jinja2 Templates: https://jinja.palletsprojects.com/en/stable/templates/

- Nunjucks Templates: https://mozilla.github.io/nunjucks/templating.html

- Current Flowmark XML handling: `src/flowmark/linewrapping/text_wrapping.py`
