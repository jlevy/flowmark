# Feature: Open GitHub Issues Triage and Fixes (2026-05-29 round)

**Date:** 2026-05-29 (last updated 2026-05-29)

**Author:** Joshua Levy (with agent assistance)

**Status:** In Review (5 of 7 issues fixed in PR #56; #21 and #4 triaged with analysis
posted upstream)

## Overview

This spec walks through every open GitHub issue on `jlevy/flowmark` as of 2026-05-29,
grounds each one in the actual code, and decides — per issue — whether it deserves a
fix, what the cleanest fix is, and how it fits the existing design.
The goal is to resolve as many issues as make sense in one focused round without rushing
changes that need a real design decision.

Each issue below records: the diagnosis (with file:line references), a recommendation
(**Fix now** / **Fix now, depends on …** / **Defer — needs design** / **Mostly works —
minimal change**), and the planned approach.

## Goals

- Triage all open issues with grounded root-cause analysis.
- Fix the well-scoped bugs and the small, clearly-correct features this round.
- For larger or design-sensitive requests, document the decision and the recommended
  direction rather than rushing an implementation.

## Non-Goals

- A locale/i18n typography subsystem (issue #4) — flagged for a separate design pass.
- Reworking the line-wrapping segmentation architecture beyond the contained fixes
  described here.

## Issue Triage

### Issue #42 — `--semantic` not idempotent on task list items — **Fix now**

**Severity:** Medium (breaks pre-commit loops).
**Complexity:** Small.

**Diagnosis.** With `--semantic` at `--width 0`, GFM task-list items (`- [ ]` / `- [x]`)
gain one extra space between `]` and the text on every pass.

Root cause is a double space created at render time, then not normalized:

1. marko’s GFM `Paragraph` strips the `[ ]` marker but keeps the following space in
   `inline_body` (library behavior).
2. `render_paragraph` in `src/flowmark/formats/flowmark_markdown.py:419` re-adds the
   prefix with its own space:
   `children = f"[{'x' if element.checked else ' '}] {children}"` — and `children`
   already begins with the leftover space → `"[ ] text"`.
3. The semantic wrapper’s `width <= 0` early return in
   `src/flowmark/linewrapping/line_wrappers.py:127-128` does `text.strip()`, which does
   **not** collapse the internal double space.
   (At `width > 0`, and in non-semantic mode, `re.sub(r"\s+", " ", text)` masks the bug
   — which is why it only shows at `--width 0 --semantic`.)
4. Next pass: marko strips `[ ]` again, leaving two leading spaces, and the count grows
   each run.

**Fix.** Eliminate the double space at the source: `children.lstrip()` before prepending
the checkbox prefix at `flowmark_markdown.py:419`. Also harden the `width=0` semantic
path (`line_wrappers.py:128`) to normalize internal whitespace
(`" ".join(text.split())`) so latent double-spaces can never resurface.
Add an idempotency test (run format twice, assert stable) at `width=0` and `width=88`.

### Issue #43 — `--force-exclude` / `.flowmarkignore` ignored on explicit file paths — **Fix now**

**Severity:** Medium (blocks pre-commit / format-on-save / agent hooks).
**Complexity:** Medium.

**Diagnosis.** When every input is an explicit file (no dir, no glob), `_resolve_files`
short-circuits and returns the paths untouched: `src/flowmark/cli.py:366-367` returns
`options.files` whenever `_needs_file_resolution()` is `False` (cli.py:349-358 only
counts dirs/globs).
The `FileResolver` — the only place exclusions are applied — is never
constructed, so `--force-exclude`, `--exclude`, `--extend-exclude`, and
`.flowmarkignore` all silently no-op for explicit-file invocations.

Secondary defects, confirmed in `src/flowmark/file_resolver/resolver.py`:

- `_should_include_explicit` (resolver.py:83-96) only checks the basename and each
  ancestor directory component **individually** (`part + "/"`), never the cumulative
  relative path, so multi-component patterns like `docs/api/` cannot match (contrast
  `_is_dir_excluded`, resolver.py:134-162, which does build `rel_with_slash`).
- `_should_include_explicit` never consults `.flowmarkignore` at all — tool-ignore is
  only loaded inside `_walk_directory` (resolver.py:103,216-221).

**Fix.** Route explicit-file inputs through `FileResolver` when any exclusion option is
active (`force_exclude`, or non-empty `exclude` / `extend_exclude`). Removing the
short-circuit entirely is tempting but changes behavior for the common no-filter case
(extra `stat`/resolve work, sorting, dedup) — so gate on “filtering is requested” to
keep the default path untouched.
Then fix `_should_include_explicit` to (a) match the file’s path relative to cwd against
the exclude spec for multi-component patterns, and (b) consult `.flowmarkignore` via the
existing `_get_tool_ignore`. Tests: explicit-file + `--force-exclude` (no
`--list-files`), multi-component pattern, and `.flowmarkignore` on an explicit path.

### Issue #44 — `--check` flag for lint/CI mode — **Fix now**

**Severity:** Feature (needed for CI + pre-commit).
**Complexity:** Small-Medium.

**Diagnosis.** No check/dry-run mode exists.
The architecture makes it easy: `reformat_text()` (`src/flowmark/reformat_api.py:12-46`)
is pure, and in `reformat_file()` both the original `text` (reformat_api.py:94) and
formatted `result` (reformat_api.py:96) are already in scope; comparing them is trivial.
`main()` exit codes today: 0 success, 1 user error, 2 unexpected error (cli.py).

**Fix.** Add a `--check` boolean flag (cli.py + `Options` + config).
Thread a `check` parameter through `reformat_files`/`reformat_file`; when set, compute
`result`, compare to `text`, do **not** write, and collect the set of files that would
change. `main()` prints the would-change files to stderr and returns exit code 1 if any
differ, 0 otherwise (matching Black/Ruff/Prettier convention; keep 2 for real errors).
`--check` must be compatible with the read-only path and must not require `--inplace`.
Tests: a file needing changes → exit 1 and unchanged on disk; an already-formatted file
→ exit 0.

### Issue #24 — Publish a pre-commit hook — **Fix now (depends on #43, benefits from #44)**

**Severity:** Feature (popular request).
**Complexity:** Small (once #43/#44 land).

**Diagnosis.** No `.pre-commit-hooks.yaml` exists.
flowmark is on PyPI with a `flowmark` entry point (pyproject.toml:61-64), and the README
only documents a `lefthook`/`local` hook (README.md:539-553). pre-commit passes explicit
filenames — so correct exclusion behavior requires #43, and a true CI “lint” mode
requires #44.

**Fix.** Add `.pre-commit-hooks.yaml` at repo root with two hook ids:

- `flowmark` — auto-fix mode: `entry: flowmark`, `args: [--auto, --force-exclude]`,
  `language: python`, `types: [markdown]`.
- `flowmark-check` — check-only mode for CI: `args: [--check]` (added once #44 lands).

Update the README pre-commit section to reference the published hooks.
Land after #43 (so `--force-exclude` actually works on the explicit paths pre-commit
passes) and #44 (so the check hook exists).

### Issue #35 — Line breaks inside multi-line HTML comments are collapsed — **Fix now**

**Severity:** Medium-high (destroys intentional structure, e.g. Markform field defs).
**Complexity:** Small-Medium.

**Diagnosis.** Multi-line `<!-- ... -->` comments are parsed by marko as paragraph
content containing an `InlineHTML` node (block-level custom HTML matching is disabled —
`flowmark_markdown.py:80-82`). The `InlineHTML` text keeps its newlines at parse time,
but the line wrapper then flattens them: semantic mode at
`src/flowmark/linewrapping/line_wrappers.py:124` does `text.replace("\n", " ")`, and
width mode at `src/flowmark/linewrapping/text_wrapping.py:117-118` does
`re.sub(r"\s+", " ", text)`. The tag-segmentation in `add_tag_newline_handling`
(`tag_handling.py`) only treats the first/last comment lines as tag boundaries, so the
interior lines fall through to the flattening wrapper.

**Fix.** In the segmentation logic of `add_tag_newline_handling`
(`src/flowmark/linewrapping/tag_handling.py`), detect a multi-line HTML comment (opening
`<!--` on one line, closing `-->` on a later line) and emit the whole comment as a
verbatim, non-wrapped segment — consistent with how table rows and tag-only lines are
already preserved. Distinguish a single spanning comment from several single-line
comments. Tests + a golden case in `tests/testdocs/`. Collapsing such comments is never
desirable, so regression risk is low.

### Issue #21 — Preserve newlines before tables/lists after bold/italic labels — **Mostly works — minimal/defer**

**Severity:** Low. **Complexity:** Small-Medium if pursued.

**Diagnosis.** Investigation shows the headline cases in the issue **already work**:

- `**Items:**` + numbered list and `*Options:*` + bullet list — marko parses the label
  and the list as separate blocks, so the wrapper never joins them.
- `**Ratings:**` + a pipe-led table — kept apart because `line_is_table_row`
  (`block_heuristics.py:26-36`) is always a segment boundary in `tag_handling.py`.
- `**Title:**` + plain text — correctly joined (desired).

The only genuine failure is a **table written without a leading `|`** (e.g.
`Source | Score` / `--- | ---`), which `line_is_table_row` doesn’t recognize — and that
fails with or without a preceding bold label, so it’s a separate, minor table-detection
gap, not really about bold/italic labels.

**Recommendation.** Do not implement the proposed bold-label preprocessing this round:
it adds a heuristic (with false-positive risk against `**Note:** regular text`) to fix
cases that already pass.
Optionally file the pipe-less-table detection as its own small issue.
Document this conclusion on the GitHub issue and keep it open or close as “works as
intended” per maintainer preference.

### Issue #4 — Typographic rules for other languages (French) — **Defer — needs design**

**Severity:** Feature.
**Complexity:** Large (design shift).

**Diagnosis.** The typography layer is fundamentally English-specific:
`src/flowmark/typography/smartquotes.py` hardcodes English curly quotes (`“ ” ‘ ’`), and
its `QUOTE_PATTERN` plus apostrophe/contraction heuristics encode English conventions.
French needs guillemets (`«` `»`), narrow no-break spaces (U+202F) inside them and
before `! ? ;`, and a no-break space (U+00A0) before `:` — none of which are
parameterizations of the current regex; they are new transforms.
There is no `--locale` concept anywhere.
Only `--smartquotes`/`--ellipses` booleans exist (cli.py, config.py); the transform
plug-in point is `src/flowmark/linewrapping/markdown_filling.py:92-95`.

**Recommendation.** Defer.
This is a real design decision: a `--locale fr` option (extensible, threaded cli →
config → reformat_api → markdown_filling, with per-locale rule sets) versus discrete
French feature flags.
Worth doing as its own spec with the maintainer’s input — out of scope for this bug-fix
round. Document the recommended direction on the issue.

## Implementation Plan

One phase. Order is easiest/most-isolated first; the pre-commit hook lands after its
dependencies.

### Phase 1: Bug fixes and pre-commit enablement

- [x] #42: `lstrip()` checkbox children + normalize `width=0` semantic path; idempotency
  tests. Done.
- [x] #43: Route explicit files through `FileResolver` when `--force-exclude` is set (so
  exclusions and `.flowmarkignore` apply to explicitly-named files too); explicit naming
  otherwise overrides exclusions, matching Black/Ruff.
  Fixed `_should_include_explicit` (relative-path match for multi-component patterns +
  `.flowmarkignore`); tests.
  Done.
- [x] #44: Add `--check` flag threaded through `reformat_files`/`reformat_file`; exit
  code 1 on would-change; tests.
  Done.
- [x] #24: Add `.pre-commit-hooks.yaml` (`flowmark` = `--auto --force-exclude`,
  `flowmark-check` = `--auto --check --force-exclude`); update README. Both hooks set
  `--force-exclude` (as `ruff-pre-commit` does) so exclusions apply to the explicit
  paths pre-commit passes; the check hook mirrors `--auto` so it validates exactly what
  the auto-fix hook would write.
  Done.
