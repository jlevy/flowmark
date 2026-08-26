---
type: is
id: is-01m0zvqgntxmpx9hsht3bb9a1p
title: Port and verify the shared documentation pipeline in flowmark-rs
kind: task
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels:
  - docs
  - rust
  - parity
dependencies:
  - type: blocks
    target: is-01m0zvr4pywnx84bq8n8zn6jew
  - type: blocks
    target: is-01m0zvr5089jta3pfz0328589y
parent_id: is-01m0zvnkyqktm79pza59a36k3b
created_at: 2026-08-26T20:21:04.825Z
updated_at: 2026-08-26T20:21:25.639Z
---
Update flowmark-rs on its port branch after the upstream documentation sources and support catalog land. Advance the `repos/flowmark` gitlink to the exact upstream commit, regenerate the Rust README and embedded docs from the shared sources, and update only Rust-owned wrapper text where necessary.

The Rust binary must expose the same supported-syntax sections and claim statuses through `flowmark --docs`, while retaining Rust-specific installation, binary, and Python-library caveats. Parse or validate the language-neutral support catalog natively where the upstream test contract requires it; do not generate Rust truth by running Python.

Follow the Rust porting playbook's mapping and evidence workflow. Acceptance includes stable regeneration, crate-package extraction, `cargo test`, clippy/fmt, shared conformance execution, exact shared-section comparison, and clean recursive-clone evidence.
