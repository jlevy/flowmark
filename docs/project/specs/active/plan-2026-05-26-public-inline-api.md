# Plan Spec: Public Markdown-Inline API (atomic spans, sentence spans, AST/link extraction)

## Terminology

- **span** — a contiguous region of source text at a known location: `text` plus
  `[start, end)`. `AtomicSpan` (carries `is_atomic`) and `SentenceSpan`
  are both spans and share the same field order (`text, start, end, ...`).
- **range** — a bare `[start, end)` offset pair with no attached text (e.g. an
  offset-lookup result). Reserved term; flowmark's current surface returns spans, not bare
  ranges.
- "token"/"word" is avoided as a noun for these regions (it collides with LLM token
  counting and word-tokenization); it is kept only where it genuinely means token/word
  counts.

## Purpose

Design a small, clean, general-purpose public API surface in flowmark so **any**
downstream consumer can reuse flowmark's Markdown-inline knowledge — atomic constructs,
sentence boundaries, and AST/link traversal — instead of re-implementing it or copying
flowmark internals that may drift.

The goal is **generality and flexibility**, not tailoring to one client. flowmark already
contains well-tested logic for "what is an unbreakable Markdown construct," "where do
sentences end," and "how do I walk a marko tree." That logic should be exposed as a
deliberate, reusable API with clean parameterization, so it serves a tool that needs
exact link spans just as well as one that needs link-safe wrapping, token counting, or
content extraction.