- [x] #35: Preserve line breaks of multi-line HTML comments via verbatim segment in
  `tag_handling.py`; unit tests.
  Done. (Interior indentation is stripped by marko’s inline parsing and is not recovered;
  line breaks are preserved, resolving the reported collapse.)
- [x] #21: Triaged — re-verified the headline cases all pass; no code change made.
  Analysis posted on the issue recommending it be closed as working-as-intended, with
  the pipe-less-table detection gap noted as a possible separate follow-up.
- [x] #4: Triaged — analysis posted on the issue; deferred with a recommended `--locale`
  design to be scoped in its own spec.
  Issue stays open as the tracker for that work.

### Design note: exclude model for explicitly-named files (#43/#24)

We considered making `.flowmarkignore` authoritative for explicitly-named files, but
that is surprising (an explicit `flowmark file.md` would silently do nothing) and offers
no override without editing the file — and no formatter behaves that way.
Surveying the ecosystem: **Black and Ruff** format explicitly-passed files even when
excluded and gate exclusions on `--force-exclude` (which `ruff-pre-commit` bakes into
its hooks); **dprint** keeps excludes authoritative but adds an `--excludes-override`
escape hatch.

Decision: **follow the Black/Ruff convention.** Exclusions (default patterns,
`--exclude`/`--extend-exclude`, `.gitignore`, `.flowmarkignore`) apply during directory
and glob discovery. A file named **explicitly** on the command line overrides exclusions
by default; `--force-exclude` opts exclusions (including `.flowmarkignore`) back in for
explicit files. The published pre-commit hooks set `--force-exclude`, exactly as
`ruff-pre-commit` does, so pre-commit honors a project’s `.flowmarkignore` without the
user thinking about it.

