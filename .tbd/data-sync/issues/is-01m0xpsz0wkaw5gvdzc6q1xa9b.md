---
type: is
id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
title: "Phase 3: preserve inline code source-exactly in Python and Rust"
kind: feature
status: open
priority: 1
version: 11
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xn12jj483njnx12sm0sjs1
child_order_hints:
  - is-01m0xpsyq253tk2p90pq8vsz7c
  - is-01m0xn1zcv01nmb6qgtw0nsf1z
  - is-01m0xscyy7w21twx4n4p5pgvh5
  - is-01m0xsc02hwk2b4xnmww9869yk
  - is-01m0xscdmzyb7m84p8mtscn2j5
  - is-01m0xsczjbncpddwkvxsehvmsz
  - is-01m0y06s6yse0c28j4fa8mz1vs
created_at: 2026-08-26T00:16:33.308Z
updated_at: 2026-08-26T03:03:47.329Z
---
Parent for FM-CODE-SPAN-001 after math parity. Define exact shared behavior first, add code-span recognition to the established scanner, route valid spans through the same side table and structured wrapper, review Python blast radius, then port the same change ID to Rust.

Flowmark policy preserves the complete authored valid span after document-level normalization; it does not canonicalize delimiters or line endings to CommonMark renderer output. Public atomic-pattern APIs stay compatible. C1/C2 close only through exact shared evidence, and native tests remain small diagnostics.
