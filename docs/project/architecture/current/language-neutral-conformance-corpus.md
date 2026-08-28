# Architecture: Language-Neutral Flowmark Conformance Corpus

**Date:** 2026-08-25

**Status:** Accepted design; implementation is tracked by `fm-o5vk`.

**Applies to:** `jlevy/flowmark` and `jlevy/flowmark-rs`.

## Decision

Flowmark has one language-neutral conformance corpus for behavior shared by the Python
implementation and the Rust port.
The corpus lives in the upstream Python repository at `tests/parity_corpus/`. The Rust
repository reads the same files through its existing `repos/flowmark` Git submodule.
Cases are never copied or translated between repositories.

The corpus is the cross-language behavioral source of truth:

```text
product contract
      |
      v
manifest.toml + exact case files in jlevy/flowmark
      |                                      |
      v                                      v
Python native runner                  Rust native runner
      |                                      |
      v                                      v
Python CLI                            Rust CLI
```

Both runners supply a binary, execute the same argument vector in the same isolated file
tree, and compare exact bytes.
Neither runner invokes the other implementation or depends on the other implementation
language.

The shared surface is larger than the minimal case corpus.
The upstream tryscript suite, topic fixtures, Flowmark reference documents, and imported
CommonMark documents are also canonical assets.
Both implementations consume them in place wherever the runner permits.
The layers deliberately overlap: a math construct can appear in a minimal parity case, a
readable tryscript workflow, and a large reference document because each catches a
different class of failure.

Small Python- or Rust-specific unit and property tests remain appropriate for scanner
states, byte indexes, parser adapters, and failure paths.
They supplement shared tests; they do not replace a shared case when the behavior is
observable in both ports.

This document supersedes the draft
`flowmark-rs/docs/project/specs/active/plan-2026-05-28-shared-parity-corpus.md`. That
draft established the correct repository and submodule direction.
This design extends it to exact CLI and filesystem behavior, multiple formatter modes,
stable change mapping, and intentional behavior changes.

## Goals

- Add a behavioral case once and run it unchanged against both implementations.
- Make an upstream change produce a precise list of Rust failures by stable case ID.
- Compare exact stdout, stderr, exit status, and file-tree bytes without whitespace
  normalization in the test runner.
- Keep golden updates explicit, reviewable, and separate from ordinary test execution.
- Exercise stdin, files, in-place updates, backups, configuration, and idempotence
  through the built CLI.
- Report every Rust difference as either a failure or a reviewed temporary divergence.
- Define shared tests and canonical test assets once wherever the behavior and harness
  are portable.
- Run the upstream tryscript suite, topic fixtures, reference documents, and CommonMark
  documents directly from both repositories instead of maintaining synchronized copies.
- Permit deliberate overlap and layer-specific goldens when they exercise a distinct
  boundary or make a regression substantially easier to understand.
- Keep the corpus usable offline and on a clean checkout.

## Non-goals

- The corpus does not prescribe Python or Rust implementation structure.
- It does not replace a small number of focused native unit tests or property tests for
  scanner internals.
- It does not run Python from Rust CI or Rust from Python CI.
- It does not generate expected output during an ordinary test run.
- It does not make every platform-specific filesystem behavior a cross-language
  contract.
- It does not treat the current Python output as correct when a case documents a known
  Python bug. Product intent, reviewed in the golden diff, is authoritative.

## Support levels and triage

The corpus distinguishes semantic compatibility from the source-form treatment chosen by
the formatter.

At the practical level, frequently used CommonMark, GitHub Flavored Markdown (GFM), and
GitLab Flavored Markdown (GLFM) constructs plus registered extension forms must be safe
in mixed documents with no dialect selection.
“Safe” means no content loss, delimiter corruption, changed block or inline meaning,
crash, non-determinism, second-pass change, or unexplained Python/Rust difference.
This is the minimum bar for a public support claim.

For CommonMark, every pinned example advances through four review gates:

