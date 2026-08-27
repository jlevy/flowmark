# Flowmark Language-Neutral Conformance Corpus

This directory defines behavior shared by the Python and Rust `flowmark` commands.
The Python repository owns the manifest and payloads.
The Rust repository reads the same files through its pinned `repos/flowmark` submodule.

The normative design is
[Language-Neutral Flowmark Conformance Corpus](../../docs/project/architecture/current/language-neutral-conformance-corpus.md).
This README records the implemented schema and authoring workflow.

## Contract

Each case describes this exact process boundary:

```text
(input bytes, arguments, controlled environment, initial file tree)
    -> (stdout bytes, stderr bytes, exit status, final file tree)
```

Runners receive the executable path out of band.
Cases never name Python, Rust, a virtual environment, Cargo, or a platform-specific
binary directory.
All expected payloads are compared as bytes without decoding, trimming,
newline conversion, ANSI removal, or path replacement.

## Support Classification

Passing a case can establish several different claims.
Authors and reports must keep them separate:

1. **Practical support:** formatting preserves meaning and content, is deterministic and
   idempotent, and agrees across Python and Rust.
2. **CommonMark semantic compatibility:** the result retains the input’s CommonMark
   block and inline structure.
3. **Source treatment:** the result uses reviewed Flowmark line wrapping and
   canonicalization, preserving authored spelling exactly only where that is the safer
   or more useful formatter policy.

The shared expected Markdown is the executable cross-language contract.
Official CommonMark HTML and independent parse comparisons inform golden review; neither
native runner derives expected Markdown from its implementation’s parser.

Fix or activate cases in user-impact order: corruption or changed structure first, then
fixed-point and Python/Rust differences in common constructs, then uncommon spec cases
and semantically equivalent source spellings.
Full-corpus counts never override that order.

## Manifest Version 1

`manifest.toml` has these top-level fields:

- `schema_version = 1`
- `corpus = "flowmark-language-neutral-conformance"`
- optional `[defaults.env]` string values
- optional `case_registry` array of repository-root-relative TOML paths
- one or more `[[case]]` tables

Case registries let a large generated corpus remain reviewable without creating a second
schema.
Each fragment repeats `schema_version` and `corpus`, contains ordinary `[[case]]`
tables, and cannot define defaults or include another registry.
Runners append fragments in declared order after the root cases and reject duplicate
paths or case IDs across the merged manifest.

Every case requires:

- `id`: a unique stable ID matching `[a-z0-9]+([.-][a-z0-9]+)*`
- `change_id`: a stable product-change identifier matching `FM-[A-Z0-9-]+`
- `description`: one sentence describing observable behavior
- `kind`: `stdin` or `files`
- `tags`: a nonempty array of unique lowercase identifiers
- `args`: the complete argument vector after the executable name
- `expected_stdout`, `expected_stderr`, and `expected_exit`
- `idempotent`: whether the runner performs the specified second pass

A `stdin` case also requires `stdin` and forbids `before_tree` and `after_tree`. Its
arguments must contain `-` exactly once.
A `files` case requires `before_tree` and `after_tree`, forbids `stdin`, and must not
use `-` as an argument.

Paths use forward slashes and are relative to the upstream repository root.
Version 1 allows only these roots:

- `tests/parity_corpus/`
- `tests/tryscript/fixtures/`
- `tests/testdocs/`

Runners reject absolute paths, `.` or `..` components, backslashes, empty components,
paths outside the allowed roots, missing paths, and symlinks.
They reject unknown fields, duplicate case IDs, duplicate tags, unsupported schema
versions, and fields invalid for a case kind before executing any case.

For `files` cases, the runner copies the contents of `before_tree` into a fresh sandbox
and runs there. It compares the complete set of regular files and their bytes with
`after_tree`. Permissions, owners, timestamps, devices, and symlinks are outside schema
version 1.

## Idempotence

For an idempotent `stdin` case, the second run receives the first stdout as stdin and
must produce the same stdout, stderr, and exit status.
For an idempotent `files` case, the second run begins from a fresh copy of `after_tree`;
its complete result must equal the first expected result.

Only successful cases may set `idempotent = true`. Backup-producing and read-only
commands use focused non-idempotent process cases plus a separate formatter fixed-point
case when needed.

## Runner Fixtures

`runner-fixtures/manifest.toml` defines shared tests of the native adapters.
Each fixture names a standalone manifest and one expected outcome code:

- `manifest-error`: strict validation must fail with the declared schema error code
- `case-failure`: validation succeeds, execution fails with the declared comparison code

The error code is the cross-language assertion.
Human diagnostic wording may be idiomatic to each runner, but it must include the
fixture ID, offending field or path when applicable, and enough context to act without a
traceback.

Validation uses this order so malformed fixtures are deterministic:

1. top-level type, allowed fields, schema version, and corpus name
2. defaults and case-table types
3. required, unknown, and kind-specific case fields
4. ID, change-ID, tag, argument, and numeric value constraints
5. duplicate IDs within each file
6. lexical path confinement
7. path existence, file kind, and symlink checks
8. registry path uniqueness, one-level loading, and forbidden registry defaults
9. duplicate IDs across the merged manifest

## Deferred Cases

An unfiltered run skips a case tagged `deferred`; an explicit exact ID, change ID, or
tag selection includes matching deferred cases so developers can work on them directly.
Every deferred case has exactly one `owner-fm-*` tag naming its bead.
Deferred CommonMark cases commit source-preserving desired output, never a known corrupt
formatter result. Removing the deferral and owner tag is part of implementing the owning
change.

The live CommonMark default manifest contains 394 active and 258 deferred cases as of
2026-08-26. The checked-in `review-report.json` describes the original import split, not
the current ledger.
A deferred case whose owner is closed or missing is invalid tracking,
even when the desired output is already correct.

## Authoring and Acceptance

Ordinary tests are read-only.
An acceptance command must name one or more exact case IDs, show the proposed complete
diff, and refuse a global update.
Review the input and every expected byte before committing; released Python output is
not authoritative when it contains a known defect.

Use small cases for precise failures and the shared tryscript, topic fixtures, reference
documents, and CommonMark documents for interaction coverage.
Repetition is appropriate only when another layer exercises a distinct boundary.

Run the read-only corpus and all reachability checks with:

```shell
make test-conformance
```

Preview and write only named cases with a comma-separated exact-ID list:

```shell
make accept-conformance CASES=cli.stdin.wrap,cli.files.inplace-backup
```

The acceptance command prints the complete proposed diff, byte counts, and SHA-256
digests before writing.
Exit-status changes remain manual manifest edits so they cannot be silently accepted
with output bytes.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
