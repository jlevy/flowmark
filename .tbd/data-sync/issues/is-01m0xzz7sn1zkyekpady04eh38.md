---
type: is
id: is-01m0xzz7sn1zkyekpady04eh38
title: Make reference documents and CommonMark inputs shared upstream assets
kind: task
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y0056wzdgx731m97mrka76
  - type: blocks
    target: is-01m0y042abxn1c7w256z31w81j
parent_id: is-01m0xn2b9tnj99k484920ysv9z
created_at: 2026-08-26T02:56:43.313Z
updated_at: 2026-08-26T02:59:21.545Z
---
Complete the whole-document and standards-scale part of the shared test surface.

Python repository files:
- tests/testdocs/** remains the single Flowmark reference-document source.
- tests/parity_corpus/spec/** and LICENSE-COMMONMARK pin CommonMark 0.31.2 with provenance and a deterministic import/check procedure.
- tests/parity_corpus/manifest.toml registers all 652 default-mode examples plus a stable reviewed alternate-mode subset and representative reference-document CLI cases.
- tests/test_ref_docs.py remains a readable Python integration layer but must not define a second expected truth.

Review candidate outputs; do not blindly bless released Python output when it exposes a known defect. Prefer the smallest manifest cases for pinpoint failures and retain the large documents for blast-radius coverage. Acceptance: assets are offline, reproducible, license-complete, referenced once, deterministic in order, and usable directly beneath repos/flowmark by Rust.
