---
type: is
id: is-01m12r7m2df85ykkw5d3r1a8wk
title: "Vacuous exclusion assertions: file-discovery fixtures are deleted before the test runs"
kind: bug
status: closed
priority: 2
version: 3
labels:
  - testing
dependencies: []
created_at: 2026-08-27T23:17:41.580Z
updated_at: 2026-08-28T00:06:25.251Z
closed_at: 2026-08-28T00:06:25.250Z
close_reason: "Implemented and verified: restored non-vacuous shared discovery fixtures and scenarios, added the exact wrapped-pipe continuation and adjacent line-block contracts, and passed the full Python gates plus hosted CI."
resolution: null
duplicate_of: null
---
Found by auditing whether PR #81's test changes are strict improvements.

## Three assertions can no longer fail

The shared tryscript file-discovery.tryscript.md deletes four fixture
directories in its `before:` block:

    rm -rf fixtures/project/.venv fixtures/project/build \
           fixtures/project/skip fixtures/project/nested/generated

and the fixture tree no longer contains them. But the document still asserts
they are excluded from discovery:

    line  41: flowmark --list-files fixtures/project/ | grep -c '\.venv'   -> 0
    line  47: flowmark --list-files fixtures/project/ | grep -c build/      -> 0
    line 110: flowmark --list-files fixtures/project/ | grep -c skip/       -> 0

With the directories absent, `--list-files` cannot emit those paths, so each
assertion passes trivially. If default-directory exclusion or .flowmarkignore
handling broke tomorrow, none of the three would catch it.

## This is a reduction from the previous behavior

flowmark-rs main committed all four fixtures
(tests/tryscript/fixtures/project/{.venv/lib/README.md, build/output.md,
skip/ignored.md, nested/generated/output.md}) and its copy of the tryscript had
no `rm -rf` line, so the same three assertions were meaningful there. The
nested/generated fixture, used for nested-gitignore coverage, is also gone.

The `rm -rf` comment says it exists to ignore untracked local artifacts, so
deleting the committed fixtures alongside them looks unintended rather than a
deliberate policy change.

## Ask

Restore the four fixtures in the shared corpus and narrow the `before:` cleanup
so it removes only genuinely untracked artifacts, keeping the exclusion
assertions meaningful. The doc is shared, so this is an upstream change that
flowmark-rs then picks up with the next submodule pin.

Note the assertions still PASS today; this is a loss of test power, not a
failure, so it does not block PR #81.
