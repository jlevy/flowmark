---
type: is
id: is-01m0xzy6s60v1k1pmchfz8a3k9
title: Define the versioned shared conformance corpus and seed current behavior
kind: task
status: closed
priority: 1
version: 6
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0xzyjzy4xf6vn0g5nsa5zdw
  - type: blocks
    target: is-01m0xzz7sn1zkyekpady04eh38
  - type: blocks
    target: is-01m0xscz8eky51d0x92qv044xh
parent_id: is-01m0xn2b9tnj99k484920ysv9z
created_at: 2026-08-26T02:56:09.506Z
updated_at: 2026-08-26T03:15:44.951Z
closed_at: 2026-08-26T03:15:44.950Z
close_reason: Defined schema version 1, exact stdin/file-tree seed cases, portable payloads, shared malformed-manifest and intentional-failure fixtures, and the reviewed authoring contract. Full lint, 463 pytest tests, 133 tryscript checks, and build pass.
resolution: null
duplicate_of: null
---
Implement the schema-owned portion of FM-CONFORMANCE-001 in the Python repository.

Files:
- tests/parity_corpus/README.md
- tests/parity_corpus/manifest.toml
- tests/parity_corpus/cases/**
- tests/parity_corpus/runner-fixtures/**
- tests/parity_corpus/LICENSE-COMMONMARK and pinned provenance metadata when the CommonMark import lands

Function:
- Define schema_version = 1 and exact byte contracts for stdin and file-tree cases.
- Commit a small reviewed seed that characterizes current CLI behavior without treating known corruption as truth.
- Include shared malformed-manifest and intentional-failure fixtures so both native runners are tested against the same schema errors.
- Require stable case IDs, change_id, tags, idempotence, exact stdout/stderr/status/tree bytes, path confinement, and no implementation-specific executable paths.

Use the existing tomllib/tomli compatibility already in pyproject.toml; do not add a parser dependency. Ordinary tests never regenerate expected output. Acceptance: the manifest and every payload are readable offline, paths are portable below the allowed upstream roots, and the schema has enough seed cases to implement both runners.
