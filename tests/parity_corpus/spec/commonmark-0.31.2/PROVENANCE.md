# CommonMark 0.31.2 Corpus Provenance

This directory pins the 652 examples published with CommonMark 0.31.2 on 2024-01-28. The
authoritative inputs come from
[`spec.json`](https://spec.commonmark.org/0.31.2/spec.json) and retain their published
example numbers, section names, and UTF-8 Markdown bytes.

The upstream `spec.json` SHA-256 is
`d431b29d97b6f73e69d547109cf5081578fac931e72afe95639ebe766c1b2a20`. The copied upstream
license SHA-256 is `3e4806ba6f20073e8ce40da5a0c4b59f7f44287965f538e195a4d734d833557b`.
The upstream `0.31.2` Git tag resolves to commit
`9103e341a973013013bb1a80e13567007c5cef6f`.

Run the offline integrity check with:

```shell
uv run python scripts/import-commonmark-spec.py check
```

The one-time `import` mode verifies both download checksums before extracting inputs.
It refuses to replace an existing corpus.
Generated formatter expectations are candidate decisions, not CommonMark HTML truth.
The one-time import classified 363 active default cases, 21 active alternate-mode cases,
71 code/backtick deferrals, 10 math-shaped deferrals, 102 HTML deferrals, and 106
baseline-behavior deferrals.
Each initial deferral committed the source bytes as desired output and named its owning
bead, never a passing corrupt baseline.

`import` and `reclassify` write a per-case `review-report.json` beside this file for the
reviewer to read. It is not committed: it is a snapshot of a single run, and the only way
to refresh it is to re-run the import, which rewrites every golden from the current binary
and re-derives every deferral. A committed copy can therefore only drift from the manifest,
and did — it recorded the 363/289 import split long after the manifest had moved on.
The historical copy remains in Git history at commit `eb500f7` if the per-case import
measurements are ever needed.

The manifest is the current execution ledger and can advance beyond that initial report
only through exact golden review.
As of 2026-08-26, the manifest contains 394 active and 258 deferred default cases, plus
21 active alternate-mode cases.
All 258 deferred cases carry the owner tag `owner-fm-n0ww`, the open bead that owns
classifying the live corpus.
They previously named `fm-w467` (166 cases), `fm-w1tn` (91), and `fm-5vlb` (one), and
all three of those beads had closed, so every deferred case pointed at finished work
while still reading as tracked.
These counts describe tracking state, not severity or a blanket conformance percentage.

Owner liveness is not machine-checkable in CI: bead records live on the `tbd-sync` Git
branch, not in the checkout, so no offline check can tell whether a named owner is still
open. The enforced invariant is instead the `DEFERRED_OWNER_TAGS` allowlist in
`devtools/conformance.py`, which names the owner tags a deferred case may carry.
`python -m devtools.conformance coverage` fails when a deferred case has no owner tag,
names an owner outside that allowlist, or when an active case still carries one.
Re-pointing the manifest tags and updating that constant is one edit, made whenever an
owner bead closes.

After source-exact inline-code preservation landed, examples 328 through 349—the
complete CommonMark Code spans section—were activated under `FM-CODE-SPAN-001`. Example
334 intentionally normalizes the soft newline between two spans while preserving both
authored spans exactly.
A backtick in another CommonMark section no longer assigns that case to the code-span
change ID; those cases retain their actual HTML, fence, list, escape, or general review
owner. The official rendered HTML remains provenance, not Flowmark output: these cases
test preservation and formatting, not parser conformance.
As a second review check, all 363 active defaults and 21 alternate outputs preserved the
same parsed structure as their inputs under the locked MarkdownIt 4.2.0 CommonMark
preset.

Ongoing review prioritizes semantic or structural corruption, non-idempotence, and
Python/Rust differences in common constructs.
Rare constructions and semantically equivalent source-spelling differences follow, but
every case still requires a reviewed compatible-normalization, selectively source-exact,
or open-gap disposition.

The explicit `reclassify` mode regenerates candidates from the pinned local inputs for a
reviewed classifier change.
It is not an acceptance command and must not replace a case-by-case output review.

The CommonMark specification is licensed under CC BY-SA 4.0. Test tooling has the
additional terms reproduced in `tests/parity_corpus/LICENSE-COMMONMARK`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