| Gate | Required evidence |
| --- | --- |
| Semantic compatibility | The formatted Markdown retains the input’s CommonMark block and inline meaning. |
| Formatter policy | Line wrapping and canonical spelling are intentional, useful Flowmark behavior; source-exact treatment is required only where re-rendering is unsafe or clearly worse. |
| Fixed point | A second formatting pass produces the same process and output bytes. |
| Port parity | Python and Rust produce the same exact shared result. |

The official CommonMark HTML and pinned independent parse checks are review oracles.
Neither implementation generates expected Markdown from its parser during a test.
The reviewed expected Markdown remains the shared executable truth, so Rust can validate
parity offline without Python.

Triage follows user impact.
First fix data loss, changed structure, and corruption; then fixed-point and cross-port
failures in common paragraphs, headings, emphasis, links and images, lists, blockquotes,
code, raw HTML, autolinks, escapes, and widely used GFM and GLFM forms.
Uncommon constructions and semantically equivalent spelling differences follow.
Every deferred case still needs an open owner and an explicit disposition.

## Contract boundary

The shared boundary is the built `flowmark` command.
A case specifies:

```text
(input bytes, argument vector, controlled environment, initial file tree)
    -> (stdout bytes, stderr bytes, exit status, final file tree)
```

This boundary is deliberately narrower than source parity and broader than a formatter
function call. It avoids parser- and language-specific mechanics while covering the
behavior users and the Rust port must match.

Language-specific public APIs keep their own compatibility tests.
For example, Python’s `iter_atomic_spans` offsets and names are not silently made part
of the Rust contract.
Any public behavior that both ports promise must also have a CLI-observable conformance
case.

## Shared-first placement rule

Put each new test at the highest portable boundary that can express its useful
assertion:

1. Use a minimal conformance case for deterministic CLI or filesystem behavior shared by
   both ports.
2. Use the upstream tryscript suite for a readable multi-command workflow.
   Inject `FLOWMARK_BIN_DIR`; do not fork the script by implementation.
3. Use an upstream topic fixture or reference document for cross-feature and
   whole-document behavior.
   Both ports read the same input and expected files.
4. Use a native unit or property test only for an internal invariant that the portable
   layers cannot isolate cleanly.

A port-specific test that discovers user-visible behavior must be promoted to a shared
case before or with the fix.
A native regression may remain as a focused diagnostic, but it cannot be the only proof
of parity. Shared tests are defined once within each layer; the same behavior may still
appear in several layers for complementary coverage.

## Repository layout

```text
tests/parity_corpus/
├── README.md
├── manifest.toml
├── LICENSE-COMMONMARK
├── spec/
│   └── spec.txt
└── cases/
    ├── commonmark/
    │   └── cm-0001/
    │       ├── input.md
    │       ├── expected.stdout
    │       └── expected.stderr
    ├── preservation/
    │   ├── math-inline/
    │   ├── math-block/
    │   ├── code-span/
    │   └── opaque-block/
    └── cli/
        └── inplace-backup/
            ├── before/
            ├── after/
            ├── expected.stdout
            └── expected.stderr
```

Text payloads are separate files rather than escaped TOML strings.
This keeps Markdown, stderr, and file-tree changes readable in normal Git diffs.

Every file under `cases/` must be reachable from exactly one manifest case, except a
file explicitly declared as shared input.
Every manifest path must exist.
The coverage gate rejects dangling files and dangling entries.

Existing topical fixtures under `tests/tryscript/fixtures/content/` may be referenced
directly when a large integration document is useful.
A fixture used as a shared golden input must not be copied into `tests/parity_corpus/`.

## Manifest schema

The manifest is UTF-8 TOML with a numeric schema version.
Payload paths are slash-separated paths relative to the upstream repository root, not to
the manifest directory.
Schema version 1 permits only the canonical shared roots `tests/parity_corpus/`,
`tests/tryscript/fixtures/`, and `tests/testdocs/`. This lets a manifest case reuse an
integration fixture without `..` traversal and gives the Rust adapter the same path
beneath `repos/flowmark`.

