# Math Preservation Desired-Output Baseline

This review records the shared conformance cases before the preservation implementation
changes either port.
The committed expected bytes state intended product behavior; they are not snapshots
accepted from the Python formatter.

## Review boundary

The baseline contains 33 language-neutral cases:

- 19 normalization and inline-math cases in
  `tests/parity_corpus/registries/math-inline.toml`;
- 14 block, whole-document, file-operation, configuration, and adversarial cases in
  `tests/parity_corpus/registries/math-block.toml`; and
- 76 uniquely referenced payload files, including binary UTF-8 error inputs and exact
  file-tree snapshots.

All cases carry a stable `FM-*` change ID, are deferred to `fm-ucy8` while red, and run
against either port’s injected executable.
No expected path names Python, Rust, Marko, comrak, uv, or Cargo.

The small cases were authored directly from the preservation contract.
The whole-topic expected file uses the formatter’s ordinary width-zero rendering only
for unprotected prose.
Every protected math slice was restored from the source fixture and the complete
source-to-expected diff was reviewed.
This avoids both accidental prose-preservation requirements and acceptance of the
current math corruption.

## Current Python disposition

The installed Python v0.7.3 behavior passes 12 cases and fails 21 desired-output cases.
Passing a pre-fix case means the existing behavior already satisfies that part of the
new contract; it does not weaken the required Rust comparison.

### Passing normalization and inline cases

| Case | Existing compliant behavior |
| --- | --- |
| `preservation.core.bom` | Restores one leading BOM. |
| `preservation.core.crlf-terminal-lf` | Normalizes CRLF and the terminal LF run. |
| `preservation.core.missing-final-lf` | Adds one final LF. |
| `preservation.core.sentinel-collision` | Carries authored private-use scalars unchanged before the bridge exists. |
| `preservation.math.inline.precedence-collisions` | Existing code and table behavior happens to retain the selected source. |
| `preservation.math.inline.malformed-fallback` | Unmatched inline openers degrade to stable ordinary text. |
| `preservation.math.inline.intraword-cluster` | This selected cluster does not cross the current wrap boundary. |
| `preservation.math.inline.width-n` | The formula ends exactly at width 14 without splitting. |
| `preservation.math.inline.width-n-plus-one` | Width 15 leaves the selected formula intact. |
| `preservation.math.inline.semantic-mode` | The selected protected form survives semantic mode. |

### Failing normalization and inline cases

| Case | Pre-fix failure that the desired output rejects |
| --- | --- |
| `preservation.core.invalid-utf8` | Invalid stdin is accepted instead of returning the shared exit-2 error with empty stdout. |
| `preservation.math.inline.dollar-boundaries` | Tabs inside balanced dollar regions become spaces. |
| `preservation.math.inline.escape-parity` | Smart quotes curl apostrophes inside active formulas instead of only transforming ordinary prose. |
| `preservation.math.inline.alternate-forms` | GitLab and MyST backtick delimiter runs are shortened by renderer canonicalization. |
| `preservation.math.inline.transform-shield` | Typography and cleanup walkers alter quotes, apostrophes, ellipses, and underscore content inside math. |
| `preservation.math.inline.markdown-contexts` | The renderer changes document-final spacing in the selected context document. |
| `preservation.math.inline.authored-newlines` | Soft newlines and continuation quote prefixes inside permissive math are collapsed. |
| `preservation.math.inline.width-n-minus-one` | Width 13 splits `$a + b$` after the plus. |
| `preservation.math.inline.width-one` | Width 1 splits the formula and escapes a fragment as Markdown. |

### Passing block and file cases

| Case | Existing compliant behavior |
| --- | --- |
| `preservation.math.block.code-precedence` | Fenced and indented code own math-shaped bytes before math scanning. |
| `preservation.math.io.check-no-mutation` | Check mode reports the missing final LF and leaves the input tree byte-identical. |

### Failing block and file cases

| Case | Pre-fix failure that the desired output rejects |
| --- | --- |
| `preservation.math.block.display-dollar` | A multiline labeled display collapses and loses tabs and aligned spaces. |
| `preservation.math.block.bracket-environments` | Bracket, nested, starred, and custom environments collapse; Markdown inside a custom environment is re-rendered. |
| `preservation.math.block.containers` | Quote/list displays collapse and their tabs and container layout change. |
| `preservation.math.block.document-adjacency` | Displays beside frontmatter, a table, and one-line raw HTML collapse into paragraphs. |
| `preservation.math.block.malformed-fallback` | A valid closed inner environment is not retained when its outer environment is unmatched. |
| `preservation.math.block.normalization-bom-crlf` | BOM and newline normalization succeed, but the normalized display slice collapses. |
| `preservation.math.topic.width-zero` | The topic document collapses multiline inline and block math and re-renders underscore content. |
| `preservation.math.io.output-file` | Direct single-file `--output` exits 1 instead of producing the isolated output file. |
| `preservation.math.io.inplace-normalization` | In-place CRLF normalization also collapses the display block. |
| `preservation.math.io.config-width` | Project-config width 13 splits the inline formula. |
| `preservation.core.invalid-file-no-mutation` | Invalid UTF-8 takes the generic exit-1 path instead of the deterministic exit-2 byte-input error. |
| `preservation.math.block.adversarial-linear` | The scan finishes within the timeout, but the long protected source is not byte-exact. |

The direct single-file `--output` expectation is an intentional public behavior change,
not a claim about v0.7.3. The existing tryscript transcript documents that operation as
an error. Its implementation, transcript, shared change ID, and Rust port must move
together.

## Golden review corrections

Review caught and corrected four traps before implementation:

1. Registry fragments live outside `cases/`; otherwise reachability treats TOML as an
   unreferenced payload.
2. The topic golden does not copy all input soft breaks at width zero.
   Ordinary prose is allowed to render normally while math remains source-exact.
3. Indented code is allowed to use Flowmark’s existing fenced-code canonical form
   because code precedence, not source-exact code-block rendering, is under test.
4. Unmatched block openers render as ordinary Markdown.
   A valid closed inner environment remains protected, with the unmatched outer opener
   outside that slice.

The topic source and reviewed expected file have different whole-file digests by design;
their protected slices match.
The adversarial input and expected output are byte-identical and include 4,096
consecutive dollars, 64 nested environments, and a 16,385-scalar body line.

## Reproduction

The baseline was validated with these read-only commands:

```bash
UV_CONFIG_FILE=uv.toml uv run python -m devtools.conformance coverage
UV_CONFIG_FILE=uv.toml uv run pytest tests/test_conformance.py -q
UV_CONFIG_FILE=uv.toml uv run python -m devtools.conformance run \
  --executable .venv/bin/flowmark --change-id FM-PRESERVE-CORE-001
UV_CONFIG_FILE=uv.toml uv run python -m devtools.conformance run \
  --executable .venv/bin/flowmark --change-id FM-MATH-INLINE-001
UV_CONFIG_FILE=uv.toml uv run python -m devtools.conformance run \
  --executable .venv/bin/flowmark --change-id FM-MATH-BLOCK-001
UV_CONFIG_FILE=uv.toml uv run python -m devtools.conformance run \
  --executable .venv/bin/flowmark --change-id FM-CLI-OUTPUT-001
```

The exact deferred cases are selected explicitly for pre-fix classification.
Normal test selection skips them until `fm-ucy8` removes the owner tags after both the
shared expected bytes and the Python implementation pass.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
