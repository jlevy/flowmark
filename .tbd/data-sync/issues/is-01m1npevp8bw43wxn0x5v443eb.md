---
type: is
id: is-01m1npevp8bw43wxn0x5v443eb
title: Add shared fenced-code adversarial parity cases
kind: task
status: closed
priority: 1
version: 5
labels:
  - release-blocker
  - parity
dependencies:
  - type: blocks
    target: is-01m1npp6qfkack71ng8czs2qdf
parent_id: is-01m1nn494vyzy4w2jqzqdtxxhp
created_at: 2026-09-04T07:52:15.815Z
updated_at: 2026-09-04T08:10:59.389Z
closed_at: 2026-09-04T08:10:59.386Z
close_reason: Canonical shared regression coverage landed locally and passes both ports bidirectionally; ready to include in the Python release-prep PR.
resolution: null
duplicate_of: null
---
Add language-neutral cases generated from the Python reference for fence info-string extra escaping/whitespace and literal numbered-looking content inside fenced code. These cases capture Rust-only gaps found by the deterministic property harness and must be pinned upstream before the Rust fixes.

## Notes

Evidence (2026-09-04): added Python-owned shared cases FM-FENCED-CODE-002, FM-FENCED-CODE-003, and FM-FENCED-CODE-004. Expected outputs were generated with current Python flowmark. Coverage/schema validation passed. Every case passes two Python runs. Rust was demonstrated red before implementation for root info suffix escaping/whitespace, literal numbered content, and container-nested language/suffix handling; all three pass two Rust runs after fmr-k9gi.