Runners reject duplicate IDs, unknown fields, missing files, absolute paths,
parent-directory traversal, symlinks, paths outside those roots, and fields that do not
apply to the selected case kind.

The root may declare a `case_registry` array of repository-root-relative TOML paths for
large generated case sets.
A fragment repeats the schema version and corpus name and contains ordinary cases, but
it cannot define defaults or include another registry.
Runners append fragments in declaration order after root cases, then reject duplicate
registry paths and duplicate IDs across the merged manifest.
This remains one logical manifest and one source of truth; splitting the generated
CommonMark tables is only a review and tooling boundary.

```toml
schema_version = 1
corpus = "flowmark-language-neutral-conformance"

[defaults.env]
NO_COLOR = "1"
LC_ALL = "C"
TZ = "UTC"

[[case]]
id = "preservation.math.inline.intraword-subscript"
change_id = "FM-MATH-INLINE-001"
description = "Pandoc-style intraword math is preserved and remains atomic."
kind = "stdin"
tags = ["math", "inline", "pandoc", "intraword", "width-boundary"]
args = ["--width", "12", "-"]
stdin = "tests/parity_corpus/cases/preservation/math-inline/intraword-subscript/input.md"
expected_stdout = "tests/parity_corpus/cases/preservation/math-inline/intraword-subscript/expected.stdout"
expected_stderr = "tests/parity_corpus/cases/preservation/math-inline/intraword-subscript/expected.stderr"
expected_exit = 0
idempotent = true

[[case]]
id = "cli.inplace.backup.math-block"
change_id = "FM-MATH-BLOCK-001"
description = "In-place formatting preserves a display block and writes the promised backup."
kind = "files"
tags = ["math", "block", "inplace", "backup"]
args = ["--inplace", "workspace/input.md"]
before_tree = "tests/parity_corpus/cases/cli/inplace-backup/before"
after_tree = "tests/parity_corpus/cases/cli/inplace-backup/after"
expected_stdout = "tests/parity_corpus/cases/cli/inplace-backup/expected.stdout"
expected_stderr = "tests/parity_corpus/cases/cli/inplace-backup/expected.stderr"
expected_exit = 0
idempotent = false
```

### Required common fields

- `id`: stable, unique identifier matching `[a-z0-9]+([.-][a-z0-9]+)*`. Once released,
  an ID is never reused for different behavior.
- `change_id`: stable product-change identifier.
  Many cases may map to one change.
  A Rust port PR cites the change IDs and receives the exact case set from the manifest.
- `description`: one sentence that states the behavior under test.
- `kind`: `stdin` or `files` in schema version 1.
- `tags`: searchable coverage dimensions, not a substitute for the case description.
- `args`: the complete argument vector after the executable name.
  A stdin case includes `-` explicitly.
- `expected_stdout`, `expected_stderr`, and `expected_exit`: always required.
  Successful silence is represented by a committed zero-byte file, never by omitting an
  assertion.
- `idempotent`: whether the runner must perform the second-pass check.

### Stdin cases

`stdin` is required.
`before_tree` and `after_tree` are forbidden.
The runner supplies the file’s exact bytes to stdin and captures stdout and stderr as
bytes.

For an idempotent stdin case, `expected_exit` must be zero.
The runner executes the same command a second time with the first run’s stdout as stdin.
The second stdout must equal the first stdout byte-for-byte; stderr and exit status must
equal their committed expectations.

### File-tree cases

`before_tree` and `after_tree` are required.
`stdin` is forbidden.
The runner copies the contents of `before_tree` into a fresh temporary directory and
uses that directory as the process working directory.
Arguments name paths relative to that root.

After execution, the runner compares the complete set of regular files and their bytes
to `after_tree`. Extra and missing files fail.
This comparison covers backups and output files without separate ad hoc fields.
Schema version 1 deliberately excludes permissions, owners, timestamps, devices, and
symlinks because their semantics are not portable.

