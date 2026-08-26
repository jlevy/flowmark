---
type: is
id: is-01m0xscz8eky51d0x92qv044xh
title: Wire code-inline.md and math.md into the tryscript goldens and the idempotency check
kind: task
status: open
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-25-markdown-preservation.md
labels: []
dependencies: []
parent_id: is-01m0xpsz0wkaw5gvdzc6q1xa9b
created_at: 2026-08-26T01:01:53.294Z
updated_at: 2026-08-26T01:02:17.472Z
---
Both content fixtures are currently dead: code-inline.md and math.md exist in the Python and Rust repos and are referenced by no test in either. That is why C1, C2 and M1-M4 all went unnoticed, and wiring them is the step that makes the corpora load-bearing rather than decorative.

Add each to tests/tryscript/formatting.tryscript.md beside the existing comprehensive.md cases, so the full formatted output becomes a checked-in golden. Add both to the idempotency check in tests/tryscript/auto-mode.tryscript.md, which currently exercises only comprehensive.md.

Expect the goldens to record CORRUPT output when first generated, since the fixes have not landed. That is the intended red state and should be committed as such only if the phase is being run TDD-first; otherwise generate goldens after fm-fa8p and fm-9ey6.

Do not add either fixture to scripts/check-golden-coverage.sh REQUIRED_FILES — that list is tryscript modules, not fixtures. The script already recurses into fixtures/ for its anti-pattern greps, so verify a bare "..." line never appears in either corpus.