chopdiff (PR #8, spec `plan-2026-05-26-block-aware-doc.md`) is the **motivating example**
that surfaced the need, and its Addendum requests four upstream changes. This spec treats
those requests as one concrete use case among many: it accepts their intent but generalizes
the design and adds two principles the Addendum underweights (see Background). Nothing here
should be specific to chopdiff's `TextDoc`.

## Background

Several kinds of consumer want flowmark's inline knowledge without re-deriving it:
exact link/code spans, link-safe sentence splitting, token/word counting that respects
atomic constructs, content/link extraction, and AST walks over GFM + footnote documents.
chopdiff is one such consumer (a block-aware `TextDoc` adding spans, sections, and link
rollups), but the API should not assume that shape. The logic all consumers need already
exists in flowmark, but lives in internal modules not in the public `__all__`:

- `src/flowmark/linewrapping/atomic_patterns.py` — `AtomicPattern`, the construct regexes
  (`INLINE_CODE_SPAN`, `MARKDOWN_LINK`, Jinja/HTML tags + comments), the ordered
  `ATOMIC_PATTERNS` tuple, and the combined `ATOMIC_CONSTRUCT_PATTERN`.
- `src/flowmark/linewrapping/sentence_split_regex.py` — `split_sentences_regex` and
  `heuristic_end_of_sentence`.
- `src/flowmark/transforms/doc_transforms.py` — `transform_tree` (robust marko walk) and
  `_collect_inline_segments`.
- `src/flowmark/formats/flowmark_markdown.py` — `flowmark_markdown()`, the configured
  GFM + footnote parser (already public).

Today flowmark already keeps two independent atomic mechanisms:

1. The **word splitter** used for wrapping (`get_html_md_word_splitter` /
   `_extract_atomic_constructs` in `text_wrapping.py:39`) protects atomic constructs by
   placeholder substitution, so wrapping never breaks a link or code span.
2. The **sentence splitter** (`split_sentences_regex`) does `text.split()` then
   `" ".join(...)`, so it is lossy (no offsets, normalized whitespace) and **not**
   atomic-aware. A sentence boundary can in principle fire inside a URL or link text.

flowmark's output is not currently broken by (2) because (1) re-protects atomics at wrap
time. But a consumer that wants sentence *spans* (chopdiff) is exposed to it directly.

### Two principles that shape this design

1. **Identity vs. spans.** marko does not record source positions for inline elements.
   So flowmark can answer *what* a link/code span/autolink is (via the AST, which handles
   reference links, autolinks, images, and escapes correctly), but it cannot return a
   source span for one from the AST alone. The division of labor that keeps the API
   general: **flowmark owns inline identity + sentence/atomic heuristics; the consumer
   maps to spans against its own source.** (Where a consumer works on raw text rather than
   an AST, `iter_atomic_spans` and `split_sentences_with_spans` *do* carry offsets — see
   Phase B — so flowmark still serves span-based consumers; it just can't synthesize spans
   for AST nodes marko never positioned.)

2. **Heuristic vs. parser.** The `MARKDOWN_LINK` atomic regex
   (`\[[^\]]*\](?:\([^)]*\)|\[[^\]]*\])?`) is a *line-wrapping heuristic*, not a Markdown
   parser. It deliberately disagrees with marko on nested brackets, reference-link
   resolution, images (`![...]`), and escaped brackets. It is correct for "don't break a
   line here" and wrong as an enumerator of links. The published API must keep these two
   notions separate and say so loudly, so a consumer never enumerates links from the
   regex (spans would silently diverge from rendered output).

## Summary of Task

Add two public submodules, strictly additively:

- **`flowmark.atomic`** — publish the atomic-construct patterns and a new
  offset-preserving span splitter `iter_atomic_spans(text, patterns=...)` that yields
  `(text, start, end, is_atomic)`. Make this the single atomic-span primitive and
  reimplement the wrapping word splitter on top of it. Add an offset-preserving,
  atomic-aware `split_sentences_with_spans(text)` built on the same primitive.
- **`flowmark.ast`** — publish a read-only `iter_inline(element)` and a convenience
  `extract_links(doc) -> list[Link]` where `Link(text, url, title)` carries **no span**
  (per the identity-vs-spans principle), built on the existing `transform_tree`.

Keep marko an implementation detail everywhere except `flowmark.ast`, where the AST is
unavoidably part of the contract.

### Explicitly not in scope

- No span on `extract_links` / `Link` (marko gives no inline offsets — consumer recovers
  spans). Documented as a deliberate boundary, not a TODO.
- No client-specific helpers (e.g. nothing shaped around a particular document model).
  The API is parameterized primitives; consumers compose them.
- No parallel wrapper types over marko's element hierarchy. Consumers use marko types.
- No change to the default `Splitter` / wrapping output in Phases A–B. Switching the
  default sentence splitter to the atomic-aware one is gated to Phase C behind golden
  tests.
- No new Markdown parsing features; `flowmark_markdown()` stays the parser.

### Acceptance criteria

- `from flowmark.atomic import ATOMIC_PATTERNS, ATOMIC_CONSTRUCT_PATTERN, iter_atomic_spans, split_sentences_with_spans`
  works and is covered by `__all__`.
- `from flowmark.ast import iter_inline, extract_links, Link` works and is in `__all__`.
- `iter_atomic_spans` round-trips: `"".join(sp.text for sp in iter_atomic_spans(s)) == s`
  and every span's `s[start:end] == text`.
- `split_sentences_with_spans(s)` never returns a span that bisects an atomic span; for
  verbatim input each returned span satisfies `s[start:end] == text`.
- The wrapping word splitter, reimplemented on `iter_atomic_spans`, produces byte-identical
  output across the existing golden corpus (no wrapping regression).
- `extract_links` agrees with marko on link identity for reference links, autolinks, and
  images-excluded cases in tests.

## Backward Compatibility

- **Code API:** Strictly additive. `split_sentences_regex`, `first_sentence`,
  `first_sentences`, and all existing `__all__` exports keep their current signatures and
  behavior. `split_sentences_regex` stays lossy/normalizing for its existing callers.
- **Output / file format:** No change in Phases A–B (wrapping output must be identical;
  enforced by golden tests). Any default-splitter change is deferred to Phase C and
  re-validated.
- **Internal moves:** `atomic_patterns.py` constants may be re-exported from
  `flowmark.atomic` without moving the source module, to avoid breaking internal imports
  (`text_wrapping.py`, `tag_handling.py`). The public submodule is the supported surface;
  internal module paths remain unsupported.
- **Versioning:** The new submodules follow semver. They are an intentional API, not
  de-underscored internals.

## Stage 1: Planning Stage

The work splits into three phases, smallest/lowest-risk first.

- **Phase A — publish patterns + AST helpers (pure additions).** Lets any consumer stop
  copying flowmark's regexes and re-walking the AST. No behavior change.
- **Phase B — offset-preserving, atomic-aware span splitter + sentence spans; refactor the
  wrapping word splitter onto the new primitive.** Collapses flowmark's two atomic
  mechanisms into one and gives any text-based consumer exact, link-safe spans. Wrapping
  output must not change.
- **Phase C — (gated, optional) make atomic-aware splitting the default sentence
  splitter.** Only if golden tests confirm equal-or-better output.

### Selectable pattern sets (a Phase-A/B design choice)

flowmark's `ATOMIC_PATTERNS` is tuned for wrapping and includes Jinja/Markdoc tags and
HTML. Different consumers want different sets: a prose/sentence consumer wants only the
Markdown-inline subset (code spans, links, autolinks); a template-aware tool wants the
full set; a custom tool may supply its own `AtomicPattern`s. So `iter_atomic_spans` takes
a `patterns` argument (the unit of flexibility) and flowmark ships named sets as
convenient defaults, not as the only options:

- `ATOMIC_PATTERNS` — the full wrapping set (current behavior, default for wrapping).
- `MARKDOWN_INLINE_PATTERNS` — code spans + links (+ autolinks/URLs) only, for prose.
- Consumers may pass any `tuple[AtomicPattern, ...]`, including their own constructs.

## Stage 2: Architecture Stage

### `flowmark.atomic`

Re-export from `atomic_patterns.py`: `AtomicPattern`, `INLINE_CODE_SPAN`,
`MARKDOWN_LINK`, the tag/comment patterns, `ATOMIC_PATTERNS`, `ATOMIC_CONSTRUCT_PATTERN`.
Add the new span splitter and the prose subset:

```python
class AtomicSpan(NamedTuple):
    text: str
    start: int
    end: int
    is_atomic: bool

def iter_atomic_spans(
    text: str,
    patterns: tuple[AtomicPattern, ...] = ATOMIC_PATTERNS,
) -> Iterator[AtomicSpan]:
    """Yield contiguous spans covering `text` exactly, each flagged `is_atomic`.

    Atomic spans match a construct that must not be split; non-atomic spans are
    the gaps between them. Round-trips: "".join(s.text ...) == text.
    """
```

Implementation: one `re.finditer` over the combined alternation built from `patterns`
(reuse the `ATOMIC_CONSTRUCT_PATTERN` construction), emitting the gaps between matches as
non-atomic spans. This is the single source of truth; `_extract_atomic_constructs` in
`text_wrapping.py` is reimplemented to consume it (placeholder substitution becomes
"join non-atomic spans, keep atomic spans whole").

Warning to document on `MARKDOWN_LINK` / the module: these patterns identify *unbreakable
spans for wrapping*, not links. To enumerate links, use `flowmark.ast.extract_links`.

### `flowmark.atomic` sentence spans

```python
class SentenceSpan(NamedTuple):
    text: str
    start: int
    end: int

def split_sentences_with_spans(
    text: str,
    min_length: int = SENTENCE_MIN_LENGTH,
    heuristic: Callable[[str], bool] = heuristic_end_of_sentence,
    patterns: tuple[AtomicPattern, ...] = MARKDOWN_INLINE_PATTERNS,
) -> list[SentenceSpan]:
    """Offset-preserving sentence split. Applies the end-of-sentence heuristic only
    at boundaries between atomic spans; never splits inside one. Preserves original
    whitespace and offsets (verbatim spans)."""
```

This reuses `heuristic_end_of_sentence` from `sentence_split_regex.py` so flowmark keeps
one sentence heuristic. The lossy `split_sentences_regex` is unchanged.

### `flowmark.ast`

```python
class Link(NamedTuple):
    text: str
    url: str
    title: str | None
    # No span: marko provides no inline source offsets. Recover spans by locating
    # `text`/`url` in the source (consumer responsibility).

def iter_inline(element: Element) -> Iterator[Element]:
    """Read-only depth-first iteration over inline elements within an inline scope."""

def extract_links(doc: Document) -> list[Link]:
    """All links in document order, via the marko AST (reference links, autolinks
    resolved; images excluded). Built on transform_tree."""
```

`iter_inline` is a thin read-only wrapper over the existing `transform_tree` walk;
`extract_links` filters for `inline.Link` (and `inline.AutoLink` / `gfm_elements.Url` as
appropriate), reading `dest`/`title` and rendering child `RawText` for `text`.

## Stage 3: Refine Architecture (reuse)

- **`transform_tree`** (`doc_transforms.py:37`) already does the robust container walk —
  `iter_inline` and `extract_links` wrap it; no new traversal logic.
- **`ATOMIC_CONSTRUCT_PATTERN` construction** (`atomic_patterns.py:186`) — reused to build
  the combined regex per pattern set.
- **`_extract_atomic_constructs`** (`text_wrapping.py:39`) — reimplemented on
  `iter_atomic_spans` rather than duplicated; removes one of flowmark's two atomic paths.
- **`heuristic_end_of_sentence`** (`sentence_split_regex.py:17`) — reused by
  `split_sentences_with_spans`; one heuristic, two splitters.

## Stage 4: Implementation Plan (TDD)

### Phase A — publish patterns + AST helpers

- [ ] Create `src/flowmark/atomic.py` re-exporting the patterns + `AtomicPattern`; add
      `MARKDOWN_INLINE_PATTERNS`; add the heuristic-vs-parser warning in the docstring.
- [ ] Create `src/flowmark/ast.py` with `Link`, `iter_inline`, `extract_links` on top of
      `transform_tree`.
- [ ] Tests: `extract_links` identity cases (inline, reference, collapsed, autolink,
      image-excluded); `iter_inline` ordering.
- [ ] Add the new names to `flowmark/__init__.py` `__all__` (or document submodule imports).

### Phase B — offset-preserving span splitter + sentence spans

- [ ] `iter_atomic_spans` with round-trip + atomic-boundary tests; selectable `patterns`.
- [ ] Reimplement `_extract_atomic_constructs` on `iter_atomic_spans`; confirm wrapping
      golden corpus is byte-identical.
- [ ] `split_sentences_with_spans` with verbatim-span + never-bisect-atomic tests.

### Phase C — (gated) default atomic-aware splitting

- [ ] Spike: route `line_wrap_by_sentence` through the atomic-aware splitter; diff golden
      corpus. Adopt as default only if equal-or-better; otherwise keep opt-in.

### Status

Planning. Not started.

### Open Questions

- Export the new names at top-level `flowmark.__all__` too, or only via the
  `flowmark.atomic` / `flowmark.ast` submodules? (Leaning: submodules are canonical;
  top-level re-export the few most-used names.)
- Should `extract_links` include images and autolinks by default, or take flags? (Leaning:
  links only by default; `include_images` / `include_autolinks` flags.)
- Move `atomic_patterns.py` under `flowmark/atomic/` eventually, or keep re-export
  indefinitely? (Leaning: re-export now; revisit if internals churn.)

## Assumptions

- marko exposes no source offsets for inline elements (verified by inspection); spans are
  the consumer's responsibility.
- `split_sentences_regex`'s existing callers (`line_wrappers.py:31`,
  `markdown_filling.py:33`) rely on its normalized-join behavior and must be left intact
  in Phases A–B.