For an idempotent file case, `expected_exit` must be zero.
The runner begins a second run from a fresh copy of `after_tree`, uses the same
arguments, and requires stdout, stderr, exit status, and the complete tree to equal
their first-run expectations.
Cases whose command intentionally creates a new backup on every run set
`idempotent = false` and get a separate focused case for the formatter’s idempotence.
Read-only commands such as `--check` also set `idempotent = false`; their exit semantics
are covered directly rather than being confused with formatter fixed-point behavior.

### Environment and process rules

The runner starts from a minimal allowlisted environment plus `defaults.env`. It
supplies the executable path out of band; no case contains `.venv`, `target/debug`,
`python`, `cargo`, `uv`, or another implementation-specific path.

The working directory is always the isolated sandbox.
Cases must not depend on network access, wall-clock time, random values, the user’s home
directory, locale-specific text, or absolute temporary paths in expected output.

Expected files are byte contracts.
Runners do not trim, decode, normalize newlines, hide ANSI sequences, or replace paths
before comparison. If the product intentionally canonicalizes CRLF to LF, the expected
file contains LF and the case proves that product behavior.

Payload files may contain arbitrary bytes so invalid-UTF-8 CLI errors can be tested.
The manifest and descriptions remain UTF-8.

## Native runner protocol

The Python and Rust runners independently implement the following protocol:

1. Parse and strictly validate the manifest before executing any case.
2. Select cases by exact ID, change ID, or tags when a developer requests a subset.
3. Create a fresh sandbox and materialize the declared input without text conversion.
4. Spawn the supplied executable with the exact argument vector and controlled
   environment.
5. Capture stdout, stderr, and exit status without decoding them.
6. Compare all declared outputs and the complete file tree.
7. Perform the second-pass check when `idempotent = true`.
8. Report the stable case ID, command, and a bounded unified or binary diff on failure.

The Python runner is collected by `pytest` and invokes the installed project CLI. It
does not call `fill_markdown` directly.
The Rust runner uses Cargo’s built-binary path and reads the corpus from
`repos/flowmark/tests/parity_corpus/`. It does not need Python, `uv`, or network access.

Runner conformance is itself tested with shared malformed-manifest and
intentional-failure fixtures.
This prevents the two adapters from quietly assigning different meanings to the same
schema.

An unfiltered run omits cases tagged `deferred`. Any populated exact selector includes
matching deferred cases, which keeps the normal suite green while making each owning
bead directly runnable.
A deferred case has exactly one `owner-fm-*` tag.
Deferred CommonMark expectations equal their input bytes so the corpus states
preservation-safe desired behavior instead of blessing a known defect.
The live CommonMark default ledger contains 394 active and 258 deferred examples as of
2026-08-26. `review-report.json` retains the historical import classification and is not
a current completion report.

## Golden authoring and review

Golden files are executable product decisions, not disposable snapshots.

### Characterizing existing behavior

1. Minimize the input while keeping the behavior visible.
2. Run the released Python baseline to produce a candidate expected file.
3. Review the full input-to-output diff for dropped content, broken structure, and
   accidental normalization.
4. Commit the expected only after that review.
   A bug discovered during review gets a desired-output case and an implementation fix,
   not a blessed broken golden.

### Changing behavior intentionally

1. Allocate or reuse a stable `change_id`.
2. Add the smallest cases that state the desired output before changing implementation
   code. The relevant Python tests should be red.
3. Implement the Python behavior until those shared cases pass.
4. Run the topical integration fixture and whole-document goldens to expose
   interactions.
5. Review every changed expected file.
   Broad, unexplained churn blocks the change.
6. Merge the upstream change with its exact case IDs in the PR description.
7. Bump the Rust `repos/flowmark` submodule.
   The new failing IDs are the porting queue.
8. Implement Rust behavior until the same cases pass without Python at test time.

