# Plan Spec: Math and Dollar-Sign Syntax Preservation

## Terminology

- **math span** — an inline run of mathematics with its delimiters, e.g. `` `$a + b$` ``
  or `` `\(a + b\)` ``. A span lives inside a paragraph and, in every dialect surveyed,
  never contains a newline in the source.
- **math block** — a display-mathematics region occupying whole lines, e.g. a `$$` pair
  on its own lines, `` `\[ … \]` ``, or a `` `\begin{equation}` `` environment.
- **atomic** — flowmark’s existing wrapping guarantee: a construct is one indivisible
  word, so a wrap boundary moves it whole to the next line rather than splitting it.
  Implemented by `AtomicPattern` in `src/flowmark/linewrapping/atomic_patterns.py`.
- **opaque** — the block-level equivalent: the region round-trips verbatim, line
  structure included, and is never reflowed.
- **preserve** vs **parse** — this spec never asks flowmark to *understand* LaTeX. It
  asks flowmark to recognise the extent of a construct and leave its interior alone.

## Purpose

Make flowmark safe to run on Markdown containing mathematics, in any of the widely used
notations, so that math-bearing documents no longer have to be excluded from formatting.

The bar is the one flowmark already sets for itself: it is designed to be “safe to run
automatically on save or at any stage of a document pipeline.”
A formatter that silently edits the interior of a formula does not meet that bar.
This spec treats **content preservation as a correctness property**, not a formatting
preference.

Two goals, in priority order:

1. **Never corrupt.** No math syntax in common use may have its characters changed, its
   delimiters separated, or a newline introduced inside an inline span.
2. **Never false-positive.** Ordinary prose uses of `$` — currency, shell variables,
   escaped dollars, unmatched dollars — must not be captured as math and must keep
   working exactly as they do today.

Goal 2 is what makes this non-trivial.
A naive `$…$` pattern would break every price list in the corpus, which is a worse
regression than the bug it fixes.

## Background

### The existing record

Three issues already circle this area:

