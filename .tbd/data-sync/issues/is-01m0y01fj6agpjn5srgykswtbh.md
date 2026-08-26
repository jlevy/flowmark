---
type: is
id: is-01m0y01fj6agpjn5srgykswtbh
title: Implement Python source normalization, region types, and recognizer registry
kind: task
status: closed
priority: 1
version: 7
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies:
  - type: blocks
    target: is-01m0y01wh744pw4vzp0516rz83
  - type: blocks
    target: is-01m0xse3xhcna7jm56zb5vj4hk
parent_id: is-01m0xn1kf4s20aga85f298dzww
created_at: 2026-08-26T02:57:56.804Z
updated_at: 2026-08-26T08:56:10.808Z
closed_at: 2026-08-26T08:56:10.807Z
close_reason: Extended the portable region model with exact block parser scaffolds in 3103f09; 496 pytest tests and lint/type checks pass.
resolution: null
duplicate_of: null
---
Create the portable data and boundary layer before recognizers.

Files and functions:
- src/flowmark/preservation/__init__.py: private package facade only.
- src/flowmark/preservation/model.py: RegionKind, RegionForm, ContainerContext, NormalizedSource, ProtectedRegion, Candidate, and invariant validation.
- src/flowmark/preservation/normalization.py: normalize_source() and finalize_output() for optional BOM, CRLF/lone-CR to LF, exactly one terminal LF, UTF-8 byte storage, and scalar-width helpers.
- src/flowmark/preservation/registry.py: ordered built-in recognizer descriptors and stable kind/change identifiers without exposing a new public API.
- tests/test_preservation_model.py: only byte-offset/scalar-width/invariant vectors that are awkward at the CLI boundary.

Normative scanner coordinates are half-open UTF-8 byte offsets. The CLI formatting path must not perform implicit textwrap.dedent or global strip before scanning; fill_markdown(dedent_input=True) remains an explicit docstring-helper transform and runs before normalization. No new dependency is needed.

Acceptance: multibyte and supplementary characters, BOM, all newline forms, empty input, terminal whitespace, and invalid region records match shared cases and small native invariants.