## Testing Strategy

- Unit tests next to each fix following repo conventions (`tests/test_*.py`).
- Idempotency assertions for #42 (format twice → identical).
- Golden test doc additions for #35 (and any wrapping changes) under `tests/testdocs/`.
- Full `make test` / `uv run pytest` plus `uv run basedpyright` and `ruff` clean before
  each commit.

## Rollout Plan

Standard release. The `--check` flag and `.pre-commit-hooks.yaml` are additive.
The #43 fix changes behavior for explicit-file invocations when exclusion options are
set — this is the documented/intended behavior, so it is a bug fix, not a breaking
change, but note it in release notes.

## Open Questions

- #24: Should the default pre-commit hook be `--auto` (aggressive: semantic + smart
  quotes + ellipses) or a more conservative arg set?
  Leaning `--auto` to match the README’s documented local hook.
- #21: Close as “works as intended”, or open a narrow follow-up for pipe-less table
  detection?
- #4: Confirm the `--locale` approach (vs discrete flags) before scoping a separate
  spec.

## References

- Issues: #42, #43, #44, #24, #35, #21, #4 on github.com/jlevy/flowmark
- `src/flowmark/cli.py`, `src/flowmark/reformat_api.py`,
  `src/flowmark/file_resolver/resolver.py`, `src/flowmark/formats/flowmark_markdown.py`,
  `src/flowmark/linewrapping/{line_wrappers,tag_handling,text_wrapping}.py`,
  `src/flowmark/typography/smartquotes.py`
- Prior art: `plan-2026-02-14-fix-smart-quoting-containers.md`,
  `plan-2026-02-15-file-discovery-and-globbing.md`

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
