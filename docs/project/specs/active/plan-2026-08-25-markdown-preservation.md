# Plan Spec: Markdown Preservation — Never Corrupt What the Parser Does Not Model

**Date:** 2026-08-25

**Status:** Active, revised after the senior review on
[#71](https://github.com/jlevy/flowmark/pull/71). Tracks A (math) and C (inline code) are
measured with corpora written; Track B is planned from the verified ledger in #62. The
review's blocker changed the architecture from post-parse to pre-parse, the recognition
rule from an intersection to a superset, the test contract from language-specific to
language-neutral, and the phase order back to math-first. Sections carrying those
revisions say so inline.

**Consolidates:** this is the single spec for all three tracks. It absorbed an earlier
math-only draft, now deleted rather than left to rot alongside it, and it supplies the
plan that `fm-drjv`, `fm-7vmg` and `fm-w467` referenced from July onward but which was
never written. Those three beads now point here. No other spec covers this ground —
verified against every bead's `spec_path`, open and closed.

## Purpose

flowmark parses to an AST and re-emits with reflow. Any construct the parser does not
model as opaque is treated as prose and reflowed — often corrupting it. Because flowmark
is designed to be "safe to run automatically on save or at any stage of a document
pipeline," the goal is **preservation**: round-trip these constructs verbatim, even where
flowmark cannot and should not fully parse every dialect.

This is one problem with one mechanism, so it gets one spec. It has three tracks:

- **Track A — mathematics.** Highest priority, and scheduled first. Measured end to end,
  with a checked-in corpus that reproduces every defect.
- **Track B — the rest of the ledger.** The twelve construct families in
  [#62](https://github.com/jlevy/flowmark/issues/62), empirically verified there.
- **Track C — inline code.** Fourteen measured defects in the construct flowmark already
  believed it handled correctly. Scheduled *first among the fixes*, because it owns the
  span code path the other two tracks build on.

**Sequencing.** Math is the critical path throughout. An earlier draft put Track C's
fixes first, on the reasoning that inline code owned a shared span path math could
inherit; review FM-PR71-01 disproved that, because the shared path runs *after* parsing
and cannot carry math at all. The order is now: the shared contract, then math end to
end in both ports, then Track C, then Track B. Track C stays tracked and tested but
gates nothing.

**The principle throughout: preserve, do not parse.** Several of these constructs have no
single standard — `:::` has at least four mutually incompatible dialects — so there is no
correct "parse it," only "do not break it."

## Terminology

- **span** — an inline run with its delimiters, living inside a paragraph.
- **block** — a region occupying whole lines.
- **atomic** — flowmark's existing wrapping guarantee: one indivisible word, so a wrap
  boundary moves it whole rather than splitting it. `AtomicPattern` in
  `src/flowmark/linewrapping/atomic_patterns.py`.
- **opaque** — the block-level equivalent: the region round-trips verbatim, line
  structure included, never reflowed.
- **recognition vs treatment** — the distinction the whole design rests on. Recognising
  where a construct starts and ends is the hard, dialect-specific part. What to do once
  recognised is the same everywhere: leave it alone.

## The Unifying Rule

Every row in all three tracks reduces to one statement:

> A construct flowmark does not model must be recognised well enough to be bounded, then
> emitted byte-for-byte. Recognition may be conservative and may miss cases. Treatment
> may never alter a byte inside the bounds.

Two consequences worth stating because they settle most design arguments:

1. **Inline code and inline math get identical treatment** — but only once both are
   bounded *before* parsing. They differ in recognition: a code span self-delimits by
   backtick runs, `$…$` is context-sensitive and collides with prose. Once bounded, both
   are atomic, both are exempt from escaping and typographic rewriting, and both preserve
   their interior per the contracts below. Testing this claim is what turned up Track C's
   fourteen bugs; testing it *again*, at the review's prompting, is what turned up
   FM-PR71-01 — the treatment cannot be shared at all where the current code path puts
   it, because Marko has already rewritten the interior by then.
2. **False positives are cheap; false negatives corrupt.** Wrongly deciding a run of text
   is opaque costs at most an overlong line. Wrongly deciding it is prose changes bytes.
   This asymmetry argues for erring toward recognition throughout — a principle the
   earlier recognition rule stated and then applied backwards, which FM-PR71-02 caught.

## Track A: Mathematics

Highest priority. This track is measured, not estimated: a 39-case battery was run
against both ports, and the corpus in `tests/tryscript/fixtures/content/math.md`
reproduces every defect below.

### What was measured (Track A)

A 39-case battery was run against **flowmark 0.7.3 (Python)** and **flowmark-rs 0.3.2
(Rust)** with `--auto`. Both ports produced identical classifications, confirming shared
behaviour rather than a port regression.
Sixteen cases corrupt content.
The failures fall into four mechanisms, M1 through M4; M3 and M4 are not in #70, and M3 is in
neither issue. Two further defects, C1 and C2, are on the code-span side and are
described in Track C.

**Defect M1 — span splitting.** `$…$`, one-line `$$…$$`, and `` `\(…\)` `` are absent from
`ATOMIC_PATTERNS`, so a wrap boundary falling inside one splits it.
A newline inside a formula defeats `grep` and breaks renderers that require inline math
to stay on one line.

**Defect M2 — escape injection.** Once a span is split, the fragment beginning the new
line goes through `markdown_escape_word`
(`src/flowmark/linewrapping/text_wrapping.py:70`), which prefixes a backslash to a word
that is exactly `-`, `*`, `+`, `>`, `#+`, or `N.`/`N)`. So `$a + b + c + d$` becomes:

```text
… now ok $a + b + c
\+ d$ tail.
```

The `\+` is a character that was not in the input.
This is content corruption, not layout.
Note the escape is *correct behaviour for prose* — a bare `+` at line start would
otherwise parse as a list bullet — which is why the fix belongs in math detection, not
in the escaper.

**Defect M3 — typographic transforms inside math.** This one needs no wrap boundary at
all:

```text
IN : Short $x'y$ tail.
OUT: Short $x’y$ tail.
```

Smartquotes curls the apostrophe inside the math span on a short line, and a curly quote
is not valid TeX input.

The trigger is narrow and worth stating exactly, because the obvious summary of it is
wrong. Measured: the apostrophe curls only when it sits between two word characters —
`$x'y$` and `$n'th$` are rewritten; `$f'(x)$`, `$a'$`, `$x' + y$` and
`` `$\alpha'\beta$` `` are not. So this does not hit every derivative in a document, as
a first look suggests; it hits the contraction-shaped subset, which includes real
mathematics such as a transposed product.

Straight double quotes inside a span are also curled. Because both are independent of
wrapping, fixing M1 and M2 will **not** fix them; they need their own guard in
`src/flowmark/typography/`.

**Defect M4 — block collapse.** Every display form that is not a fenced code block is
flattened onto a single line:

```text
IN                          OUT
$$                          $$ \begin{aligned} a &= b + c \\
\begin{aligned}              d &= e + f \end{aligned} $$
a &= b + c \\
d &= e + f
\end{aligned}
$$
```

This is #62's P1 item 6, and it applies equally to `` `\[…\]` ``,
`` `\begin{equation}…\end{equation}` ``, and the MyST labelled form. Non-whitespace
characters survive, so the formula usually still renders — but the line structure that
makes an aligned environment readable is gone, and the git diff for any edit to such a
block becomes whole-block noise. Only the fenced forms (` ```math `, ` ```{math} `)
escape, because a code fence is already opaque.

### Measured results by syntax

Verified, not assumed.
“Safe” means content and span integrity both held.

| Syntax | Form | Result today |
| --- | --- | --- |
| `$…$` | inline | **corrupt** (M1, M2, M3) |
| `$$…$$` on one line | inline display | **corrupt** (M1, M2) |
| `$$…$$` across lines | block display | **corrupt** (M4) |
| `\(…\)` | inline | **corrupt** (M1, M2) |
| `\[…\]` | block | **corrupt** (M4) |
| `\begin{equation}…\end{equation}` | block | **corrupt** (M4) |
| ` ```math ` fence | block (GitHub, GitLab) | safe — code fence |
| `` $`…`$ `` | inline (GitLab) | safe — code span is already atomic |
| ` ```{math} ` | block (MyST) | safe — code fence |
| `` {math}`…` `` | inline (MyST) | safe — code span is already atomic |
| `$$…$$ (label)` | labelled block (MyST) | **corrupt** (M4) |

Every non-math dollar case tested is safe today and must stay that way: two currency
amounts in one line, currency across a wrap boundary, escaped `\$`, `$HOME`/`$PATH`, a
trailing lone `$`, an unclosed `$a + b`, dollars in separate paragraphs, and dollars
inside code spans and fences.

Only the two fenced forms are genuinely safe, and they are safe for a reason that has
nothing to do with math: a code fence is already opaque. Everything else either splits
(inline) or collapses (block).

### Why the bug survived this long

`tests/tryscript/fixtures/content/math.md` already exists in **both** repos and is
referenced by **no test in either**. It is a dead fixture: nothing formats it, so
nothing compares its output.
It also contains only two short constructs, neither long enough to reach a wrap column.
Turning that file into a real, exercised corpus is the largest single piece of this
work.


## Track C: Inline Code Correctness

Found by testing the Unifying Rule's claim that code spans and math spans get identical
treatment. They do not, and every difference is a bug on the code-span side. Track C is
scheduled **before** the math fixes because it owns the shared span code path: once a span
is emitted byte-for-byte, math inherits that rather than needing a stricter path of its
own.

Measured with a 30-case battery against flowmark 0.7.3. Sixteen cases change; two of those
changes are correct, leaving **fourteen defects** in two families.

### Defect C1 — delimiter runs are collapsed regardless of content

flowmark shortens a multi-backtick delimiter to a single backtick unconditionally. That is
harmless when the content has no backticks and **structurally corrupting** when it does,
because the shortened delimiter is then closed early by a backtick inside the content.

```text
IN                              OUT
``simple``                 →    `simple`                  (correct: same render)
``has ` tick``             →    `has ` tick`              (broken: span ends at the inner tick)
``code with `backtick` in``→    `code with `backtick` in` (broken: becomes two spans)
```outer with `` inner```  →    `outer with `` inner`     (broken)
```

The corruption is silent and idempotent — stable after one pass, so it is a one-time
structural change rather than runaway. It fires in every context including table cells.

This is what mangled this spec's own table cells while it was being written, and it is
almost certainly the same root as [#58](https://github.com/jlevy/flowmark/issues/58).

### Defect C2 — whitespace inside a span is normalised

```text
`a    b`   →  `a b`      6 bytes of content become 3; internal runs are significant
`  a  `    →  ` a `      then `a` on a second pass — not idempotent
`   `      →  ` `        all-space content is exempt from the strip rule
`a<TAB>b`  →  `a b`      tabs inside a span are significant
```

CommonMark 0.31.2 §6.1 converts line endings to spaces and strips one space from each end
only when the content both begins and ends with a space **and is not entirely spaces**.
Internal runs and tabs are significant. Rewriting source `` `  a  ` `` to `` ` a ` ``
also changes what a renderer produces, since ` a ` then strips to `a`.

The cause is ordering rather than intent: the paragraph-level `re.sub(r"\s+", " ", text)`
in `wrap_paragraph_lines` runs before atomic protection, so a span's interior is
normalised before anything declares it untouchable. No test pins the current behaviour.

**The context asymmetry is the diagnostic.** C2 fires in paragraphs, list items,
blockquotes and link text, but **not** in table cells or headings — which take a different
emit path that never reaches that normaliser. C1, by contrast, fires everywhere including
tables. So the two defects are independent, and C2's fix belongs at the point the
paragraph path diverges from the others.

### What is already correct

Regression cover, confirmed by the same battery: a line ending inside a span becomes a
space (CommonMark-correct); backslashes, emphasis markers, HTML, entities and block
markers all survive literally; no typographic transform fires inside a span, so straight
quotes, apostrophes, ellipses and double hyphens are left alone; and spans are atomic for
wrapping, including one whose content begins with a list marker and one longer than the
wrap column.

### The corpus

`tests/tryscript/fixtures/content/code-inline.md`, which — exactly like `math.md` —
already existed in both repos, was referenced by **no test in either**, and whose final
line was already the C1 reproducer:

```text
Multiple backticks: ``code with `backtick` inside``.
```

The shipped fixture corrupts itself on that line. It is now a five-part corpus on the same
shape as the math one: delimiter runs, whitespace, literal content, block contexts, and
wrapping. It reproduces all fourteen defects.

## The Recognition Rule

Revised after [review FM-PR71-02](https://github.com/jlevy/flowmark/pull/71). The
earlier version of this section described itself as "the union of the strictest
constraints from Pandoc and GitHub," and that was the error: a union of *restrictions*
is an intersection of *accepted forms*, so the rule recognised less than either dialect.
Under this spec's own asymmetry — false positives are cheap, false negatives corrupt —
that is backwards.

### What the earlier rule got wrong, measured

Probed against pandoc 3.1.3:

| Source | Pandoc | Earlier rule here |
| --- | --- | --- |
| `H$_2$O` | math | **rejected** (opener follows an alphanumeric) |
| `1$a$` | math | **rejected** (same) |
| `$a$B` | math | **rejected** (closer precedes a letter) |
| `x $a +`⏎`b$ y` | math | **rejected** (no-newline clause) |
| `$$ a + b $$` | math | **declared out of scope** |
| `$a$2` | not math | not math |
| `$100 and $200` | not math | not math |

The last two rows are the point. **Pandoc rejects the currency case using only its three
documented rules**, with none of the restrictions this spec had added to justify exactly
that protection. In `$100 and $200` the candidate closer is preceded by a space, which
Pandoc's rule already rejects. The extra clauses bought nothing and cost five valid
forms.

### The rule

Recognition is **preservation-biased**: a superset of the common dialects, with no
configuration needed for standard forms. Inline `$…$`:

1. The opening `$` is not escaped (see parity below), and the character after it is not
   whitespace.
2. The character before the closing `$` is not whitespace.
3. The character after the closing `$` is not a digit.
4. The pair does not span a blank line — that is, never across a paragraph boundary. A
   soft newline inside is permitted, because Pandoc accepts it.

That is Pandoc's documented rule plus the paragraph-boundary guard. It is deliberately
*not* GitHub's stricter variant; where a dialect is narrower, recognising the wider form
only risks an unbreakable span, while failing to recognise it corrupts content.

Display `$$…$$` uses its own rule and does **not** inherit the inline whitespace
restrictions: Pandoc accepts `$$ a + b $$`.

`\(…\)` and `\[…\]` have unambiguous delimiters and need only the container and nesting
rules in the block scanner contract.

### Escape parity

A single backslash escapes; two backslashes are a literal backslash and the `$` still
opens. So the test is the **parity of the backslash run** immediately before the
delimiter, not the one-character check the earlier draft specified:

```text
\$a$      escaped, not math
\\$a$     opens math
\\\$a$    escaped again
```

### The body rule

The body may contain an escaped `\$` but never a bare `$`. This survives from the
earlier draft and is still verified against the interleaved line in
`tests/testdocs/testdoc.orig.md`: the permissive body finds 3 of 3 true spans and
captures neither currency amount, while excluding `$` outright finds 1 of 3.

### On false positives

Restated because the earlier draft asserted this and then contradicted it. A false
positive costs at most an unbreakable span and an overlong line; no character changes. A
false negative changes bytes. Recognition should therefore err wide. Where a strict
profile is genuinely wanted it belongs behind an option, not in the default — and this
spec does not currently propose one.


### Desired behaviour, by construct

**Inline spans — must become atomic, must not be typographically transformed.**

| Construct | Dialects | Required behaviour |
| --- | --- | --- |
| `$…$` | GitHub, GitLab, Pandoc, MyST, Obsidian, Quarto | Atomic. Interior byte-identical. |
| `$$…$$` on one line | GitHub, Pandoc | Atomic. Interior byte-identical. Matched before `$…$`. |
| `\(…\)` | MathJax default, raw LaTeX | Atomic. Interior byte-identical. |
| `` $`…`$ `` | GitLab | Already safe. Pin with a test; keep the whole thing one word. |
| `` {math}`…` `` | MyST | Already safe. Pin with a test. |

**Blocks — must be opaque, interior preserved line for line.**

| Construct | Dialects | Required behaviour |
| --- | --- | --- |
| `$$` … `$$` on own lines | ubiquitous | Opaque. Line structure preserved. |
| `\[` … `\]` | MathJax, LaTeX | Opaque. Line structure preserved. |
| `\begin{env}` … `\end{env}` | LaTeX, MathJax | Opaque. Line structure preserved. |
| ` ```math ` | GitHub, GitLab | Already safe as a fence. Pin with a test. |
| ` ```{math} ` | MyST | Already safe as a fence. Pin with a test. |
| `$$ … $$ (label)` | MyST | Opaque; the trailing label must survive. |

**Non-math dollars — must never be captured.**

Currency (single, multiple, and across a wrap boundary), escaped `\$`, shell variables
`$HOME`/`$PATH`/`$1`, a lone `$`, a trailing `$`, an unclosed `$a + b` at end of line,
dollars in different paragraphs, dollars inside code spans and code fences, and `$a+b$5`
(closing `$` followed by a digit).


## Track B: The Rest of the Ledger

Twelve construct families, empirically verified in
[#62](https://github.com/jlevy/flowmark/issues/62) against a round-trip battery. Severity
is #62's. The math rows are struck through here because Track A owns them, and #62's
"already robustly safe" list needs one correction: it names the interior of `$…$` inline
math as safe, which [#70](https://github.com/jlevy/flowmark/issues/70) and Track A
disprove.

| # | Construct | Observed result | Sev |
| --- | --- | --- | --- |
| 1 | Pandoc multiline tables | dashed rules became `* * *` breaks + `##` headings; rows merged | P0 |
| 2 | Obsidian callouts | `> [!tip]+ My Title` → `> [!TIP]`; drops custom title and fold marker | P0 |
| 3 | `:::` containers / Pandoc fenced divs | collapsed to prose; panels merged | P0 |
| 4 | TOML `+++` frontmatter | reflowed into one prose line | P0 |
| 5 | Definition lists | `Term` / `: Def` collapsed to `Term : Def` | P0 |
| 6 | ~~`\[…\]` and `$$…$$` block math~~ | ~~collapsed onto one line~~ — **Track A** | P1 |
| 7 | Pandoc grid tables | not recognised; body cells reflow | P1 |
| 8 | Raw multi-line HTML blocks | collapsed onto one line | P1 |
| 9 | `{.class #id}` attribute lists and spans | reflowed or splittable | P1 |
| 10 | Line blocks (`\|`) | lone `\|` line reflows and loses the marker | P2 |
| 11 | ~~LaTeX `\(…\)` inline~~ | ~~reflowed as prose~~ — **Track A** | P2 |
| 12 | MyST roles and wikilinks | survive only when an adjacent atomic span covers them | P2 |

Rows 1–5 are real data loss and outrank everything in Track A except that Track A proves
the mechanism they all depend on. That is the whole scheduling argument: Track A is small,
fully measured, and exercises block passthrough, inline atomics and the typography guard
together.

### Dialect-agnostic recognition rules

From #62, preferred because they are robust across flavours without parsing any dialect:

- **`:::` regions** — `^:{3,}` opener to a bare `:::`-run closer, counts need not match
  (Pandoc's rule). Covers all four dialects without reading the info string.
- **Attribute groups** — protect a line that is only `^\s*\{[.#][^}]*\}\s*$`, and
  inline `]{…}` spans.
- **`+++` frontmatter** — teach the frontmatter splitter the delimiter, mirroring `---`.
- **Callouts, multiline and grid tables, definition lists, raw HTML blocks, line
  blocks** — opaque-block passthrough, or enable and test a parser extension where one
  exists and round-trips.

### On waiting for the parser

#62 records that comrak 0.52's `block_directive` covers `:::` only, does not handle
`::: {.class}` info-string or nesting semantics, and that comrak still has no fields for
attributes, Pandoc fenced divs, grid tables, Pandoc definition lists, line blocks, or
TOML frontmatter. A parser upgrade alone fixes almost none of this. The pre-parse
passthrough is both the faster and the more robust route.

## Architecture

### Protection must happen before parsing

Revised after [review FM-PR71-01](https://github.com/jlevy/flowmark/pull/71), which is a
**blocker against the earlier design** and is confirmed by measurement.

The earlier draft put math recognition in the wrapping and typography stages — after
Marko has parsed the source into inline nodes. That cannot work, because by then the
formula may no longer be one string and the original bytes may already be gone:

```text
IN : Short math $\text{__init__}$ tail.
OUT: Short math $\text{**init**}$ tail.
```

Marko converted `__init__` into a `StrongEmphasis` node before any renderer ran. No
post-parse atomic pattern can recover it, because there is no longer a single text node
spanning the formula. Two further probes confirm the same shape:

```text
Short math $\$1 + x'y$ tail.     ->  Short math $\$1 + x’y$ tail.
Short math $a *b* ... c$ tail.   ->  Short math $a *b* … c$ tail.
```

The second is split around an `Emphasis` node, so a raw-text guard cannot see the whole
span. Two claims the earlier draft made are therefore **false and are withdrawn**:

- that M2 follows automatically from M1 — it does not, because escape injection is not
  the only way the interior changes;
- that math can become byte-exact by inheriting the code-span path — it cannot, because
  that path runs after the damage.

**Protection is a pre-parse facility.** Track B had already concluded this; Track A must
use the same boundary rather than a second, weaker one. Two admissible designs:

1. **Source scanner with a side table.** Extract protected regions into a collision-safe
   side table before Markdown parsing, then restore the exact slices after rendering.
   This is the mechanism the Rust port already uses for its PUA-marker passthrough.
2. **Parser extension.** Recognise math before generic emphasis and link parsing and
   retain the raw source slice on a dedicated opaque node.

Either way the contract must state: placeholder collision handling, width accounting for
the wrapper, index and encoding semantics, and exact restoration. Typography, escaping,
cleanup and wrapping then consume **typed protected regions** rather than rediscovering
them from already-parsed text.

### The block scanner contract

Revised after [review FM-PR71-04](https://github.com/jlevy/flowmark/pull/71). "A `$$`
line opens an opaque region terminated by the next `$$` line" is not a specification —
it leaves a scanner free to consume delimiters inside code fences, swallow the rest of a
document after an unmatched opener, or close the wrong environment.

The scanner is linear-time with explicit states and this precedence:

- Already-opaque blocks win: fenced and indented code, frontmatter, and existing
  passthrough regions are recognised **before** math.
- Container prefixes and indentation (blockquote, list) are carried through opener and
  closer matching. MyST supports display math and starred amsmath environments inside
  lists and quotes, so top-level-only matching is insufficient.
- Inline `$$` and block `$$` are distinguished.
- `\[` matches only `\]`; `\begin{name}` matches only the same `\end{name}`, including
  starred and custom names.
- Nesting and mismatched-closer behaviour is defined, not incidental.
- An unmatched opener has a stated fail-safe that does **not** consume unrelated trailing
  prose.
- Line endings and attached labels or attributes are preserved per the input-normalisation
  contract below.
- Behaviour stays O(n) on input with many unmatched delimiters.

Specify this as language-neutral pseudocode with test vectors, not as a Python regex:
Rust's `regex` crate supports neither backreferences nor lookaround, and flowmark's
existing `INLINE_CODE_SPAN` pattern uses a backreference — `` (`+)(?:(?!\1).)+\1 `` — so
the current Python mechanics are literally unportable. That is why the port contract is
black-box (FM-PR71-03) rather than a source translation.

### Recognition arbitration, and why ordering does not settle it

Revised after [review FM-PR71-05](https://github.com/jlevy/flowmark/pull/71), which
disproves the "keep code spans first" resolution this spec previously recorded as
settled. Alternation order only decides between matches starting at the **same** offset.
For `` $`a+b`$ `` the dollar candidate starts at offset 0 and the code span at offset 1,
so leftmost-match wins regardless of order. Verified both ways: each produces a single
math span at offset 0.

The consequence is an API break, not just a byte question. Today
`iter_atomic_spans(..., MARKDOWN_INLINE_PATTERNS)` yields three spans for that source — a
non-atomic `$`, an atomic `inline_code_span`, and a non-atomic `$`. A generic dollar
recogniser yields one. Output bytes may agree; public names, offsets and boundaries do
not.

So the GitHub/GitLab dollar-backtick form needs its **own** recogniser with a stated
arbitration rule, not an ordering assumption. Add public-API conformance cases asserting
exact span text, offsets, atomic flag and name. If the default tuple's behaviour changes,
that is a break to classify and document honestly — a changelog line is not SUPPORT BOTH.

### Normative preservation contracts

Revised after [review FM-PR71-06](https://github.com/jlevy/flowmark/pull/71). The earlier
draft said treatment never changes a byte, then allowed CommonMark normalisation of code
spans, then proposed a "non-whitespace characters unchanged" test helper — which would
pass exactly the whitespace corruption byte-exactness forbids. Three separate contracts,
stated separately:

- **Opaque constructs (math, and Track B's families).** Exact source-slice preservation,
  after an explicitly defined decoding and newline-normalisation step.
- **Code spans.** Either preserve the authored source exactly — the safest formatter
  policy and the one this spec now prefers — or specify the exact CommonMark
  canonicalisation and delimiter-emission algorithm. Not both.
- **Surrounding prose.** May reflow, but only outside protected regions.

Tests assert protected-slice equality and exact committed output bytes. **The
non-whitespace helper is withdrawn as an oracle.** "Byte" also needs defining at the CLI
boundary: Python currently reads and writes in text mode, which can normalise CRLF, and
Python string indices are code points while Rust's are UTF-8 byte offsets. The contract
must cover UTF-8, combining characters, tabs, LF/CRLF, a missing final newline, and
invalid encoding.


## Test Architecture: Language-Neutral by Construction

Revised after [review FM-PR71-03](https://github.com/jlevy/flowmark/pull/71). The earlier
draft leaned on `admin/port-coverage-mapping/` — test-name mapping plus literal discovery
counts — and on manually copying fixtures between the repos. That is **inventory, not
conformance**. It proves two test names were acknowledged; it proves nothing about the
same bytes, arguments, configuration, stdout, stderr, exit status, or file mutations. And
manual mirroring creates two sources of truth that drift silently.

### The governing decision

**The contract is language-neutral. Nothing that only one language can run is normative.**

This is not a preference about style; it is forced by the code. Rust's `regex` crate
supports neither backreferences nor lookaround, and flowmark's existing
`INLINE_CODE_SPAN` is `` (`+)(?:(?!\1).)+\1 `` — a backreference. The Rust port already
approximates code spans with separate one- through four-backtick patterns because it
cannot express the Python one. A source-level regex port is therefore impossible, and any
contract phrased in Python mechanics is unportable by construction.

Two artifacts already in this repo are language-neutral, and both are the right shape:

1. **The test documents.** `tests/tryscript/fixtures/content/*.md` are input bytes. They
   carry no language.
2. **The golden CLI tests.** `tests/tryscript/*.tryscript.md` are command plus expected
   output. The Rust repo runs the same tryscript files today.

Together they express the whole contract at the CLI boundary: given these input bytes and
these arguments, produce exactly these output bytes and this exit status. Both ports run
it; neither runs the other's language.

### What is normative, and what is not

| Artifact | Status | Why |
| --- | --- | --- |
| Corpus documents (`math.md`, `code-inline.md`, and Track B's) | **Normative** | input bytes, no language |
| Tryscript golden CLI cases | **Normative** | command, args, expected stdout/stderr, exit status |
| Shared parity corpus manifest | **Normative when it lands** | see below |
| Python unit tests | **Non-normative** | scanner internals only; never the parity contract |
| `test-mapping.yaml` and discovery counts | **Non-normative** | inventory, useful for coverage bookkeeping only |

Concretely, `tests/test_code_spans.py` and any math unit tests are demoted: keep them for
internals such as the scanner state machine, but **no behavioural guarantee may live only
there**. Every behaviour this spec promises must be expressible as input bytes plus a
golden CLI case.

### Merge the shared parity corpus in, rather than beside

`plan-2026-05-28-shared-parity-corpus.md` (tracker `fmr-bh2b`, still Draft) already
designs exactly this: one checked-in `tests/parity_corpus/`, committed input/expected
pairs, two thin native runners, and no Python runtime in Rust CI. The earlier draft of
this spec acknowledged it and then chose manual mirroring anyway. That was the wrong
trade, and it is reversed here: **landing the shared corpus is a prerequisite for the
implementation work**, not a parallel nice-to-have.

The manifest is the normative artifact, language-neutral and black-box:

```toml
schema_version = 1

[[case]]
id = "math.pandoc.multiline-inline"
tags = ["math", "pandoc", "stdin", "idempotent"]
args = ["--width", "40"]
input = "cases/math/pandoc-multiline/input.md"
expected_stdout = "cases/math/pandoc-multiline/expected.stdout"
expected_stderr = "cases/math/pandoc-multiline/expected.stderr"
exit_code = 0
```

It must support stdin/stdout cases and isolated file-tree cases; file cases declare
expected output files, backups, files that must be unchanged, and files that must not
exist. Both runners invoke a supplied executable at the CLI boundary and read the same
manifest and the same bytes. Expected results are committed and reviewed. Rust never
executes Python at test time.

The workflow this buys: an intentional Python behaviour change updates the shared
expected once, and Rust CI fails until the port matches. A temporary Rust
known-divergence list may shrink but never silently grow — a new unreviewed divergence
fails.

### Assertions, per case

For every passing case, assert exact stdout, stderr and file bytes and the exit status;
idempotence `F(F(x,c),c) = F(x,c)`; no mutation inside any protected region; no pairing
across a paragraph boundary; and Python/Rust equality against the same committed
expected. Do not strip whitespace before comparing — that was the withdrawn oracle.

### A gate against dead fixtures

Both corpora shipped for months referenced by no test, which is the whole reason these
defects survived. Add a fixture-inventory gate to
`scripts/check-golden-coverage.sh`: every file under `tests/tryscript/fixtures/content/`
must be referenced by at least one tryscript case, or CI fails. A dead fixture should be
impossible to add, not merely unlucky.

### The conformance matrix

The current corpora are a seed, not the contract. Before either can serve as the math
contract, these families are required — from the review, and each becomes corpus cases:

| Family | Required cases |
| --- | --- |
| Dollar boundaries | `H$_2$O`, `1$a$`, `$a$B`, `$a$2`, adjacent `$a$$b$`, empty/unclosed/mismatched runs |
| Escape parity | one to four backslashes before openers and closers; escaped dollars inside formulas |
| Multiline | soft newline inside `$…$`, blank-line boundary, multiline and whitespace-padded `$$`, missing closer |
| Parser collisions | `$\text{__init__}$`, emphasis/links/images/entities/HTML/backticks inside math, TeX comments |
| Markdown contexts | paragraph, heading, list, blockquote, table, link text, footnote, definition list, container, raw HTML adjacency |
| Block math | `$$`, `\[`, `equation`, `align*`, custom and nested environments, labels, container indentation |
| Opaque precedence | math-like delimiters inside inline code, fenced and indented code, frontmatter, raw blocks |
| Unicode and I/O | Unicode whitespace/digits/letters, CJK adjacency, combining marks, tabs, LF/CRLF, BOM and final-newline policy |
| Modes and boundaries | default, semantic, smartquotes, ellipses, auto, width 0/1 and N−1/N/N+1, stdin, file, in-place, check, config precedence |
| Adversarial | thousands of unmatched or adjacent dollars, deep nesting, very long spans, linear-time behaviour |
| Code spans | delimiter runs beyond four, shorter/equal/longer interior runs, tabs, all-spaces, multiline, unmatched runs, every block context |


## Test Corpora, and Which Gate Each Backs

Documented here because the parity gate this spec relies on depends on a corpus whose
provenance is recorded nowhere, and that is worth fixing before more work leans on it.

| Corpus | Checked in? | Purpose | Provenance |
| --- | --- | --- | --- |
| `tests/tryscript/fixtures/content/*.md` | yes | per-topic golden fixtures | hand-authored in repo |
| `tests/testdocs/testdoc.orig.md` + 4 expected | yes | whole-document reference goldens | hand-authored in repo |
| `flowmark-rs` `tests/parity/corner-cases.md` + 5 expected | yes | Python↔Rust corner cases | hand-authored in repo |
| `flowmark-rs` `benchmarks/corpus/` | no, regenerable | throughput and directory-walk timing | `benchmarks/generate_corpus.sh [N]` copies repo `.md` files round-robin into a 4–5 level tree, default 1000 files |
| `flowmark-rs` `attic/test-docs/` | **no** | the byte-parity gate between ports | **undocumented — see below** |
| `tests/parity_corpus/` (planned) | not implemented | CommonMark-seeded shared corpus | `plan-2026-05-28-shared-parity-corpus.md`, still Draft |

### The undocumented one

`scripts/corpus-parity-check.sh` defaults to `attic/test-docs`, 623 real-world files.
Two different things are worth separating here, because the convention is documented even
though the contents are not.

**What is documented: the `attic/` convention.** `attic/` is a gitignored, machine-local
scratch directory — the same place third-party repository checkouts go under tbd's
`checkout-third-party-repo` shortcut, which creates the directory and adds it to
`.gitignore`. It persists across sessions on one machine and is never tracked. So
`attic/test-docs` is by construction local to whoever assembled it.

**What is not documented: the contents.** No document in flowmark, flowmark-rs, or
`rust-porting-playbook` records which files those are, where they came from, or how to
rebuild the set. Verified against git history as well as the working trees: nothing under
`attic/` was ever committed (`git log --diff-filter=A -- "attic/*"` is empty), no download
or assembly step appears anywhere, and `corpus-parity-check.sh` arrived on 2026-02-19
already defaulting to the path with no accompanying creation step.

**The consequence follows from the convention.** A container session cannot have that
directory, so every fresh session finds it missing. That is exactly what the record shows:
a senior review flagged the non-reproducibility on 2026-05-28 and the response documented
a *substitute* (60 tracked repo files) rather than the original; two later syncs recorded
the same substitution. The script itself fails loudly when the directory is absent
(`exit 2`), so the degradation is a human decision to proceed with a smaller corpus, taken
in the open each time — not a silent failure.

The practical reading is that the corpus is a local directory on the maintainer's machine
that predates the port, and the answer lives there rather than in any repository.

The port-sync playbook documents the fallback honestly — substitute a repo-Markdown
spot-check and say so — and two sync artifacts show it being taken: 60 tracked files on
2026-05-28, a repo-Markdown spot-check on 2026-05-30. So the gate degrades visibly rather
than silently, but at roughly a tenth of its intended scale, and only one machine can run
it at full strength.

**Action:** recover the contents from the maintainer's machine, then either check in a
redistributable subset or document a reconstruction procedure. Note that the stalled
CommonMark-seeded corpus below is the structural fix for this same problem: a corpus that
is checked in and reproducible needs no provenance archaeology. Tracked separately; it blocks nothing here, because
Track A's evidence is the checked-in `math.md`, not the external corpus. Treat a green
`corpus-parity-check.sh` run as confirmation, and record which corpus it ran against.

### The planned shared corpus

`plan-2026-05-28-shared-parity-corpus.md` (tracker `fmr-bh2b`, Status: *Draft — proposal
pending upstream agreement*) would vendor all 655 CommonMark 0.31.2 spec examples
(CC-BY-SA 4.0) into `tests/parity_corpus/` in the Python repo, consumed by both ports
with no copy-paste. It is not implemented — that directory exists in neither repo.

It matters here for two reasons. It records a measured scratch run of **69/655 (~10.5%)
divergences** between Python 0.7.0 and the Rust port across ~12 spec sections, a real
signal currently invisible to CI. And if it lands, both tracks' cases belong in it as
`cases/flowmark/math/` and `cases/flowmark/preservation/` families rather than as a
parallel structure. Neither track blocks on it; both should be written so their cases can
migrate.


## Implementation Beads

Epic `fm-7vtx`. The file-and-function map below was written against the pre-review
architecture; the review invalidated part of it, so each row now states what survived.

| Bead | Work | Status after review |
| --- | --- | --- |
| `fm-fa8p` | C1: delimiter from the longest backtick run, `render_code_span` | **Stands.** Site and fix unchanged |
| `fm-9ey6` | C2: exclude atomic spans from whitespace normalisation | **Site stands, contract changes** — see Normative preservation contracts |
| `fm-uzvf` | `tests/test_code_spans.py` | **Demoted to non-normative.** Internals only; the contract is the corpus plus golden CLI cases |
| `fm-okli` | Wire both corpora into the tryscript goldens | **Stands and is now central** — this is the normative vehicle |
| `fm-ocpw` | Survey and regenerate changed goldens | **Stands** |
| `fm-q32c` | M1: three inline math atomic patterns | **Withdrawn.** Post-parse patterns cannot preserve source bytes (FM-PR71-01) |
| `fm-mu4s` | M3: typography through `iter_atomic_spans` | **Withdrawn** for the same reason; typography consumes typed protected regions instead |
| `fm-6erm` | M4: opaque display-math blocks | **Reframed.** Same goal, but from the pre-parse block scanner, not `block_heuristics.py` |

Review findings are tracked under `fm-mbhb` as `fm-f270`, `fm-pr8i`, `fm-50nn`,
`fm-dkpr`, `fm-844g`, `fm-trno` and `fm-ma9e`.

### What survived the review, and what did not

Worth stating plainly, because two of the three findings this spec was proudest of turned
out to be wrong in their *conclusions* even though the measurements behind them held.

**Survived.** Every measurement: the 19 math defect instances, the 14 inline-code
defects, C1's delimiter collapse and its exact trigger, C2's context asymmetry, the
dead-fixture discovery, and the body rule verified against the interleaved corpus line.
Those were probed, not inferred, and the review did not dispute any of them.

**Did not survive.** Three conclusions drawn *from* those measurements:

- that math could be protected by post-parse atomic patterns — refuted by a probe the
  review supplied and this spec reproduced;
- that a restrictive delimiter rule was the conservative choice — it was the opposite,
  and Pandoc's own simpler rule rejects the currency case without any of the added
  clauses;
- that pattern ordering settled the GitLab arbitration — alternation order cannot,
  because the two candidates start at different offsets.

The pattern is consistent: the empirical work was sound and the architectural inference
on top of it was not. That is worth remembering when reading the parts of this spec that
are still inference.


## Phases

Reordered after [review FM-PR71-07](https://github.com/jlevy/flowmark/pull/71). The
earlier order put all of Track C's tests, fixes and golden churn ahead of the math
implementation, on the reasoning that inline code owned the shared span path. FM-PR71-01
disproved that: the shared path runs after parsing, so it cannot carry math at all.
Track C was therefore gating the explicitly highest-priority feature for no reason.

Math is now the critical path. Track C stays tracked and tested but does not block it.

### Phase 0 — The shared contract (prerequisite)

- [ ] Land `plan-2026-05-28-shared-parity-corpus.md`: `tests/parity_corpus/`, the
      manifest schema, and two thin native runners.
- [ ] Add the fixture-inventory gate to `scripts/check-golden-coverage.sh` so a dead
      fixture fails CI.
- [ ] Write the pre-parse protection contract: placeholder collision handling, width
      accounting, index and encoding semantics, exact restoration.
- [ ] Write the block scanner as language-neutral pseudocode plus test vectors.

Nothing below starts until the contract exists, because everything below is expressed
against it.

### Phase 1 — Math corpus, as black-box cases

- [x] `tests/tryscript/fixtures/content/math.md`, Parts A–E.
- [ ] Extend it to the conformance matrix families, especially the parser-collision
      family that FM-PR71-01 exposed and the dialect forms FM-PR71-02 restored.
- [ ] Correct the two false claims in the current corpus: E5 (`$ a + b $`) is valid
      Pandoc display-adjacent input, not malformed; E7's "single-line in every dialect"
      is false, since Pandoc accepts a soft newline.
- [ ] Express every case as manifest entries plus tryscript goldens. Red is expected.

### Phase 2 — Pre-parse math protection in Python

- [ ] Implement the scanner and side table, or the parser extension, per the Phase 0
      contract.
- [ ] Typography, escaping, cleanup and wrapping consume typed protected regions.
- [ ] M4's display blocks come from the same scanner, not a separate mechanism.
- [ ] Regenerate goldens, including `testdoc.expected.auto.md` line 111, which records
      the collapsed `$$` form as expected output.

### Phase 3 — Rust math implementation against the same corpus

- [ ] Implement against the committed manifest — not a translation of the Python regexes,
      which is impossible (no backreferences or lookaround in `regex`).
- [ ] Drive the known-divergence list to zero for math.

### Phase 4 — Track C: inline code correctness

- [x] `tests/tryscript/fixtures/content/code-inline.md`, Parts A–E.
- [ ] C1: derive the delimiter run from the longest backtick run in the content.
- [ ] C2: settle the code-span contract per **Normative preservation contracts** —
      preferably preserve the authored source exactly — then implement it.
- [ ] Both ports, against the shared corpus.

### Phase 5 — Track B: the generic preservation scanner

- [ ] Broaden the Phase 2 scanner to the P0 rows: multiline tables, Obsidian callouts,
      `:::` containers, `+++` frontmatter, definition lists.
- [ ] Then the P1 and P2 rows.


## Backward Compatibility

**BACKWARD COMPATIBILITY REQUIREMENTS:**

- **Code types, methods, and function signatures**: KEEP DEPRECATED. `ATOMIC_PATTERNS`
  and `MARKDOWN_INLINE_PATTERNS` are public (`plan-2026-05-26-public-inline-api.md`). New
  patterns are additive; existing names, ordering semantics and the `AtomicPattern` shape
  do not change.
- **API compatibility for libraries**: SUPPORT BOTH. Adding math to the default tuple
  changes what `iter_atomic_spans` returns for math-bearing input. Strictly more
  protective, but a behavioural change worth a changelog line.
- **File format compatibility**: N/A. **Server API**: N/A. **Database schema**: N/A.

**Output compatibility** is the one that matters. This changes flowmark's output for
documents containing math, and — via Track C — for documents containing code spans with
internal whitespace or with backticks inside a wide delimiter. All are one-time changes
and all are the fix. Documents with
neither must be byte-identical, which the corpus parity machinery can demonstrate.

## Outstanding Questions

Resolved by the review, kept for the record:

- [x] Pattern ordering against `INLINE_CODE_SPAN` — **not resolvable by ordering.**
      Alternation decides only between matches at the same offset, and the two candidates
      for `` $`a+b`$ `` start at 0 and 1. Needs an explicit recogniser (FM-PR71-05).
- [x] C2 fix placement — subsumed by the pre-parse boundary; the paragraph normaliser is
      no longer where math is protected, though it is still where C2 lives.
- [x] `\begin{}` environment list — the block scanner contract settles it: match by name,
      including starred and custom names.

Open:

- [ ] Which pre-parse design: source scanner with a side table, or a parser extension?
      The side table matches what the Rust port already does for its PUA passthrough,
      which argues for it on portability grounds.
- [ ] Code-span contract: preserve the authored source exactly, or specify the exact
      CommonMark canonicalisation? This spec prefers the former; it needs a decision
      before Phase 4.
- [ ] Does the shared parity corpus land in `jlevy/flowmark` as its spec proposes, and
      does this work wait for it, or seed it?
- [ ] Which existing goldens change once protection moves pre-parse? Larger blast radius
      than the earlier estimate, since the scanner sees every document.

## Issue Disposition

- Closes [#70](https://github.com/jlevy/flowmark/issues/70) (Track A, M1–M2).
- Closes [#62](https://github.com/jlevy/flowmark/issues/62) across both tracks. Its
  "already robustly safe" list needs the `$…$` interior entry corrected.
- Very likely closes [#58](https://github.com/jlevy/flowmark/issues/58): C1 is delimiter
  collapse producing exactly the backtick mis-pairing that issue reports. C2 is a distinct
  defect in the same area.
- Contributes the two math forms to
  [#67](https://github.com/jlevy/flowmark/issues/67) (GitLab Flavored Markdown).

## An Adjacent Bug Found While Writing This

Formatting this spec corrupted it. Three table cells written as code spans containing
backticks — fenced-block info strings and the GitLab dollar-backtick form — came back with
their delimiters re-paired and content changed. That is #58 reproduced on a table row.

The spec is therefore in `.flowmarkignore`, temporarily, with a comment recording what to
re-check before removing the entry. Part C of the math corpus includes nested-backtick
spans so the shape is covered by a test even though the fix ships separately.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
