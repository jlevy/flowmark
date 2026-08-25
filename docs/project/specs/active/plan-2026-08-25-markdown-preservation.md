# Plan Spec: Markdown Preservation — Never Corrupt What the Parser Does Not Model

**Date:** 2026-08-25

**Status:** Active. Track A (math) is measured and its corpus is written; Track B is
planned from the verified ledger in #62.

**Consolidates:** this spec replaces `plan-2026-08-25-math-syntax-preservation.md` (math
only) and supplies the missing `plan-2026-07-30-rare-markdown-preservation.md` that
`fm-drjv`, `fm-7vmg` and `fm-w467` reference but which was never written.

## Purpose

flowmark parses to an AST and re-emits with reflow. Any construct the parser does not
model as opaque is treated as prose and reflowed — often corrupting it. Because flowmark
is designed to be "safe to run automatically on save or at any stage of a document
pipeline," the goal is **preservation**: round-trip these constructs verbatim, even where
flowmark cannot and should not fully parse every dialect.

This is one problem with one mechanism, so it gets one spec. It has two tracks:

- **Track A — mathematics.** Highest priority, and scheduled first. Measured end to end,
  with a checked-in corpus that reproduces every defect.
- **Track B — the rest of the ledger.** The twelve construct families in
  [#62](https://github.com/jlevy/flowmark/issues/62), empirically verified there.

Track A goes first not only because it is the priority but because it is the ideal proving
slice: math alone exercises **all three** mechanisms Track B needs — block-level opaque
passthrough, inline atomic spans, and a typography guard. Getting math green de-risks
everything after it.

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

Every row in both tracks reduces to one statement:

> A construct flowmark does not model must be recognised well enough to be bounded, then
> emitted byte-for-byte. Recognition may be conservative and may miss cases. Treatment
> may never alter a byte inside the bounds.

Two consequences worth stating because they settle most design arguments:

1. **Inline code and inline math get identical treatment.** They differ only in
   recognition — a code span self-delimits by backtick runs, `$…$` is context-sensitive
   and collides with prose. Once bounded, both are atomic, both are exempt from escaping,
   both are exempt from typographic rewriting, and both must be byte-exact inside. Any
   place where they currently differ in *treatment* is a bug, not a distinction to
   preserve. See **Defect M5** below, which is exactly such a bug.
2. **False positives are cheap; false negatives corrupt.** Wrongly deciding a run of text
   is opaque costs at most an overlong line. Wrongly deciding it is prose changes bytes.
   This asymmetry argues for erring toward recognition throughout.

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
neither issue. A fifth, M5, is on the code-span side and is described after them.

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


### Defect M5 — code span interiors lose whitespace, progressively

Found while writing this spec, by asking whether math and code spans really are treated
identically. They are not, and the difference is a bug on the code-span side.

```text
source            pass 1        pass 2        pass 3
`a    b`     →    `a b`         `a b`         `a b`
`  a  `      →    ` a `         `a`           `a`
```

Byte counts, since a Markdown renderer hides this: the first interior goes from 6 bytes
to 3. The second is worse — it is **not idempotent**, losing one space per pass for two
passes before it settles.

Per CommonMark 0.31.2 §6.1, a code span's content has line endings converted to spaces
and, if it both begins and ends with a space and is not all spaces, one space stripped
from each end. Internal runs are significant. So `` `a    b` `` must keep its four
spaces, and rewriting source `` `  a  ` `` to `` ` a ` `` changes what a renderer
produces (` a ` becomes `a`).

The cause is ordering, not intent: the paragraph-level `re.sub(r"\s+", " ", text)` in
`wrap_paragraph_lines` runs before atomic protection, so the interior is normalised
before anything declares it untouchable. No test pins the current behaviour.

This is adjacent to [#58](https://github.com/jlevy/flowmark/issues/58) and it belongs in
this spec rather than beside it, because the Unifying Rule says code spans and math spans
get identical treatment. Fixing it is a precondition for math spans being byte-exact by
the same code path, rather than math getting a special stricter path.

## The delimiter rule

The whole design rests on one question: when is a `$` math?
The rule below is the union of the strictest constraints from Pandoc’s
`tex_math_dollars` and GitHub’s renderer, so it is conservative in both directions.

A `$…$` span is recognised only when **all** hold:

1. The opening `$` is not backslash-escaped, and is not preceded by an alphanumeric
   character.
2. The character after the opening `$` is not whitespace.
3. The character before the closing `$` is not whitespace and not a backslash.
4. The character after the closing `$` is not a letter or a digit.
5. No newline appears between them.

Rule 4 is what saves currency: in `costs $100 and $200 total`, the candidate closing `$`
is followed by `2`, so no span is recognised.
Rule 5 is what prevents pairing across a line or a paragraph boundary.
Rule 1 handles `\$`.

`$$…$$` uses the same rules with a doubled delimiter and is matched **before** `$…$`.

`` `\(…\)` `` has no ambiguity — the delimiters are unambiguous — so it needs only the
no-newline constraint.

### The body rule, and why it is not optional

A sixth constraint governs what may appear *between* the delimiters, and getting it wrong
silently loses real math. The body may contain any character except a bare `$`, but a
backslash-escaped `\$` **is** allowed:

```text
body := ( [^$\n\\] | \\. )+?
```

The obvious simpler form — exclude `$` from the body entirely — fails on legitimate
mathematics about money, which is exactly the content where dollar ambiguity is worst.

flowmark's own reference document already contains the hard case, in
`tests/testdocs/testdoc.orig.md`:

```text
… they would be paying $\$0.55116 \times \$0.80$ per share, or $0.44093 per share.
And $\$420K \div 0.44093$ is $952{,}532$ shares.
```

Three true math spans, two currency amounts, escaped dollars inside the math. Tested
against both candidate bodies:

| Body rule | True spans found | Currency wrongly captured |
| --- | --- | --- |
| exclude `$` entirely | 1 of 3 | none |
| allow `\$`, forbid bare `$` | **3 of 3** | **none** |

The forbid-bare-`$` half is what protects the currency: starting at `$420K`, the body can
run forward but cannot cross the next `$`, and that `$` is preceded by a space, so rule 3
rejects it and the whole candidate fails. This line should be a named test case, since it
is the sharpest discriminator available and it came from real content rather than
invention.

### On false positives

Worth stating explicitly, because it changes how risky this work is: under this design a
false positive is **cheap**. The only consequence of wrongly deciding a run of text is
math is that it becomes one unbreakable word, so a line may overflow the wrap column. No
character changes. A false *negative*, by contrast, corrupts content. The asymmetry
argues for erring toward recognition — but not without limit, since a long false span
would produce a badly overflowing line. If practice shows this happening, the cheapest
mitigation is a maximum recognised span length; not needed until measured.

### Deliberately out of scope

`$ a + b $` (whitespace immediately inside the delimiters) is **not** math under rule 2,
and neither Pandoc nor GitHub renders it as math.
It currently gets an injected `\+` when it wraps.
This spec leaves that behaviour alone and records it as a decided boundary: it is prose
containing dollar signs, and the escape is correct for prose.
Widening rule 2 to capture it would start capturing prose that mentions prices.

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

### Python reference

**Defect M1, span splitting** — `src/flowmark/linewrapping/atomic_patterns.py`. Add three
`AtomicPattern` entries and place them in `ATOMIC_PATTERNS` with `$$` ahead of `$`.
Ordering against `INLINE_CODE_SPAN`: **keep code spans first.** Putting code spans first
keeps today's GitLab behaviour, where the `$` glue happens in `iter_atomic_words`; putting
math first would make `` $`…`$ `` a single math span. Because both constructs receive the
same treatment, the two readings emit identical bytes, so the choice is behavioural
no-op and the existing order wins on risk. A test pins it.

These patterns also belong in `MARKDOWN_INLINE_PATTERNS`, since a sentence boundary
should not fire inside a formula either.

**Defect M2, escape injection** — no change needed to `markdown_escape_word`. Once a span
is one atomic word, `_md_specials_pat` cannot match it, because that pattern is anchored
to the *entire* word.
Verified by construction; pinned by a test that would fail if the atomicity regressed.

**Defect M3, typographic transforms** — `src/flowmark/typography/smartquotes.py` and
`src/flowmark/typography/ellipses.py`. These operate on text independently of wrapping,
so they need their own exclusion.
The clean approach is to route them through `iter_atomic_spans` and transform only the
non-atomic gaps, which reuses the machinery rather than adding a second notion of “don’t
touch this.”
This has a welcome side effect: it also stops smartquotes firing inside code
spans and links if it currently does, which should be checked and, if it is a change,
recorded.

**Defect M4, block collapse** — the block-level path in
`src/flowmark/linewrapping/block_heuristics.py`. A `$$` line opens an opaque region
terminated by the next `$$` line; same for `` `\[` ``/`` `\]` `` and
`` `\begin{env}` ``/`` `\end{env}` ``. The region is emitted verbatim, line structure
included. This is the block-level analogue of the inline atomic mechanism, and in the
Rust port it maps onto the existing PUA-marker passthrough rather than anything new.

Note this changes a checked-in golden: `tests/testdocs/testdoc.expected.auto.md` line 111
currently records the collapsed form `$$ L = \frac{1}{2} \rho v^2 S C_L $$` as expected
output for a three-line input block. The corruption is baked into the test suite, so the
golden must be regenerated as part of the fix and that diff is evidence the fix works,
not a regression.

### A math span and a code span are the same thing here

Worth stating, because it is the justification for the whole design being three regexes
rather than a subsystem. The two constructs differ in **recognition** and agree in
**treatment**.

Recognition is where the difficulty lives. A code span self-delimits: N backticks open,
the next run of N closes, purely local and unambiguous. `$…$` is context-sensitive and
collides with currency, shell variables and unmatched dollars, which is what the
delimiter and body rules above exist for. GitLab's `` $`…`$ `` sits on the code-span side
of that line by design, which is exactly why it is the one dollar-bearing form that
already survives flowmark today.

Treatment is the same for both: opaque interior, atomic for wrapping, exempt from
escaping and from typographic transforms. Three qualifications:

1. **Block siblings differ.** A code fence is already opaque; math's block forms are not
   fenced and collapse (M4). That work has no code-span analogue.
2. **The stakes of splitting differ.** Splitting a code span is semantically harmless in
   CommonMark, where line endings become spaces; splitting math breaks renderers that
   require single-line input, and breaks `grep`. flowmark already meets the stronger bar
   for code spans, so this changes nothing in practice.
3. **Byte-exactness differs, and math should be the stricter one.** Measured: flowmark
   does not preserve a code span's interior byte-for-byte — `` `a    b` `` becomes
   `` `a b` `` and `` `  a  ` `` becomes `` ` a ` ``. CommonMark converts line endings to
   spaces and strips one leading/trailing pair, but internal runs are significant, so
   this appears incidental rather than intended: it falls out of the paragraph-level
   `\s+` normalization running before atomic protection, and no test pins it. Math spans
   in this spec are specified byte-exact, which is stricter. That costs nothing — a span
   emitted verbatim as a single token is byte-exact by default; the collapse only happens
   because the interior currently flows through the normalizer first.

Point 3 is a candidate separate issue against code spans, adjacent to #58. It is not in
scope here.

### How the port is *forced* to follow

This is the part that makes the work durable rather than a one-off, and it uses
machinery that already exists in `flowmark-rs`:

1. **`admin/port-coverage-mapping/`** holds `python-tests.yaml` (440 entries),
   `rust-tests.yaml` (668), and `test-mapping.yaml` (440). Regenerating after new Python
   tests land lists each new test with `status: missing`.
2. **`python/tests/test_smoke.py::TestMappingCompleteness::test_no_unmapped_entries`**
   fails while any entry is `missing`. It is described in-repo as “the primary TDD
   target.” So every new Python math test becomes a failing test in the Rust repo until
   an equivalent Rust test exists.
3. **`TestDiscoveryCounts`** asserts the three counts as literals, so the counts must be
   bumped deliberately — a new test cannot slip in unnoticed.
4. **`tests/tryscript/fixtures/content/`** is mirrored between the repos and is
   currently byte-identical except for `comprehensive.md`. The new `math.md` is copied
   across; the tryscript that consumes it is mirrored too, and the goldens must match.
5. **`scripts/corpus-parity-check.sh`** runs both binaries over a corpus and requires
   zero differences, against the Python version pinned in `Cargo.toml`
   `[package.metadata.parity]`. **With a caveat worth knowing before relying on it:**
   its default corpus is `attic/test-docs`, 623 real-world files that are not checked in
   (`attic/` is gitignored) and whose provenance is not recorded anywhere in either
   repository. The port-sync playbook documents the fallback — substitute a
   repo-Markdown spot-check and say so — and two sync artifacts show that fallback being
   taken, against 60 files on 2026-05-28 and a repo-Markdown spot-check on 2026-05-30.
   So this gate is honest about degrading but can run at roughly a tenth of its intended
   scale depending on whose machine it runs on. For math specifically the checked-in
   `math.md` corpus covers the cases that matter, so nothing here depends on
   `attic/test-docs` being present; treat a green corpus-parity run as confirmation
   rather than as the primary evidence.

So the answer to “how does the Rust port get the same coverage” is: it already has an
enforcement gate, and this work only has to feed it.
No new cross-repo infrastructure is needed.
The one gap worth noting is that fixture mirroring is manual today — worth a follow-up
issue, but not a blocker.

## Test Architecture

### The corpus document

`tests/tryscript/fixtures/content/math.md`, replacing the dead two-construct stub, laid
out in sections so a failure names itself:

- **Part A — inline forms**: one section per syntax, each containing a *short* instance
  and a *long* instance with enough filler to force a wrap boundary inside the span.
  The long instances are what reproduce M1 and M2; the current fixture has
  neither.
- **Part B — block forms**: one section per syntax, including multi-line interiors and
  the MyST label variant.
- **Part C — interiors that collide with Markdown**: formulas containing `_`, `*`, `#`,
  `>`, `+`, `-`, `N.`, `'`, `"`, `...`, `--`, and backslashes.
  These are the ones that reveal M2 and M3.
- **Part D — dollars that are not math**: currency, escaped, shell variables, unmatched,
  cross-paragraph, in code spans and fences, and `$a+b$5`.
- **Part E — malformed and ambiguous**: unclosed spans, mismatched `$`/`$$`, a `$$`
  opener with no closer, whitespace-padded delimiters, and nested-looking delimiters.
  These exist to prove flowmark *degrades safely* rather than to prove it parses them.

Part E deserves an explicit note in the document itself: these inputs have no correct
rendering in any dialect, so the requirement is only that flowmark not make them worse
and not crash.

### How it is exercised

- **Golden CLI test**: add `math.md` to `tests/tryscript/formatting.tryscript.md`
  alongside the existing `comprehensive.md` cases, so the full formatted output is a
  checked-in golden. This is the step that would have caught #70.
- **Idempotency**: add it to the `auto-mode.tryscript.md` idempotency check.
- **Unit tests**: new `tests/test_math.py`, one test per defect class plus one per
  delimiter-rule clause, asserting properties rather than golden text — no newline
  inside a span, non-whitespace content preserved, no character added.
  Property assertions survive legitimate reflow changes; goldens catch everything else.
- **Content-integrity helper**: the property “non-whitespace characters are unchanged”
  is the sharpest single check for this class of bug and is worth a small shared test
  helper, since every math test wants it.


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
`attic/` is gitignored, so the corpus is not checked in, and **no document in either
repository records what those files are, where they came from, or how to rebuild the
set.** Seven mentions exist across both repos; all of them are either the default path,
the file count, the word "curated", or instructions for working around its absence.

The port-sync playbook documents the fallback honestly — substitute a repo-Markdown
spot-check and say so — and two sync artifacts show it being taken: 60 tracked files on
2026-05-28, a repo-Markdown spot-check on 2026-05-30. So the gate degrades visibly rather
than silently, but at roughly a tenth of its intended scale, and only one machine can run
it at full strength.

**Action:** record the provenance, then either check in a redistributable subset or
document the reconstruction procedure. Tracked separately; it blocks nothing here, because
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


## Phases

Sequenced so the mechanism is proven on the smallest fully-measured surface first.

### Phase 1 — Track A corpus and red tests (`jlevy/flowmark`)

- [x] Replace `tests/tryscript/fixtures/content/math.md` with Parts A–E.
- [ ] Add `tests/test_math.py` with property assertions per defect class.
- [ ] Wire the fixture into `formatting.tryscript.md` and the idempotency check.
- [ ] Record the failing goldens and confirm the red state matches the baseline.

Baseline measured against flowmark 0.7.3: **19 defect instances** across the four math
classes — 13 sections whose non-whitespace content changes (A2–A4, C1–C5, C7, C8–C9, E5,
E7) and 6 whose display block collapses (B1–B4, B7, E3). Everything else passes today and
is regression cover: GitLab and MyST inline forms, both fenced block forms, all twelve
Part D non-math dollar cases.

### Phase 2 — Track A fixes (`jlevy/flowmark`)

- [ ] M5 first: stop normalising inside atomic spans, so code spans become byte-exact.
      This is the shared code path; math inherits it.
- [ ] M3: route smartquotes and ellipses through `iter_atomic_spans`.
- [ ] M1: add the three inline math patterns; confirm M2 falls out.
- [ ] M4: make `$$`, `` `\[…\]` `` and `` `\begin{}` `` opaque deliberately.
- [ ] Regenerate goldens, including `testdoc.expected.auto.md`, whose line 111 currently
      records the collapsed `$$` form as expected output.
- [ ] Changelog: output changes for math-bearing and code-span-bearing documents.

### Phase 3 — Track A port and parity (`jlevy/flowmark-rs`)

- [ ] Mirror `math.md` and the tryscript changes.
- [ ] Port the fixes to `atomic_patterns.rs`, `filling.rs`, and typography.
- [ ] Regenerate `admin/port-coverage-mapping/*.yaml`; bump the counts in
      `python/tests/test_smoke.py`; drive `test_no_unmapped_entries` back to zero.
- [ ] Run `scripts/corpus-parity-check.sh`, recording which corpus it ran against.

### Phase 4 — Track B P0 rows: real data loss

- [ ] Block-level opaque passthrough reusing the Phase 2 mechanism.
- [ ] Rows 1–5: multiline tables, Obsidian callouts, `:::` containers, `+++`
      frontmatter, definition lists.
- [ ] Extend the corpus with a `preservation.md` fixture on the same Part A–E shape.

### Phase 5 — Track B P1 and P2 rows, goldens and parity

- [ ] Rows 7–10 and 12.
- [ ] Rare-syntaxes end-to-end goldens; Rust porting notes; regenerate.


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
documents containing math, and — via M5 — for documents containing code spans with
internal multiple spaces. Both are one-time reflows and both are the fix. Documents with
neither must be byte-identical, which the corpus parity machinery can demonstrate.

## Outstanding Questions

- [x] Pattern ordering against `INLINE_CODE_SPAN` — **resolved: keep code spans first.**
      Treatment is identical, so the two readings of `` $`…`$ `` emit identical bytes;
      the existing order wins on risk. A test pins it.
- [ ] M5 fix placement: exclude atomic spans from the paragraph-level whitespace
      normalisation, or protect them before it runs? The second is likely cleaner but
      touches the wrapping entry point.
- [ ] Does fixing M5 change any existing golden? Expected yes for any fixture with
      multiple spaces inside a code span; needs a survey before Phase 2.
- [ ] `\begin{}…\end{}` — restrict to a known environment list, or accept any
      `\begin{word}`? Accepting any matches preserve-don't-parse.
- [ ] Fixture mirroring between the repos is manual. Sync script, or accept the step?

## Issue Disposition

- Closes [#70](https://github.com/jlevy/flowmark/issues/70) (Track A, M1–M2).
- Closes [#62](https://github.com/jlevy/flowmark/issues/62) across both tracks. Its
  "already robustly safe" list needs the `$…$` interior entry corrected.
- Overlaps [#58](https://github.com/jlevy/flowmark/issues/58): M5 shares its area but is
  a distinct defect (whitespace normalisation, not backtick mis-pairing).
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
