# Feature: Comprehensive Cross-Agent Skill Support (Self-Documenting, Self-Installing)

**Date:** 2026-05-27 (last updated 2026-07-14)

**Author:** Flowmark maintainers

**Status:** Implemented and merged (PR #49); release-pin hardening and in-repo
dogfooding follow in PR #53. A Rust-first repository-migration reference and bundled
resource installation were added in the `fm-rfnx` follow-up.

## Overview

Flowmark already ships an agent skill (`src/flowmark/skills/SKILL.md`) and a Claude-only
installer (`flowmark --install-skill` writes to a single Claude agent base, default
`~/.claude`). This spec extends that into **genuine cross-agent** support: one
`flowmark` invocation installs a portable, self-documenting skill that Claude Code,
Codex, Gemini CLI, and other agents can discover, plus a public discovery bundle so
`npx skills add jlevy/flowmark@flowmark` works without proliferating separate skills for
formatting and repository setup.

It follows the tbd guideline `cli-agent-skill-patterns` (run
`tbd guidelines cli-agent-skill-patterns`), verified current against tbd v0.1.30.
Flowmark is a **Tier 1** tool in that guideline’s terms: a *single capability* (a
Markdown formatter) exposed as a pure skill invoked via a pinned runner.
It deliberately does **not** adopt the Tier 2 knowledge-injection machinery (no
`guidelines`/`shortcut` subcommand library, no format-migration engine); it only borrows
the lighter multi-agent *install* patterns (§6.6): a marker-bounded `AGENTS.md` block,
`DO NOT EDIT` and format-stamped generated artifacts, idempotent setup, and
deterministic, formatter-stable output.

## Goals

- **Cross-agent install** from one command: write the portable
  `.agents/skills/flowmark/SKILL.md` (read natively by Codex, Gemini CLI, pi), mirror it
  to `.claude/skills/flowmark/SKILL.md` (Claude Code reads only this path), and maintain
  a compact marker-bounded block in `AGENTS.md`.
- **Self-documenting**: the installed `SKILL.md` is portable (standard frontmatter and
  `allowed-tools`), states *what it does* and *when to use it*, and points to
  `flowmark --docs` for the full reference (progressive disclosure, §3.1).
- **Self-installing and idempotent**: surface-oriented `--surfaces` flag (values:
  `portable`, `claude`, `agents-md`, or the `all` alias); project-local by default;
  re-running makes no change when already current; user content outside markers is
  preserved.
- **Supply-chain-correct invocation**: the skill references a **pinned** flowmark
  version with a local-first fallback (`flowmark` on PATH →
  `uvx --from flowmark==<version>`), never an unpinned `@latest` (§6.7, §9; aligns with
  this repo’s `SUPPLY-CHAIN-SECURITY.md`). Also note the Rust port (`flowmark-rs`) as an
  alternative.
- **Public discovery**: generate a repo-root `skills/flowmark/` bundle from the same
  sources (drift-tested) so `npx skills add jlevy/flowmark@flowmark` and GitHub skill
  indexers pick it up (§6.8). The main Flowmark repository is the sole public
  skill-distribution and documentation source; flowmark-rs provides the recommended
  executable implementation.
- **One source of truth**: every surface (portable, Claude mirror, repo-root discovery
  copy, `AGENTS.md` block) is generated from a single authored body so they cannot
  drift. The Rust port vendors that authored bundle only for `--skill` /
  `--install-skill` compatibility and tests it byte-for-byte against its pinned Flowmark
  submodule; it does not publish a second repo-root discovery bundle.

## Non-Goals

- **MCP server.** A CLI is ~17x cheaper and more reliable than MCP when a CLI exists
  (§7); flowmark has one.
  No MCP surface.
- **Tier 2 knowledge library.** No `guidelines`/`shortcut`/`template` subcommands, no
  context-injection loop, no `prime` command.
  Flowmark is one capability, not a knowledge platform.
- **Format-migration engine.** A single format stamp and a forward-compatibility guard
  is enough; no multi-version migration framework (flowmark’s skill body is small and
  stable).
- **Per-agent rule files** (`.cursor/rules/*.mdc`, Windsurf rules, etc.)
  and multi-language docs.
- **Global/user installs by default.** Writing `~/.claude`, `~/.agents/skills/`, etc.
  stays an explicit, separately-flagged action, never something the project-local
  default does silently.
- **A second public skill bundle in flowmark-rs.** The Rust CLI may install its vendored
  runtime mirror, but discovery, `npx skills add`, and the main documentation all point
  to `jlevy/flowmark`.

## Background

- Prior spec `plan-2026-01-30-flowmark-agent-skill.md` delivered Phase 1 (Claude-only
  skill and `--skill`/`--install-skill`/`--agent-base`/`--docs`). That is **implemented
  today**; this spec is the cross-agent extension.
- `cli-agent-skill-patterns` §6.6 defines the portable-first multi-agent install:
  `.agents/skills/<tool>/` canonical and `.claude/skills/<tool>/` mirror and compact
  `AGENTS.md` block; copy (don’t symlink) the payload; mark generated files
  `DO NOT EDIT`; keep output deterministic and **stable under the repo’s own
  formatter**.
- That last point is sharp for flowmark: running `flowmark --auto` on a file with a
  mid-document `---/title:/---` fence rewrites it as a setext heading (this is why the
  repo now has a `.flowmarkignore` for `AGENTS.md`/`CLAUDE.md`). Any `AGENTS.md` block
  flowmark generates must therefore be flowmark-clean (no mid-document YAML frontmatter,
  canonical wrapping/quotes), so a format pass over it is a genuine no-op.
- The skill currently invokes `uvx flowmark@latest`, an unpinned runner the supply-chain
  guideline explicitly warns against; switching to a pinned invocation is part of this
  work.

## Design

### Approach

Introduce a single **compose step** that renders all install surfaces from one authored
source, then broaden the installer to write the portable location, the Claude mirror,
and the `AGENTS.md` block under a single surface-oriented `--surfaces` flag whose values
match the `surface=` field on every generated artifact’s format stamp.

### Components

- **`src/flowmark/skills/SKILL.md`**: the authored source body (standard frontmatter and
  `allowed-tools`), kept portable.
  Already exists; update its invocation examples to the pinned local-first form and keep
  the Python/Rust note.
- **`src/flowmark/skill.py`** extends:
  - `compose_skill(version) -> str`: render the final `SKILL.md` text, substituting the
    pinned version into the invocation examples.
    Deterministic.
  - `agents_md_block(version) -> str`: the compact marker-bounded block
    (`<!-- BEGIN FLOWMARK INTEGRATION format=f03 surface=agents-md -->` … `END`),
    emitted in flowmark’s own canonical format so `flowmark --auto` is a no-op on it.
    All generated artifacts (SKILL.md mirrors and this block) share a single
    monotonically-increasing `format=fNN` stamp; the `surface=` field distinguishes
    which artifact it is.
    Bump the single `FLOWMARK_FORMAT` constant whenever any artifact’s shape changes.
  - `install_skill(targets, project_root, agent_base, ...)`: write portable and Claude
    surfaces, update the `AGENTS.md` block in place (preserving content outside
    markers), idempotently; print an itemized summary (installed / upgraded / unchanged
    / user-owned / format-too-new).
  - A **forward-compatibility guard**: if an existing artifact’s `format=fNN` is newer
    than this build understands, stop and tell the user to upgrade flowmark rather than
    clobber it.
- **`src/flowmark/skills/references/project-setup.md`**: concise repository-adoption
  guidance for a pinned Rust runner, one project command, `.flowmarkignore`, auto-fixing
  commit hooks, CI policy, and disabling competing Markdown formatters.
- **`skills/flowmark/`** (repo root): generated discovery bundle for `npx skills add` /
  indexers, produced from the authored skill and reference at build/lint time; opens
  with a pinned bootstrap line so a registry install (Markdown only, no binary) still
  works.
- **CLI (`src/flowmark/cli.py`):** add `--surfaces=<list>`, a comma-separated subset of
  {`portable`, `claude`, `agents-md`} plus an `all` alias (default when omitted is all
  three). The values match the `surface=` field on every generated artifact’s format
  stamp, so the same vocabulary covers user-facing flags, on-disk metadata, and library
  calls. Reject unknown surfaces and `--surfaces` combined with `--agent-base` with exit
  code 2. Keep `--install-skill`, `--skill`, `--docs`, and `--agent-base` working;
  `--agent-base` continues to scope a custom/global base.

### API Changes

- New CLI flag (additive): `--surfaces` (values: `portable`, `claude`, `agents-md`,
  `all`; default = all three).
  Existing flags (`--install-skill`, `--skill`, `--docs`, `--agent-base`) unchanged in
  meaning.
- `skill.py` gains `compose_skill`, `agents_md_block`, and a richer `install_skill`
  signature (target set and project root).
  The old single-base behavior remains the `--agent-base` path.
- **Behavior change (deliberate):** the installed/printed `SKILL.md` switches its
  example invocations from `uvx flowmark@latest` to a pinned local-first form.
  Call this out in release notes under *Behavior and Compatibility Changes*.

### Generated-Artifact Handling

Use **commit and drift test** (the tbd mode): the authored sources live in
`src/flowmark/skills/`; the generated `skills/flowmark/` bundle (and any other generated
surface) is committed and a test regenerates and fails on drift.
Output must be byte-deterministic and flowmark-stable.

## Implementation Plan

### Phase 1: Compose and portable/Claude install and pinned invocation

- [x] Add `compose_skill(version)` to `skill.py`; substitute a pinned version into the
  invocation examples (local-first: `flowmark` → `uvx --from flowmark==<version>`).
- [x] Update `src/flowmark/skills/SKILL.md` examples to the pinned local-first form;
  keep the Python/Rust (`flowmark-rs`) note.
- [x] Tighten the skill `description` to the two-part rule (§4.2): front-load trigger
  keywords, state capability and when-to-use; keep `allowed-tools` minimally scoped
  (`Bash(flowmark:*)`, `Read`, `Write`).
- [x] Extend `install_skill` to write both `.agents/skills/flowmark/SKILL.md` (portable)
  and `.claude/skills/flowmark/SKILL.md` (mirror), project-local by default; copy the
  payload to both (no symlinks).
  Mark each `DO NOT EDIT` with the unified `format=fNN surface=skill-md` stamp (the same
  single `fNN` used on the AGENTS.md block).
- [x] Add `--surfaces` flag (values: `portable`, `claude`, `agents-md`, `all`; default =
  all three); reject unknown values and combination with `--agent-base`; keep
  `--agent-base` for custom/global installs.
- [x] Idempotency and itemized summary; forward-compat guard for too-new format stamps.
- [x] Tests: install paths, idempotent re-run, pinned-version substitution, summary.

### Phase 2: AGENTS.md block and public discovery and drift test

- [x] `agents_md_block(version)`: compact marker-bounded block, deterministic and
  **flowmark-`--auto`-stable** (no mid-document frontmatter).
  Install/update it in place, preserving user content; remove stale blocks; honor the
  forward-compat guard.
- [x] Generate the repo-root `skills/flowmark/SKILL.md` discovery copy from
  `compose_skill`; open it with a pinned bootstrap line.
  Keep it flowmark-`--auto`-stable (it is committed and formatted by `make format-docs`)
  rather than adding it to `.flowmarkignore`.
- [x] Validate the published skill: lint frontmatter (required `name`/`description`,
  length caps), confirm referenced links resolve (§4.4), and run
  `npx skills-ref validate skills/flowmark` before publishing (§6.8).
- [x] Drift test: regenerate all committed generated artifacts and fail on difference;
  assert `flowmark --auto` over the generated `AGENTS.md` block is a no-op.
- [x] Update README “Agent Use” section and `docs/` to document cross-agent install and
  `npx skills add jlevy/flowmark@flowmark`.

### Phase 3: Rust-first formatting and repository adoption

- [x] Keep one Flowmark skill and route repository adoption to one bundled reference.
- [x] Prefer pinned `uvx --from flowmark-rs==<version> flowmark` examples while
  retaining the Python reference for its library API or newer unported patches.
- [x] Cover one-file `--auto`, whole-tree migration, `.flowmarkignore`, Makefile wiring,
  auto-fixing commit hooks, and disabling Prettier or other competing Markdown owners.
- [x] Make ordinary Markdown formatting a local auto-fix rather than a main-build gate;
  retain drift checks for generated or byte-exact documentation contracts.
- [x] Install and forward-compatibility-check the complete skill bundle on portable,
  Claude, and explicit-base surfaces in both Python and Rust implementations.

## Testing Strategy

- **Unit**: `--surfaces` parsing (subset, alias, unknown, empty, mutually-exclusive with
  `--agent-base`), portable and mirror write paths, marker-bounded `AGENTS.md` update
  preserves surrounding content, format-stamp parsing, forward-compat guard triggers on
  a too-new stamp.
- **Golden**: `flowmark --skill` output (pinned invocation present, no `@latest`);
  generated `skills/flowmark/SKILL.md`. Extend the existing `verbose-docs.tryscript.md`
  suite.
- **Drift/determinism**: regenerate == committed (byte-identical); two runs identical;
  `flowmark --auto` over the generated `AGENTS.md` block produces no change.
- **Skill validation** (CI): frontmatter lint (required `name`/`description`, length
  caps) and a check that every link/file the skill references resolves (§4.4);
  `npx skills-ref validate skills/flowmark` on the discovery copy.
- **Activation (manual)**: positive prompts trigger the skill in Claude Code and Codex;
  nearby negative prompts do not; sandbox/read-only and no-network degrade with a clear
  message.

## Rollout Plan

Ships additively in a minor release.
The only compatibility note is the pinned-invocation switch in the skill body
(rendering-equivalent guidance, documented under *Behavior and Compatibility Changes*).
Existing `--install-skill`/`--agent-base` usage keeps working.

## Open Questions

- Exact-version pin vs minimum in the generated invocation?
  (Recommend exact `==<version>` per §6.7/§9; the version is the current package version
  at compose time.)
- Should the `AGENTS.md` block install only under `--codex`/detection, given Claude
  reads `CLAUDE.md` not `AGENTS.md`? (Recommend: AGENTS.md is part of the Codex/portable
  surface; Claude relies on the `.claude/skills/` mirror.)
- Do we add a global/user install flag (e.g. `--global`) distinct from project-local, or
  keep `--agent-base` as the explicit global path?
- Should the installed skill prefer the Rust `flowmark-rs` binary when present on PATH,
  or always document Python-first with Rust as a noted alternative?
- Wire the drift test into CI (`make`) and decide whether it blocks.

## References

- `tbd guidelines cli-agent-skill-patterns` (§3 SKILL.md, §4 descriptions, §6.6
  multi-agent install, §6.7 pinned invocation, §6.8 discovery, §9 security)
- Prior spec: `docs/project/specs/active/plan-2026-01-30-flowmark-agent-skill.md`
- `SUPPLY-CHAIN-SECURITY.md` (pinned-runner rule)
- Agent Skills standard: https://agentskills.io ; AGENTS.md: https://agents.md
- Rust port: https://github.com/jlevy/flowmark-rs

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