Ordinary test commands are read-only.
An explicit acceptance command may update selected goldens, but it must require case
IDs, print the diff, and refuse an unbounded rewrite.
There is no global “update every snapshot” step in CI or normal development.

## Rust divergence policy

The Rust repository may temporarily carry `tests/parity_corpus_known_divergences.toml`.
Each entry contains:

```toml
[[divergence]]
case_id = "commonmark.cm-0017"
tracker = "fmr-xxxx"
reason = "Parser-library difference under investigation."
```

The Rust runner enforces both directions:

- An unlisted mismatch is a failure.
- A listed case that now passes is a failure until the stale entry is removed.
- An entry for a case missing from the submodule-pinned manifest is a failure.
- Duplicate entries and empty `tracker` or `reason` fields are failures.

Baseline additions occur only in the explicit submodule-sync review.
They are never generated or accepted automatically.
New preservation changes, beginning with math, have a zero-new-divergence merge policy:
the submodule bump and implementation land together, or the Rust PR remains red.

## Relationship to existing test systems

Sharing is the default at every layer.
“Shared” means the test definition, input, and expected behavior live upstream once and
both implementations run them.
It does not mean that every layer must collapse into one assertion.
Independent expectations are justified when the layer has a distinct purpose—for
example, a concise parity failure versus a readable CLI transcript versus a
whole-document diff.

| Existing system | Continuing role | Sharing rule |
| --- | --- | --- |
| `tests/tryscript/*.tryscript.md` | Readable CLI workflows and broad smoke coverage | Keep one upstream suite and make the binary directory an injected runner value. Rust runs the files through `repos/flowmark`; a Rust-only CLI feature may add a local script. Embedded transcript expectations may intentionally overlap corpus cases. |
| `tests/tryscript/fixtures/content/*.md` | Topic-level integration documents | Reference the upstream file directly from the manifest and both tryscript runners; never copy it. Every fixture must be referenced. |
| `tests/testdocs/` | Large whole-document regression and blast-radius detection | Treat upstream inputs and expected documents as shared goldens and run them directly from both ports. Register representative mode pairs in the manifest when process-level coverage adds value. |
| CommonMark and other imported documents | Standards-scale syntax coverage | Pin provenance upstream once, then run the same documents and reviewed expected outputs in both ports. Do not vendor another Rust copy. |
| Python and Rust unit tests | Small internal contracts, failure paths, and property tests | Keep only tests whose useful assertion depends on native internals. Add a shared black-box case for any behavior promised by both ports. |
| Rust `tests/parity/` and golden generator | Historical corner-case parity and focused native diagnostics | Register portable cases and expected outputs upstream. Retain a native golden only when it exercises a distinct boundary; never regenerate truth from whichever Python binary happens to be installed. |
| Optional cross-binary tests | Local diagnosis during a port | Never required for normal Rust CI and never the source of expected output. |
| `admin/port-coverage-mapping/` | Inventory of language-specific tests | Do not use it as behavioral proof. Shared cases map by `change_id` directly. |
| Machine-local `attic/test-docs/` | Additional real-world differential sweep | Diagnostic only until provenance and reconstruction are checked in. |

The tryscript runner must accept the implementation’s executable path or binary
directory out of band.
The shared scripts must not contain `.venv/bin` or `target/debug`; those details belong
in the thin Python and Rust runner adapters.
The Rust adapter runs the upstream scripts and fixtures from
`repos/flowmark/tests/tryscript/` rather than copying them into `tests/tryscript/`.

The tryscript fixture-coverage gate expands to require that every topical fixture is
referenced by tryscript or the parity manifest.
The parity gate separately requires every case payload to be referenced exactly once.
These gates make dead fixtures structurally impossible.

## Coverage model

The corpus combines three scales:

- **Minimal regression cases:** one behavior and one reason to fail, with a stable ID.
- **Interaction cases:** deliberately cover pairs such as math plus smart quotes, math
  in a list, or a protected block under in-place formatting.
