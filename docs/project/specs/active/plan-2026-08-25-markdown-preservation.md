# Plan Spec: Lossless Markdown Preservation

**Date:** 2026-08-25

**Status:** Active. Math is the first implementation target.

**Trackers:** Epic `fm-7vtx`; shared foundation `fm-o5vk`; math behavior `fm-9jtc`;
Python implementation `fm-ar24`; Rust math port `fm-wkve`; inline code `fm-zgte`.

**Cross-repository contract:**
[Language-Neutral Flowmark Conformance Corpus](../../architecture/current/language-neutral-conformance-corpus.md).

## Decision summary

Flowmark will protect syntax it cannot safely model before a Markdown parser can reinterpret
it. A deterministic source scanner identifies typed regions, stores their normalized source
slices in a side table, and presents collision-safe tokens to the parser and formatter.
Transforms and wrapping operate only on unprotected text. Restoration is exact and fails
closed.

The design makes these decisions:

- Math is highest priority and lands end to end in Python and Rust before the other
  preservation work.
- The default recognizer is preservation-biased. It accepts the broad union of common math
  forms without dialect configuration, including intraword, whitespace-padded, and
  soft-newline dollar math.
- Protected math and extension blocks preserve their normalized UTF-8 source slices
  exactly. Inline code preserves its authored source exactly as a formatter policy.
- Recognition is a portable state machine over normalized UTF-8 bytes, not a Python regex
  contract and not a parser-library feature.
- One upstream manifest and exact golden corpus define shared behavior. The Rust port reads
  it through `repos/flowmark`; it does not translate Python tests or run Python in CI.
- Stable `change_id` and case IDs turn each upstream behavior change into an explicit Rust
  porting queue.

## Purpose

Flowmark parses Markdown, transforms an AST, and re-emits source with clean line breaks.
That works only when the parser models a construct faithfully. Syntax the parser treats as
ordinary prose can be split, escaped, normalized, or reinterpreted before the formatter has
a chance to protect it.

The product promise is therefore broader than support for one Markdown flavor:

> Flowmark should safely format documents that mix common Markdown dialects with little or
> no configuration. When it cannot model a construct, it preserves that construct instead
> of guessing at its semantics.

This plan has three tracks:

- **Track A — mathematics:** inline and display forms used by GitHub, GitLab, MyST,
  Pandoc, Quarto, Obsidian, MathJax, and raw LaTeX. This is the critical path.
- **Track C — inline code:** source fidelity for arbitrary backtick delimiters and authored
  whitespace. It uses the same protection infrastructure after math.