- [#70](https://github.com/jlevy/flowmark/issues/70) — inline `$…$` is split by wrapping
  and the fragment that lands at the start of the new line is escaped, so the LaTeX
  changes. Filed against both ports; identical output from each.
- [#62](https://github.com/jlevy/flowmark/issues/62) — the broader “preserve
  uncommon-but-real constructs verbatim” ledger.
  Lists `` `\[…\]` ``/`$$…$$` block math as P1 item 6 and `` `\(…\)` `` inline as P2
  item 12. It also lists “the interior of `$…$` inline math” under *already robustly
  safe*, which #70 shows is wrong.
- [#67](https://github.com/jlevy/flowmark/issues/67) — GitLab Flavored Markdown support,
  which includes GitLab’s two math forms.

This spec supersedes the math rows of #62 and subsumes #70. It does not address #62’s
non-math rows (callouts, fenced divs, grid tables, definition lists).

### What was measured

A 39-case battery was run against **flowmark 0.7.3 (Python)** and **flowmark-rs 0.3.2
(Rust)** with `--auto`. Both ports produced identical classifications, confirming shared
behaviour rather than a port regression.
Sixteen cases corrupt content.
The failures fall into four mechanisms; the third and fourth are not in #70, and the
third is in neither issue.

**Class 1 — span splitting.** `$…$`, one-line `$$…$$`, and `` `\(…\)` `` are absent from
`ATOMIC_PATTERNS`, so a wrap boundary falling inside one splits it.
A newline inside a formula defeats `grep` and breaks renderers that require inline math
to stay on one line.

**Class 2 — escape injection.** Once a span is split, the fragment beginning the new
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

**Class 3 — typographic transforms inside math.** This one needs no wrap boundary at
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
wrapping, fixing Classes 1 and 2 will **not** fix them; they need their own guard in
`src/flowmark/typography/`.

**Class 4 — block collapse.** Every display form that is not a fenced code block is
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
| `$…$` | inline | **corrupt** (classes 1, 2, 3) |
| `$$…$$` on one line | inline display | **corrupt** (classes 1, 2) |
| `$$…$$` across lines | block display | **corrupt** (class 4) |
| `\(…\)` | inline | **corrupt** (classes 1, 2) |
| `\[…\]` | block | **corrupt** (class 4) |
| `\begin{equation}…\end{equation}` | block | **corrupt** (class 4) |
| ` ```math ` fence | block (GitHub, GitLab) | safe — code fence |
| `` $`…`$ `` | inline (GitLab) | safe — code span is already atomic |
| ` ```{math} ` | block (MyST) | safe — code fence |
| `` {math}`…` `` | inline (MyST) | safe — code span is already atomic |
| `$$…$$ (label)` | labelled block (MyST) | **corrupt** (class 4) |

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

## Summary of Task

1. Define the complete desired behaviour for every math syntax in common use, and for
   every ordinary use of `$` that must not be mistaken for math.
2. Replace `math.md` with a comprehensive test document covering both, structured in
   sections, including a section of deliberately malformed and ambiguous forms.
3. Wire it into the tryscript golden tests so it is actually exercised, and add unit
   tests that reproduce each defect.
   Both are written first and must fail (TDD).
4. Fix the three defect classes in the Python reference.
5. Carry the same corpus and the same coverage into the Rust port, using the existing
   port-coverage mapping so the parity gate enforces it.

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

## Backward Compatibility

**BACKWARD COMPATIBILITY REQUIREMENTS:**

- **Code types, methods, and function signatures**: KEEP DEPRECATED. `ATOMIC_PATTERNS`
  and `MARKDOWN_INLINE_PATTERNS` are part of the public inline API
  (`plan-2026-05-26-public-inline-api.md`). New patterns are additive; the existing
  names, ordering semantics, and `AtomicPattern` shape do not change.
  Consumers that enumerate `ATOMIC_PATTERNS` will see new members, which is the intended
  extension point.
- **API compatibility for libraries**: SUPPORT BOTH. Adding math to the default pattern
  tuple changes what `iter_atomic_spans` returns for math-bearing input.
  That is the point of the change, and it is strictly more protective, but it is a
  behavioural change for downstream consumers and belongs in the changelog.
- **File format compatibility**: N/A.
- **Server API compatibility**: N/A.
- **Database schema compatibility**: N/A.

**Output compatibility** is the one that matters here and deserves stating plainly: this
change alters flowmark’s output for documents containing math.
Documents already formatted will re-wrap where a math span previously split.
That is a one-time reflow, it is the fix, and it must be called out in the release
notes. Documents with no math must be byte-identical — which the existing corpus parity
machinery can prove.

## Stage 1: Planning Stage

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

### Acceptance criteria

1. Round-tripping the new `math.md` through `flowmark --auto` changes no non-whitespace
   character anywhere in the document.
2. No inline math span in the output contains a newline.
3. The output is idempotent — a second pass is a no-op — matching the existing
   `auto-mode.tryscript.md` idempotency check.
4. Every case in the “must never be captured” list formats exactly as it does today.
5. Both ports produce byte-identical output on the corpus.

### Explicitly not in scope

- Parsing, validating, or rendering LaTeX.
- Normalising between dialects (`\(…\)` is never rewritten to `$…$`).
- Re-wrapping or pretty-printing the *interior* of math.
- The non-math rows of #62 (callouts, fenced divs, grid tables, definition lists, TOML
  frontmatter). Those share the mechanism but not this spec.
- A `--no-math` opt-out flag.
  Preservation is correctness; there is no reason to want it off.
  Revisit only if the delimiter rule proves to false-positive in practice.

## Stage 2: Architecture Stage

### Python reference

**Class 1, span splitting** — `src/flowmark/linewrapping/atomic_patterns.py`. Add three
`AtomicPattern` entries and place them in `ATOMIC_PATTERNS` with `$$` ahead of `$`.
Ordering against `INLINE_CODE_SPAN`: **keep code spans first.** Putting code spans first
keeps today's GitLab behaviour, where the `$` glue happens in `iter_atomic_words`; putting
math first would make `` $`…`$ `` a single math span. Because both constructs receive the
same treatment, the two readings emit identical bytes, so the choice is behavioural
no-op and the existing order wins on risk. A test pins it.

These patterns also belong in `MARKDOWN_INLINE_PATTERNS`, since a sentence boundary
should not fire inside a formula either.

**Class 2, escape injection** — no change needed to `markdown_escape_word`. Once a span
is one atomic word, `_md_specials_pat` cannot match it, because that pattern is anchored
to the *entire* word.
Verified by construction; pinned by a test that would fail if the atomicity regressed.

**Class 3, typographic transforms** — `src/flowmark/typography/smartquotes.py` and
`src/flowmark/typography/ellipses.py`. These operate on text independently of wrapping,
so they need their own exclusion.
The clean approach is to route them through `iter_atomic_spans` and transform only the
non-atomic gaps, which reuses the machinery rather than adding a second notion of “don’t
touch this.”
This has a welcome side effect: it also stops smartquotes firing inside code
spans and links if it currently does, which should be checked and, if it is a change,
recorded.

**Class 4, block collapse** — the block-level path in
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
   fenced and collapse (Class 4). That work has no code-span analogue.
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

### Rust port

The port mirrors the same three sites:

- `src/wrapping/atomic_patterns.rs` — the pattern list (#70 identifies this file).
- `src/formatter/filling.rs` — the pre-parse PUA-marker passthrough for opaque blocks,
  the mechanism #62 documents as `COMRAK-WORKAROUND1–12`.
- The typography module, for the Class 3 guard.

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
   `[package.metadata.parity]`.

So the answer to “how does the Rust port get the same coverage” is: it already has an
enforcement gate, and this work only has to feed it.
No new cross-repo infrastructure is needed.
The one gap worth noting is that fixture mirroring is manual today — worth a follow-up
issue, but not a blocker.

## Stage 3: Test Architecture

The user-facing requirement is a comprehensive test document covering every variation,
including the broken ones, used to reproduce all the bugs and drive TDD.

### The corpus document

`tests/tryscript/fixtures/content/math.md`, replacing the dead two-construct stub, laid
out in sections so a failure names itself:

- **Part A — inline forms**: one section per syntax, each containing a *short* instance
  and a *long* instance with enough filler to force a wrap boundary inside the span.
  The long instances are what reproduce Classes 1 and 2; the current fixture has
  neither.
- **Part B — block forms**: one section per syntax, including multi-line interiors and
  the MyST label variant.
- **Part C — interiors that collide with Markdown**: formulas containing `_`, `*`, `#`,
  `>`, `+`, `-`, `N.`, `'`, `"`, `...`, `--`, and backslashes.
  These are the ones that reveal Classes 2 and 3.
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

### TDD sequence

Write Part A–E and the tests first.
Expected initial state, from the measured battery: the twelve corrupting cases fail, the
safe ones pass and thereby become regression tests.
Then fix Class 3, then Class 1 (which resolves Class 2), then the blocks, re-running
after each so the fix that closes each failure is identifiable.

## Phases

Three phases, split where the work genuinely changes repository and character.

### Phase 1 — Corpus and red tests (`jlevy/flowmark`)

- [x] Replace `tests/tryscript/fixtures/content/math.md` with Parts A–E.
- [ ] Add `tests/test_math.py` with property-based assertions per defect class.
- [ ] Wire the fixture into `formatting.tryscript.md` and the idempotency check.
- [ ] Record the failing goldens and confirm the red state matches the baseline below.

The corpus is written and its baseline measured. Against flowmark 0.7.3 it reproduces
**19 defect instances** across all four classes: 13 sections whose non-whitespace content
changes (A2–A4 splitting and escape injection; C1–C5 and C7 escape injection; C8–C9
typographic rewriting; E5 and E7 in the malformed set) and 6 whose display block is
collapsed onto one line (B1–B4, B7, E3). Everything else passes today and is regression
cover: the GitLab and MyST inline forms, both fenced block forms, and all twelve Part D
non-math dollar cases.

### Phase 2 — Python fixes

- [ ] Class 3: route smartquotes and ellipses through `iter_atomic_spans`.
- [ ] Class 1: add the three inline patterns; confirm Class 2 falls out.
- [ ] Blocks: make `$$`, `` `\[…\]` ``, and `` `\begin{}` `` opaque deliberately.
- [ ] Regenerate goldens; confirm non-math fixtures are byte-identical.
- [ ] Changelog entry noting the output change for math-bearing documents.

### Phase 3 — Rust port and parity (`jlevy/flowmark-rs`)

- [ ] Mirror `math.md` and the tryscript changes.
- [ ] Port the three fixes to `atomic_patterns.rs`, `filling.rs`, and typography.
- [ ] Regenerate `admin/port-coverage-mapping/*.yaml`; bump the counts in
  `python/tests/test_smoke.py`; drive `test_no_unmapped_entries` back to zero.
- [ ] Run `scripts/corpus-parity-check.sh` for byte parity.

## Outstanding Questions

- [x] Pattern ordering against `INLINE_CODE_SPAN` — **resolved: keep code spans first.**
  A math span and a code span get identical treatment (see below), so the two readings of
  `` $`…`$ `` produce identical bytes. Code-span-first is current behaviour and already
  correct, so it is the zero-risk choice. A test still pins it.
- [ ] Should the typography guard’s side effect (no smartquotes inside code spans and
  links, if that is a change) ship in this spec or be split out?
- [ ] Fixture mirroring between the repos is manual.
  File a follow-up for a sync script, or accept the manual step?
- [ ] `\begin{}…\end{}` — restrict to a known environment list (`equation`, `align`,
  `gather`, `matrix`, …) or accept any `\begin{word}`? Accepting any is simpler and
  matches the preserve-don’t-parse principle.

## An Adjacent Bug Found While Writing This

Formatting this spec corrupted it.
Three table cells written as code spans containing backticks — the fenced-block info
strings and the GitLab dollar-backtick form — came back with their delimiters re-paired
and the content changed.
That is [#58](https://github.com/jlevy/flowmark/issues/58), escaped-backtick code spans
mis-pairing later backticks, reproduced incidentally on a table row.

It is **not** in scope here; it is recorded because it is the same failure shape as the
math bug (a construct the wrapper does not model, silently rewritten) and because the
cells in this document had to be reworded to survive their own formatter.
Part C of the corpus should include nested-backtick spans so the shape is at least
covered by a test, even if the fix ships separately.

## Issue Disposition

- Closes [#70](https://github.com/jlevy/flowmark/issues/70).
- Closes the math rows of [#62](https://github.com/jlevy/flowmark/issues/62) (P1 item 6,
  P2 item 12); the issue stays open for its remaining rows.
  Its “already robustly safe” list needs the `$…$` entry corrected.
- Contributes the two math forms to [#67](https://github.com/jlevy/flowmark/issues/67).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
