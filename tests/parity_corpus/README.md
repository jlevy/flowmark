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

## Manifest Version 1

`manifest.toml` has these top-level fields:

- `schema_version = 1`
- `corpus = "flowmark-language-neutral-conformance"`
- optional `[defaults.env]` string values
- one or more `[[case]]` tables

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
5. duplicate IDs
6. lexical path confinement
7. path existence, file kind, and symlink checks

## Authoring and Acceptance

Ordinary tests are read-only.
An acceptance command must name one or more exact case IDs, show the proposed complete
diff, and refuse a global update.
Review the input and every expected byte before committing; released Python output is
not authoritative when it contains a known defect.

Use small cases for precise failures and the shared tryscript, topic fixtures, reference
documents, and CommonMark documents for interaction coverage.
Repetition is appropriate only when another layer exercises a distinct boundary.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