- **Track B — other extensions:** the verified ledger from
  [#62](https://github.com/jlevy/flowmark/issues/62), beginning with the data-loss cases.

The order is the shared conformance gate, math in both ports, inline code in both ports,
then the remaining extension registry. Code-span fixes do not block math: the current
code-span path runs after parsing and cannot protect math from parser reinterpretation.

## Goals

- Preserve recognized math and opaque extension regions exactly after documented input
  normalization.
- Keep inline protected regions atomic for wrapping and exempt from typography, escaping,
  cleanup, and whitespace normalization.
- Preserve display-region line structure, container prefixes, labels, and attributes.
- Support common dialect forms by default; configuration is reserved for genuinely custom
  delimiters.
- Use one scanner model and one shared black-box corpus in Python and Rust.
- Keep recognition and formatting linear in input size, including malformed input.
- Fail without partial output or file mutation if internal protection/restoration
  invariants are violated.

## Non-goals

- Flowmark does not evaluate TeX, validate equations, or choose a renderer.
- It does not resolve semantic ambiguity between currency, shell variables, and dollar
  math. Conservative atomic treatment is acceptable because it preserves source.
- It does not require Marko and comrak to build identical ASTs.
- It does not expose scanner internals as a new public API in this change.
- It does not replace the parser for Markdown constructs that already round-trip safely.
- It does not promise to repair malformed Markdown. Malformed cases must remain safe,
  deterministic, and idempotent according to committed goldens.

## Terminology

- **Protected region:** a non-overlapping source range that transformations may not edit.
- **Inline region:** a protected range inside paragraph content. It is atomic for wrapping.
- **Opaque block:** a protected range occupying one or more physical lines. Its complete
  normalized source slice is restored.
- **Container view:** a logical line after recognizing blockquote and list prefixes while
  retaining the raw source range.
- **Recognition:** finding a safe boundary. Recognition does not imply understanding or
  validating the body.
- **Treatment:** preserving and restoring a recognized range.
- **Normalized source:** decoded text after the input contract below has handled BOM and
  line endings.

## Normative behavior

### Input and output normalization

The two implementations must share these boundary rules before byte-exact preservation can
have one meaning:

1. Input is UTF-8. An optional leading UTF-8 BOM is recorded, removed before parsing, and
   restored exactly once at output.
2. CRLF and lone CR are normalized to LF. The terminal LF run is then canonicalized to
   exactly one LF before scanning: add one when missing and collapse multiple terminal LFs
   to one. Protected slices are exact slices of this fully normalized buffer, so output
   finalization cannot silently change a protected region at end of file.
3. A successful formatted document therefore ends with exactly one LF, including empty
   input and input that lacked a final newline.
4. Invalid UTF-8 is a CLI error. Stdout is empty, in-place files are not changed, and the
   exit behavior is pinned by shared conformance cases.
5. Scanner coordinates are half-open UTF-8 byte offsets into the normalized buffer.
   Python must not expose code-point indices as if they were byte offsets. Wrapping width
   remains the existing count of Unicode scalar values in both ports; it is not terminal
   display width.

The CLI and the Markdown path through `reformat_text()` do not implicitly call
`textwrap.dedent()` or globally strip the document before scanning. Those operations can
turn an indented code block into prose or remove significant whitespace from a protected
region at a document boundary. `fill_markdown(dedent_input=True)` remains an explicit
docstring convenience; when requested, dedenting occurs before the normalization above,
and the preservation contract applies to the resulting buffer. Ordinary parsing and
rendering may still normalize unprotected leading blank lines according to the committed
goldens.

These rules are tested with stdin and files. The test runner itself performs no newline or
encoding normalization.

### Protected-region contract

For every recognized protected region:

- The emitted UTF-8 bytes equal the region's normalized source slice exactly.
- Delimiters, indentation, container markers, labels, attributes, tabs, internal spaces,
  and existing line endings are part of the slice.
- Smart quotes, ellipses, cleanups, escaping, sentence splitting, and whitespace
  normalization do not inspect or mutate its body.
- An inline region is one wrapping unit. It may move as a whole; it is never split by a new
  wrap boundary. Existing physical line endings inside a permissive multiline inline form
  remain where authored.
- A protected token is never separated from adjacent source text when there was no
  whitespace at that boundary. Intraword forms such as `H$_2$O` remain one wrapping
  cluster.
- An opaque block retains its physical line structure and is not collapsed into a
  paragraph.

Surrounding prose may be reformatted normally. Exact committed output, rather than a
whitespace-stripped helper, determines whether that interaction is correct.

### Inline-code policy

Inline code uses source preservation, not renderer canonicalization. Once a valid code span
is bounded, Flowmark emits the authored delimiter run and body exactly. This intentionally
preserves source forms that render equivalently under CommonMark, including wider-than-
necessary delimiters and authored spaces.

This policy is safer for a source formatter, avoids a second-pass change, and gives math
and code one treatment contract while retaining separate recognition rules.

### Preservation-biased ambiguity

False negatives can change syntax bytes. False positives generally inhibit a wrap or
typographic cleanup. Flowmark therefore recognizes a broad balanced dollar form by
default.

A pair such as `$100 and $200` or `$HOME and $PATH` may be treated atomically. Its bytes
must remain unchanged even if it is not math. The accepted tradeoff is a possible overlong
line, not content corruption. There is no strict-dollar option in this plan; one can be
added later without weakening the default.

## Measured defects

The initial batteries used Flowmark Python 0.7.3 and flowmark-rs 0.3.2 with `--auto`.
The two ports showed the same defect classes, so these are upstream behavior gaps rather
than Rust-only regressions. The batteries are seed evidence; the shared corpus defined
below is the lasting contract.

| ID | Construct | Current failure |
| --- | --- | --- |
| M1 | Inline `$…$`, `$$…$$`, and `\(…\)` | A width boundary splits the formula. |
| M2 | Split inline math | A fragment beginning with `+`, `-`, `>`, `#`, or a numeral marker receives a new backslash escape. |
| M3 | Math containing prose-like punctuation or Markdown | Smart quotes, ellipses, emphasis, and other parser transforms alter the body even on short lines. |
| M4 | Display math and LaTeX environments | Multiple source lines collapse into one line. |
| C1 | Code spans whose body contains backticks | The renderer shortens the delimiter and can close the span early. |
| C2 | Code spans containing spaces or tabs | Paragraph whitespace normalization changes the body and can be non-idempotent. |

M3 proves that post-parse atomic patterns are insufficient. For example, a parser can turn
the underscores in `\text{__init__}` into emphasis nodes before wrapping or typography
runs. The original source is unrecoverable at that point.

The topic fixtures
`tests/tryscript/fixtures/content/math.md` and
`tests/tryscript/fixtures/content/code-inline.md` reproduce the interacting forms. They
were previously dead fixtures; the implementation must make them load-bearing through both
the shared manifest and tryscript integration coverage.

## Lossless protection architecture

### Pipeline

Both implementations follow the same observable stages:

```text
input bytes
  -> UTF-8/BOM/newline normalization
  -> block and inline source scan
  -> sorted typed protected regions + side table
  -> collision-safe parser bridge
  -> Markdown parse, transforms, render, and wrapping of unprotected text
  -> validated exact restoration
  -> BOM/final-newline emission
```

The scanner is a dedicated pre-parse component. Parser extensions may recognize the
scanner's synthetic tokens, but parser-specific syntax recognition is not authoritative.
This keeps Marko and comrak adapters thin and keeps the recognition algorithm portable.

### Region record

Each region record contains:

```text
index              monotonically increasing source-order integer
kind               stable type such as math_dollar_inline or code_span
start, end         half-open UTF-8 byte offsets in normalized source
source             exact normalized UTF-8 slice
form               inline or block
logical_widths     Unicode-scalar width of each physical fragment for inline forms
container          blockquote depth and list/content-column metadata when applicable
```

Records are sorted, non-overlapping, and cover only recognized regions. Outer opaque
regions own their complete range; nested syntax inside them is not emitted as independent
regions.

### Collision-safe parser bridge

Synthetic tokens use a deterministic sentinel that cannot occur in the source.

1. In one pass, find the maximum number `m` of consecutive `U+F0000` scalars immediately
   before any `U+F0001`.
2. Let `S` be `m + 1` copies of `U+F0000` followed by `U+F0001`. No suffix of a longer
   authored run can collide with it because `m` is maximal.
3. Encode region `i` as `S`, `U+F0002`, lowercase base-36 `i` without leading zeros,
   `U+F0003`, then `S`.

The sentinel search terminates for every finite input and is linear. Supplementary private-
use scalars are chosen because they are valid
UTF-8 text and inert Markdown characters; corpus cases verify that Marko and comrak carry
them unchanged. The collision case where the source already contains candidate private-use
sequences is mandatory.

The literal token length never determines wrapping. The inline lexer carries explicit
whitespace boundaries rather than rebuilding output by joining strings with spaces. Text
and tokens separated by no source whitespace form one unbreakable cluster.

A single-line inline token takes its width from the side table. For a multiline inline
token, `logical_widths` records the scalar width of every source fragment separated by an
authored LF, including any continuation container prefix inside the slice. The wrapper may
insert a new break before the token as a whole. It then emits the first fragment at the
current column, forces each authored internal LF, resets the column to the corresponding
fragment width, and measures following text from the final fragment. It may not add,
remove, or relocate an internal break. Restoration substitutes the complete source slice
only after wrapping, so the parser never gets an opportunity to reinterpret a continuation
line as a list, quote, or heading.

Typography and cleanup walkers skip tokens. Block tokens are represented as opaque block
nodes by the parser adapter so paragraph rendering cannot add or remove container
structure. Shared intraword, multiline, list, quote, and width-boundary cases constrain
both thin adapters; neither port may approximate token width with placeholder text length.

Restoration validates all invariants before producing output:

- every token index exists;
- every region is restored exactly once and in source order;
- no token is missing, duplicated, reordered, nested, or malformed; and
- no sentinel remains in the result.

An invariant failure returns a nonzero internal error with empty stdout. In-place writing
uses the existing atomic commit boundary, so the original file remains unchanged. The
formatter never emits a partial document or an internal token.

### Complexity

Delimiter scanning, sentinel selection, token replacement, and restoration are each
O(n). Environment matching uses a stack bounded by source length. No rule backtracks over
the body, recursively reparses substrings, or searches from every unmatched opener.

## Recognition model

### Global precedence

Recognition is deterministic in two stages.

First, the block scanner selects leading frontmatter and existing opaque Markdown blocks,
then registered opaque blocks beginning with display math and LaTeX environments. These
ranges are not searched for inline syntax.

Second, each inline recognizer independently proposes complete candidates in the remaining
inline scopes. A paragraph or heading is one scope. Each GFM pipe-table cell is a separate
scope, split at active unescaped structural pipes before math matching; a dollar pair or
code span may not hide a cell boundary from the Markdown parser. If a table's cell
boundaries cannot be identified deterministically, the block scanner preserves the table
as one opaque block. Arbitration repeatedly selects the candidate with the earliest start
byte and discards every candidate that overlaps it. For candidates beginning at the same
byte, this priority applies:

1. GitLab dollar-backtick math and MyST role-plus-backtick math;
2. general inline code spans;
3. unambiguous inline math delimiters and environments;
4. dollar runs; and
5. other registered extension spans.

If candidates still tie, the longest complete range wins, then a fixed stable kind name.
This leftmost-outer rule gives a dollar formula ownership of code-like text inside it and a
code span ownership of dollar-like text inside it. It also handles the GitLab composite
without changing the public `MARKDOWN_INLINE_PATTERNS` tuple or relying on regex-
alternation order.

### Escape parity

An ASCII delimiter is active when the immediately preceding run of backslashes has even
length. An odd run escapes it. The delimiter's own backslash in `\(`, `\)`, `\[`, `\]`,
`\begin`, or `\end` is not counted as a preceding escape.

Examples:

```text
\$a$       first dollar is escaped
\\$a$      first dollar is active
\\\$a$     first dollar is escaped
\\\\$a$    first dollar is active
```

The same parity rule applies to candidate closers and to escaped dollars inside a formula.

### Dollar math

Dollar recognition has no whitespace, alphanumeric-adjacency, or following-digit
restriction. This is deliberate: it includes Pandoc intraword math, MyST's optional
space-padded form, soft newlines, and narrower GitHub-style forms without configuration.

Scanning occurs independently inside each Markdown paragraph and never pairs across a
blank-line boundary. Code and higher-precedence protected ranges are skipped.

The scanner processes each active dollar run left to right with three states:

```text
NONE:
  run length >= 2 -> open DOUBLE with two dollars
  run length == 1 -> open SINGLE with one dollar

SINGLE:
  the next active dollar closes SINGLE with one dollar
  any dollars remaining in that run are processed again from NONE

DOUBLE:
  a run length >= 2 closes DOUBLE with two dollars
  a run length == 1 is body content and participates in fallback SINGLE pairing
  any dollars remaining after the closer are processed again from NONE
```

Every state transition consumes only the stated one or two dollars. Any remainder in the
same run is processed immediately in the new state; thus `$$$$` is an empty double-dollar
region. While DOUBLE is open, singleton runs are paired into fallback SINGLE candidates.
If DOUBLE later closes, its outer candidate owns them. If DOUBLE is unmatched, completed
fallback candidates survive, so an unmatched opener cannot suppress valid later math.

Only a closed candidate becomes a protected region. An unclosed candidate is left as
ordinary source. This rule makes `$a$$b$` two adjacent single-dollar regions while making
`$$a$$` one double-dollar region. Escaped dollars remain body content. Existing soft
newlines inside a closed region are preserved; a blank line terminates an unclosed inline
candidate.

The required forms include:

- `$…$` and `$$…$$`, with or without interior spaces;
- intraword forms such as `H$_2$O`, `1$a$`, and `$a$B`;
- a closer followed by a digit, adjacent spans, empty bodies, Unicode adjacency, and tabs;
- escaped dollars under one through four preceding backslashes; and
- parser-collision bodies containing underscores, emphasis, links, images, entities, HTML,
  backticks, TeX comments, straight quotes, ellipses, and block-marker text.

Balanced currency and shell-variable pairs are allowed false positives under the
preservation contract. Lone and unclosed dollars remain ordinary source and receive exact
golden coverage for safe degradation.

### Other inline math forms

- `\(…\)` pairs with the next active `\)` in the same paragraph. Interior whitespace and
  soft newlines are allowed; blank lines and unmatched openers end the candidate.
- GitLab math begins with an active dollar immediately followed by a backtick run of length
  N. It closes at the next run of exactly N backticks immediately followed by an active
  dollar. The whole composite is one region.
- MyST math begins with `{math}` immediately followed by a backtick run of length N and
  closes at the next run of exactly N. The whole role and code span are one region.
- A `\begin{name}` and matching `\end{name}` contained in a paragraph form one region.
  Environment names are nonempty raw text up to the next `}` on the same logical line;
  braces and line endings are not allowed in the name. Matching is exact and
  case-sensitive, including `*`, `@`, punctuation, and custom names.

### Inline code spans

A run of N backticks opens a code span when the next backtick run of exactly N exists in
the same paragraph. Runs of different lengths are body content. N has no implementation
limit; one-through-four regex approximations are noncompliant. Backslash does not escape a
backtick in CommonMark code-span recognition.

The complete authored slice is protected. Internal spaces, tabs, line endings, backslashes,
Markdown, HTML, entities, and typographic punctuation remain exact. An unmatched opener is
ordinary source. The corpus includes delimiters longer than four, bodies with shorter,
equal, and longer runs, all-space bodies, padded bodies, multiline bodies, adjacent spans,
and every supported block context.

### Container-aware block view

The block scanner retains raw line ranges while deriving a logical container view. It
recognizes:

- zero to three leading spaces;
- repeated blockquote markers with their optional following space;
- unordered or one-to-nine-digit ordered list markers plus their content padding; and
- continuation indentation relative to the opener's content column.

An opener records blockquote depth, list nesting, and content column. A closer is compatible
only in the same blockquote/list container at the recorded content column or a valid deeper
continuation. It cannot close across a quote or list-item boundary. The raw prefixes stay
inside the restored source slice.

The algorithm is a small container stack with CommonMark marker widths, not a top-level
regular expression. Required vectors cover top-level blocks, nested lists, nested quotes,
quotes inside lists, lists inside quotes, lazy continuations, tabs in indentation, and
delimiter-looking text in indented code.

### Display math and environment blocks

After removing the logical container prefix:

- A line containing only active `$$` opens a dollar display block. A compatible line with
  `$$` closes it. The closer may carry a MyST label in parentheses or a single attribute
  group after whitespace; the suffix is part of the protected slice.
- A line containing only active `\[` opens a bracket display block; only compatible
  `\]` closes it.
- `\begin{name}` opens an environment block. Environment openers nest. Only
  `\end{name}` matching the top stack entry closes it. Starred and custom names match
  exactly.
- Dollar and bracket blocks do not nest. Delimiter-looking text inside them is body text;
  the next compatible closer of the same type closes the block.
- A mixed or mismatched closer never pops the current block. It remains body text if a
  later valid closer completes the region.

A candidate is committed only after its legal closer is found. An unmatched opener
therefore cannot swallow trailing prose. Closed nested environments are retained as
independent candidates if an unmatched outer environment is discarded; a candidate tree
resolves outer ownership in one pass.

Fenced and indented code win before math, so math-looking delimiters inside them are never
considered. Matched block regions may contain blank lines. Every unmatched and mismatched
case has an exact, idempotent golden and an adversarial linear-time case.

## Track B: extension registry

The same scanner grows through explicit, tested rules. Built-in recognition covers the
common dialect union; users should not need to identify their Markdown flavor.

| Priority | Family | Recognition and treatment |
| --- | --- | --- |
| P0 | Pandoc multiline tables | Detect caption/header/rule structure and preserve the complete table block. |
| P0 | Obsidian callouts | Detect the first quote line `[!type]`, optional fold marker, and title; preserve the contiguous callout quote block exactly. |
| P0 | Colon containers and fenced divs | A container-content line beginning with a run of at least three colons opens; a bare run closes. Maintain a nesting stack without requiring equal run lengths. |
| P0 | TOML frontmatter | At document start after an optional BOM, `+++` pairs with `+++` exactly as YAML `---` does; preserve the complete region. |
| P0 | Definition lists | Detect term lines followed by one or more definition markers in the same container; preserve the contiguous definition-list block. |
| P1 | Pandoc grid tables | Detect compatible top/bottom border and row lines; preserve the complete table. |
| P1 | Raw multiline HTML | Apply CommonMark HTML-block boundaries, then preserve the source block rather than re-rendering it. |
| P1 | Attribute groups | Protect standalone `{.class #id …}` lines and inline attribute groups immediately following a compatible span. |
| P2 | Line blocks | Preserve contiguous container-content lines beginning with an active vertical bar and required following space. |
| P2 | MyST roles and wikilinks | Protect balanced role/backtick and double-bracket spans with explicit escape and nesting tests. |

Each registry rule defines opener, closer or extent, precedence, container compatibility,
nesting, unmatched behavior, and a case matrix before implementation. Parser support may
replace a passthrough rule only after the same shared cases prove exact or intentionally
canonical output in both ports.

Custom delimiter configuration is a later additive feature. It must register rules in the
same scanner and cannot weaken built-in protection by default.

## Language-neutral golden strategy

The architecture document linked at the top is normative for layout, manifest schema,
native runners, golden review, and Rust divergence policy. The following requirements are
specific to preservation work.

### Change map

The manifest is the porting ledger. These stable change IDs group the initial work:

| Change ID | Contract | Python tracker | Required Rust result |
| --- | --- | --- | --- |
| `FM-CONFORMANCE-001` | Shared manifest, strict runners, fixture reachability, idempotence | `fm-o5vk` | Native runner reads `repos/flowmark`; no Python runtime. |
| `FM-PRESERVE-CORE-001` | Normalization, region records, sentinel bridge, fail-closed restoration | `fm-2tto` | Same golden outputs and failure semantics. |
| `FM-MATH-INLINE-001` | Dollar, paren, GitLab, MyST, and inline environment recognition | `fm-9jtc` plus implementation beads | Zero new divergence entries. |
| `FM-MATH-BLOCK-001` | Container-aware display and environment blocks | `fm-6erm` | Zero new divergence entries. |
| `FM-CLI-OUTPUT-001` | Atomic `--output` for exactly one direct input file | `fm-9r1n` | Same routing, bytes, and multiple-input rejection. |
| `FM-CODE-SPAN-001` | Arbitrary delimiters and source-exact code spans | `fm-fa8p`, `fm-9ey6` | Same cases pass after the math port. |
| `FM-OPAQUE-P0-001` | P0 extension registry families | Track B beads under `fm-7vtx` | Port family by family against shared IDs. |

Every behavior PR adds or updates manifest cases with one of these IDs or a new stable ID.
The Rust submodule bump exposes the exact set with no separate hand-maintained test map.

### Math conformance matrix

The math suite covers these dimensions with minimal cases, deliberate pairwise
interactions, and the topic-level `math.md` document:

| Dimension | Required coverage |
| --- | --- |
| Delimiters | Single dollar, double dollar, paren, bracket, environment, GitLab dollar-backtick, MyST role and fence forms |
| Boundaries | Intraword on both sides, spaces and tabs inside, digit after closer, adjacent spans, empty and long bodies |
| Escapes | One through four backslashes at openers and closers; escaped dollars in bodies |
| Lines | Short, N-1/N/N+1 width boundaries, soft newline, blank-line boundary, display blocks, missing final newline |
| Parser collisions | Emphasis, links, images, entities, HTML, backticks, TeX comments, quotes, apostrophes, ellipses, dashes, block markers |
| Contexts | Paragraph, heading, list, blockquote, nested containers, table, link text, footnote, definition list, colon container, raw-block adjacency |
| Blocks | Labels, attributes, `align*`, nested and custom environments, mismatches, missing closers, code-block precedence |
| Unicode and I/O | Non-ASCII letters/digits/space, CJK adjacency, combining marks, tabs, LF/CRLF, BOM, stdin, output file, in-place, check, config |
| Modes | Default, semantic, smart quotes, ellipses, cleanups, auto, width zero and one |
| Adversarial | Thousands of dollar runs, deep environments, very long bodies, sentinel collisions, linear-time watchdog |

Exact expected bytes already prove protected content survived; the black-box runner does
not reimplement the scanner to assert a second "protected slice" property. Python and Rust
unit/property tests may inspect region boundaries internally, but no product promise lives
only there.

### Golden layers

- Minimal shared parity cases are the normative cross-language contract and produce
  precise failures.
- `math.md` and `code-inline.md` are shared integration inputs. Both ports consume the
  upstream files directly through the manifest and the upstream tryscript suite. The
  tryscript transcript may intentionally repeat an expected result because it validates a
  readable CLI workflow rather than the isolated conformance case.
- `tests/testdocs/testdoc.orig.md` and its mode-specific expected files remain shared
  whole-document blast-radius checks. Rust runs them through `repos/flowmark` instead of
  copying them. Representative mode pairs may also appear in the manifest for an exact
  process-level assertion.
- The pinned CommonMark documents and reviewed outputs are shared inputs for both ports.
  All 652 CommonMark 0.31.2 examples seed default-mode recognition coverage; a reviewed
  stable subset plus every preservation case exercises other modes.
- A small number of native unit and property tests cover scanner states, byte indexes,
  parser adapters, and fail-closed paths. Any result observable from both CLIs also gets a
  shared case.
- `scripts/check-golden-coverage.sh` fails if a topical fixture is referenced by neither
  tryscript nor the manifest, or if a parity payload is dangling.

Golden updates are never automatic during tests. For a behavior fix, desired output is
committed or reviewed as part of the Python implementation; the Rust port consumes that
same expected output from the pinned upstream commit.

## File and function map

The following boundaries are part of the implementation design. New file names may change
only if this map and the owning bead are updated before implementation; parser-specific
helpers must not absorb scanner authority by accident.

### Shared test system

| File | Responsibility |
| --- | --- |
| `tests/parity_corpus/manifest.toml` | Versioned case registry, stable `change_id` mapping, selectors, and exact process expectations. |
| `tests/parity_corpus/cases/**` | Minimal stdin and file-tree inputs plus exact stdout, stderr, and final-tree bytes. |
| `tests/parity_corpus/runner-fixtures/**` | Shared malformed schemas and intentional failures that constrain both native runners. |
| `tests/parity_corpus/spec/**` | Pinned CommonMark 0.31.2 source, provenance, license, and reviewed expected outputs. |
| `devtools/conformance.py` | `load_manifest()`, `validate_manifest()`, `select_cases()`, `materialize_case()`, `run_case()`, `compare_result()`, and selected `accept_cases()`. |
| `tests/test_conformance.py` | Pytest collection against the installed Python `flowmark` command; it never calls `fill_markdown()` as its oracle. |
| `scripts/check-golden-coverage.sh` | Manifest/path validation, payload reachability, topical-fixture reachability, and implementation-path rejection. |
| `Makefile` and `.github/workflows/ci.yml` | Read-only conformance targets, explicit selected acceptance, installed-binary injection, and CI gates. |
| `tests/tryscript/**` | One executable-neutral workflow suite using `FLOWMARK_BIN_DIR`; `math.md` and `code-inline.md` remain canonical topic inputs. |
| `tests/testdocs/**` and `tests/test_ref_docs.py` | One upstream whole-document input/expected set and a readable Python integration adapter. |

The Python runner uses the repository's existing `tomllib`/`tomli` compatibility. The Rust
runner uses the existing `toml` crate. The conformance design introduces no dependency.

### Python preservation pipeline

| File | Responsibility |
| --- | --- |
| `src/flowmark/preservation/model.py` | Typed region, candidate, container, normalized-source, and invariant records using UTF-8 byte offsets. |
| `src/flowmark/preservation/normalization.py` | `normalize_source()`, `finalize_output()`, BOM/newline handling, and scalar-width helpers. |
| `src/flowmark/preservation/registry.py` | Stable built-in recognizer kinds, precedence, and future extension registration. |
| `src/flowmark/preservation/scanner.py` | `scan_protected_regions()`, inline-scope and block scans, container views, delimiter state machines, candidate arbitration, and fallback. |
| `src/flowmark/preservation/bridge.py` | `choose_sentinel()`, token encoding/parsing, side-table substitution, and validated exact restoration. |
| `src/flowmark/linewrapping/markdown_filling.py::fill_markdown()` | Pipeline integration: optional explicit dedent, normalize, scan/protect, parse/transform/render, restore, and finalize. |
| `src/flowmark/formats/flowmark_markdown.py` | Thin Marko inline-token and opaque-block nodes plus renderer paths that carry tokens without recognizing their source syntax. |
| `src/flowmark/linewrapping/text_wrapping.py` | Structured fragments and unbreakable clusters with side-table widths and authored internal-line handling. |
| `src/flowmark/linewrapping/line_wrappers.py` | Width and semantic wrappers that never collapse protected gaps or measure token spelling. |
| `src/flowmark/transforms/doc_transforms.py` and typography modules | Walkers that skip typed protected nodes/tokens. |
| `src/flowmark/reformat_api.py` | Strict UTF-8 byte I/O for stdin/files, no implicit document dedent, deterministic errors, atomic no-partial writes, and direct single-file output routing. |
| `tests/test_preservation_*.py` | Small native tests for byte offsets, scanner states, arbitration, parser-token round trips, width metadata, and fail-closed invariants only. |

`atomic_patterns.py` and `block_heuristics.py` may keep their existing public or diagnostic
roles. They are not extended into a second preservation scanner. `iter_atomic_spans()`,
`ATOMIC_PATTERNS`, and `MARKDOWN_INLINE_PATTERNS` keep their compatibility contracts.

### Rust port

| File | Responsibility |
| --- | --- |
| `src/preservation/{model,normalization,registry,scanner,bridge}.rs` | Idiomatic Rust implementation of the same normative records, algorithms, and invariants. |
| `src/formatter/filling.rs::fill_markdown()` | Comrak-side protection pipeline and replacement of overlapping ad hoc PUA workarounds. |
| `src/formatter/markdown.rs` | Thin protected-node/parser-renderer adapter; comrak is not the syntax-recognition authority. |
| `src/wrapping/text_wrapping.rs` | Structured protected fragments and logical widths; replace preservation uses of NUL placeholder-length approximation. |
| `src/lib.rs` and `src/main.rs` | Library and CLI normalization, strict byte I/O, deterministic failure, atomic output semantics, and the direct single-file output route. |
| `tests/support/conformance.rs` and `tests/test_conformance.rs` | Independent native runner against `repos/flowmark/tests/parity_corpus/` and the shared runner fixtures. |
| `tests/test_tryscript_golden.rs` | Run upstream scripts with `FLOWMARK_BIN_DIR`; retain only genuinely Rust-specific workflows locally. |
| `tests/test_ref_docs.rs` and CommonMark tests | Read upstream assets directly below `repos/flowmark`; do not maintain synchronized copies. |
| `admin/port-coverage-mapping/**` and `repos/rust-porting-playbook` | Report the pinned upstream commit, stable change IDs, case IDs, and explicit temporary divergences. |

The Rust checkout inspected for this plan already has unrelated changes to
`repos/flowmark` and `repos/rust-porting-playbook`. Implementation must preserve or
coordinate those changes rather than overwriting them.

## Implementation plan

The tbd graph is the executable form of this plan. Parent beads group work; leaf beads own
files, functions, tests, and validation. Dependencies are attached to leaves so grouping
beads do not create parent-child deadlocks.

### Phase 0: shared conformance foundation (`fm-o5vk`)

1. `fm-ltof` (**complete**) defines schema version 1, payload layout, shared runner
   fixtures, and reviewed current-behavior seeds.
2. `fm-4cfe` (**complete**) implements the Python built-binary runner after `fm-ltof`.
3. `fm-0agl` (**complete**) adds selective acceptance, reachability, Makefile, and CI
   gates after `fm-4cfe`.
4. `fm-okli` (**complete**) makes upstream tryscript executable-neutral after `fm-ltof`.
   The exact `math.md` and `code-inline.md` workflows activate in `fm-ucy8` and
   `fm-ocpw`, respectively, so known-corrupt output is never committed as an intermediate
   baseline.
5. `fm-shou` imports and registers shared reference/CommonMark assets after `fm-ltof` and
   `fm-4cfe`.
6. `fm-gc8d` implements all Rust shared-test adapters after the runner, gates, tryscript,
   and document assets are stable.

The foundation may contain reviewed current-behavior cases, but never a golden known to
encode corruption. Both native runners and all runner-conformance fixtures must be green
before math changes expected output.

### Phase 1A: shared desired-output math behavior (`fm-9jtc`)

- `fm-9m7k` adds preservation-core and inline-math cases after `fm-0agl`.
- `fm-8rmy` adds display/container/I/O/adversarial math cases after `fm-0agl`.

These are red tests against exact desired output. They deliberately overlap `math.md`,
tryscript, reference documents, and CommonMark only where another layer exercises a
distinct boundary.

### Phase 1B: Python preservation core and math (`fm-ar24`)

1. `fm-k581` implements normalization, typed regions, and the recognizer registry after
   both shared math case groups exist.
2. `fm-felt` implements the inline scanner and arbitration after `fm-k581` and `fm-9m7k`.
3. `fm-6erm` implements container-aware block scanning after `fm-k581` and `fm-8rmy`.
4. `fm-idkl` implements the collision-safe bridge and thin Marko adapter after both
   scanners.
5. `fm-bsan` makes wrapping and transforms token-aware after `fm-idkl`.
6. `fm-ybpd` integrates `fill_markdown()`, public formatting paths, strict byte I/O, and
   fail-closed atomic output after `fm-bsan`.
7. `fm-9r1n` makes direct single-file `--output` succeed atomically after `fm-bsan`, while
   retaining the multiple-file rejection.
8. `fm-ucy8` reviews all Python golden layers and adversarial behavior after `fm-ybpd`,
   `fm-9r1n`, `fm-okli`, and `fm-shou`.

The closed experimental regex beads `fm-q32c` and `fm-mu4s` are historical evidence, not
implementation prerequisites. Their proposed post-parse fixes are superseded.

### Phase 2: direct Rust math port (`fm-wkve`)

1. `fm-fpbj` bumps the upstream submodule and ports the model, registry, scanners, and
   bridge after `fm-gc8d` and `fm-ucy8`.
2. `fm-1mq0` integrates protected nodes, structured wrapping, and byte-safe Rust I/O after
   `fm-fpbj`.
3. `fm-s0bl` proves every preservation-core/math change ID at all shared layers and updates
   the port ledger after `fm-1mq0`.

The Rust port is complete when the pinned upstream commit and shared case results prove it,
not when translated test names or counts match.

### Phase 3: inline code (`fm-zgte`)

1. `fm-uzvf` defines source-exact shared code-span cases after Rust math parity
   (`fm-s0bl`).
2. `fm-fa8p` adds the Python code-span recognizer after `fm-uzvf`; it closes the mechanism
   behind C1 (`fm-dq8n`).
3. `fm-9ey6` routes spans through exact restoration and structured wrapping after
   `fm-fa8p`; it closes the mechanism behind C2 (`fm-bj2c`).
4. `fm-ocpw` reviews all Python golden layers after both fixes.
5. `fm-82vu` ports `FM-CODE-SPAN-001` to Rust and proves exact parity after `fm-ocpw`.

### Phase 4: extension registry

After `fm-82vu`, each syntax family is a vertical slice: shared case matrix and desired
output, Python registry/scanner rule, direct Rust port, integration review, and zero new
divergence.

- P0 parent `fm-drjv`: Pandoc multiline tables (`fm-kr0a`), Obsidian callouts
  (`fm-aq78`), colon containers (`fm-dvl6`), TOML frontmatter (`fm-bl2j`), and definition
  lists (`fm-663e`).
- P1/P2 parent `fm-7vmg`, blocked on all P0 leaves: Pandoc grid tables (`fm-z8xh`), raw
  multiline HTML (`fm-w1tn`), attribute groups (`fm-c57j`), line blocks (`fm-mw49`), and
  MyST roles/wikilinks (`fm-5vlb`).
- `fm-w467` is the final cross-family integration and parity closeout after both parent
  groups.

Every behavior bead begins with shared desired-output cases, adds only the native tests
needed to diagnose internal invariants, and closes only after its exact golden diffs and
full relevant layers are reviewed. The Python commit and `change_id` set are the Rust
porting handoff.

## Backward compatibility

The new protection layer is internal. `AtomicPattern`, `ATOMIC_PATTERNS`,
`MARKDOWN_INLINE_PATTERNS`, `iter_atomic_spans`, their ordering, names, and character-offset
contract remain unchanged in this plan. Math is not added to those public tuples. A future
public protected-region API requires its own specification.

Formatter output intentionally changes for documents containing recognized math, source-
exact code spans, or extension blocks. Those changes restore authored syntax and are
the feature. Documents without recognized protected syntax should remain unchanged except
for the explicit BOM/newline boundary rules; the shared corpus measures that blast radius.

Configuration files and CLI flags remain compatible. Built-in recognition needs no new
option. No dependency is required by the architecture itself; any later dependency change
must follow the repository's supply-chain policy.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| A parser alters or splits a synthetic token. | Collision and parser-round-trip cases plus restoration validation; fail closed before output. |
| A sentinel collides with authored private-use text. | Deterministically choose an absent sequence and test inputs containing candidate sentinels. |
| Broad dollar pairing inhibits wrapping in currency or shell prose. | Accept as the safe default, pin exact output, and consider an additive strict profile only after evidence. |
| A block opener consumes unrelated trailing prose. | Commit only candidates with legal compatible closers; unmatched openers never own the suffix. |
| Lists and blockquotes close at the wrong indentation. | Shared container vectors cover every nesting direction, tabs, lazy continuation, and boundary mismatch. |
| Python code-point offsets diverge from Rust byte offsets. | Normative scanner positions are UTF-8 bytes; test CJK, combining marks, and supplementary scalars. |
| Placeholder width changes wrapping. | Use side-table logical width, never token text length; test N-1/N/N+1 boundaries. |
| Deep or malformed input becomes quadratic. | Single-pass runs and stacks, adversarial fixtures, and a generous hang watchdog. |
| Golden regeneration blesses corruption. | Desired-output TDD, selected explicit acceptance, full diff review, and no update mode in normal tests. |
| Test trees drift between repositories. | One upstream shared test surface consumed by a pinned submodule; no synchronized copies. |

## Acceptance criteria

- All required math forms work without dialect configuration.
- Recognized math and extension regions are exact normalized-source slices after formatting.
- Valid code spans preserve authored delimiters and body bytes exactly.
- Display blocks retain line structure, prefixes, labels, attributes, and nesting.
- Parser collisions cannot reinterpret protected content.
- Unmatched and mismatched input is deterministic, idempotent, non-crashing, and does not
  cause an unmatched block opener to own unrelated trailing prose.
- Scanner and restoration work are O(n) and fail closed.
- The Python and Rust built binaries consume the same manifest, inputs, and expected bytes.
- Math lands in Rust with zero new known divergences.
- Every behavior change is traceable from a stable `change_id` to shared case IDs and the
  pinned upstream commit.
- Both ports run the upstream tryscript, topic fixtures, reference documents, and
  CommonMark documents directly wherever their harnesses are portable.
- Language-specific unit tests are limited to internal invariants; shared observable
  behavior is never proven only by a native test.
- No preservation fixture is dead or maintained as an independent copy.

## Issue disposition

- [#70](https://github.com/jlevy/flowmark/issues/70) is Track A's original inline-math
  report; M3 and M4 expand its required fix.
- [#62](https://github.com/jlevy/flowmark/issues/62) supplies Track B's verified extension
  ledger. Its claim that dollar-math interiors are already safe must be corrected.
- [#58](https://github.com/jlevy/flowmark/issues/58) is consistent with C1's delimiter
  collapse; the shared cases determine whether the same fix closes it completely.
- [#67](https://github.com/jlevy/flowmark/issues/67) receives the GitLab math forms.

This spec remains in `.flowmarkignore` until source-exact code spans land. It contains
backtick-bearing examples that the current formatter can corrupt while formatting its own
documentation.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