- **Integration documents:** kitchen-sink fixtures and reference documents expose
  cross-feature churn that a minimal case cannot.

Coverage is organized by manifest tags across these dimensions:

| Dimension | Required examples |
| --- | --- |
| Syntax | CommonMark plus GitHub, GitLab, MyST, Pandoc, Quarto, Obsidian, raw HTML, and supported extension forms |
| Context | Paragraph, heading, list, blockquote, table, link text, footnote, frontmatter adjacency, container |
| Transform | Default, semantic, cleanups, smart quotes, ellipses, auto, list spacing |
| Width | Zero, one, deliberately overlong, and delimiter at N-1, N, and N+1 |
| I/O | Stdin/stdout, input/output files, in-place, backup/no-backup, check, config precedence |
| Encoding | ASCII, non-ASCII scalars, combining marks, tabs, LF, CRLF, BOM, missing final newline, invalid UTF-8 error |
| Validity | Canonical, permissive-dialect, ambiguous, unmatched, mismatched, and adversarial |

The suite does not blindly take the Cartesian product.
Each rule gets a minimal case; high-risk interactions get deliberate pairwise cases;
each feature gets at least one topic-level integration document.
Coverage checks inspect required IDs and dimensions, not a fragile total test count.

All 652 CommonMark 0.31.2 examples seed the default-mode surface.
Alternate modes use a stable, reviewed subset plus all Flowmark-specific preservation
cases. A case moves from the subset only through a manifest diff, so coverage cannot
change because of hash order or runner implementation.

Coverage of all examples is an inventory, not by itself a conformance claim.
Reports must separate active from deferred cases and group failures by semantic
compatibility, formatter policy, fixed point, or port parity.
Raw pass counts cannot hide a common high-impact failure behind many rare passing
examples.

Adversarial linear-time inputs are committed or deterministically generated from a fixed
recipe and hash. CI uses a generous watchdog to catch hangs, not a machine-sensitive
microbenchmark threshold.
Python and Rust keep their own performance benchmarks.

## CI and synchronization

Python CI runs schema validation and the native corpus runner as part of `make test`.
Rust CI initializes `repos/flowmark`, builds the Rust binary, and runs its native
adapter against the submodule-pinned corpus.
Both jobs are offline after dependencies are installed.

The submodule commit is the synchronization boundary.
A Rust port is exactly synchronized for a change when:

- `repos/flowmark` points at a commit containing that `change_id`;
- all cases with that `change_id` pass against the Rust binary; and
- no case is hidden by a new divergence entry.

This proof needs no copied fixture hash, translated test name, Python runtime, or manual
claim of parity. The manifest can generate a port report grouped by `change_id` for the
Rust PR and release notes.

## Acceptance criteria

- One upstream manifest and payload tree drives both built binaries.
- Each case asserts exact process and filesystem results.
- Both runners reject the same invalid schema fixtures.
- Every shared behavior change has a stable `change_id` and at least one stable case ID.
- Idempotence is checked at the same CLI boundary for every formatting case where a
  second run is meaningful.
- Expected files cannot change during ordinary tests.
- Rust CI runs without Python and identifies parity gaps by case ID.
- New Rust divergences fail by default; stale divergence entries also fail.
- Portable tryscript, topic-fixture, reference-document, and CommonMark tests are
  defined upstream once and run directly by both implementations.
- Frequently used CommonMark, GFM, and GLFM constructs meet the practical support floor
  before public support claims become unconditional.
- Every CommonMark example has a reviewed compatible-normalization, selectively
  source-exact, or open-gap disposition; semantic, formatter-policy, fixed-point, and
  parity failures are reported separately from equivalent source-spelling differences.
- Deliberate overlap between minimal parity cases, tryscript transcripts, and
  whole-document goldens is retained and documented by test boundary.
- Native-only unit tests remain small; any cross-language behavior they expose also has
  a shared test.
- No topical or parity fixture can remain unreferenced.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
