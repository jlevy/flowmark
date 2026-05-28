# Feature: Comprehensive Cross-Agent Skill Support (Self-Documenting, Self-Installing)

**Date:** 2026-05-27 (last updated 2026-05-27)

**Author:** Flowmark maintainers

**Status:** Draft

## Overview

Flowmark already ships an agent skill (`src/flowmark/skills/SKILL.md`) and a Claude-only
installer (`flowmark --install-skill` writes to a single Claude agent base, default
`~/.claude`). This spec extends that into **genuine cross-agent** support: one
`flowmark` invocation installs a portable, self-documenting skill that Claude Code,
Codex, Gemini CLI, and other agents can discover, plus a public discovery copy so
`npx skills add jlevy/flowmark` works.

It follows the tbd guideline `cli-agent-skill-patterns` (run
`tbd guidelines cli-agent-skill-patterns`), verified current against tbd v0.1.30.
Flowmark is a **Tier 1** tool in that guideline’s terms — a *single capability* (a
Markdown formatter) exposed as a pure skill invoked via a pinned runner.
It deliberately does **not** adopt the Tier 2 knowledge-injection machinery (no
`guidelines`/`shortcut` subcommand library, no format-migration engine); it only borrows
the lighter multi-agent *install* patterns (§6.6): a marker-bounded `AGENTS.md` block,
`DO NOT EDIT` + format-stamped generated artifacts, idempotent setup, and deterministic,
formatter-stable output.

## Goals

- **Cross-agent install** from one command: write the portable
  `.agents/skills/flowmark/SKILL.md` (read natively by Codex, Gemini CLI, pi), mirror it
  to `.claude/skills/flowmark/SKILL.md` (Claude Code reads only this path), and maintain
  a compact marker-bounded block in `AGENTS.md`.
- **Self-documenting**: the installed `SKILL.md` is portable (standard frontmatter +
  `allowed-tools`), states *what it does* and *when to use it*, and points to
  `flowmark --docs` for the full reference (progressive disclosure, §3.1).
- **Self-installing and idempotent**: tri-state targeting flags (`--all`, `--claude`,
  `--codex`, `--skip-*`); project-local by default; re-running makes no change when
  already current; user content outside markers is preserved.
- **Supply-chain-correct invocation**: the skill references a **pinned** flowmark
  version with a local-first fallback (`flowmark` on PATH →
  `uvx --from flowmark==<version>`), never an unpinned `@latest` (§6.7, §9; aligns with
  this repo’s `SUPPLY-CHAIN-SECURITY.md`). Also note the Rust port (`flowmark-rs`) as an
  alternative.
- **Public discovery**: generate a repo-root `skills/flowmark/SKILL.md` from the same
  source (drift-tested) so `npx skills add jlevy/flowmark` and GitHub skill indexers
  pick it up (§6.8).
- **One source of truth**: every surface (portable, Claude mirror, repo-root discovery
  copy, `AGENTS.md` block) is generated from a single authored body so they cannot
  drift.

## Non-Goals

- **MCP server.** A CLI is ~17x cheaper and more reliable than MCP when a CLI exists
  (§7); flowmark has one.
  No MCP surface.
- **Tier 2 knowledge library.** No `guidelines`/`shortcut`/`template` subcommands, no
  context-injection loop, no `prime` command — flowmark is one capability, not a
  knowledge platform.
- **Format-migration engine.** A single format stamp + a forward-compatibility guard is
  enough; no multi-version migration framework (flowmark’s skill body is small and
  stable).
- **Per-agent rule files** (`.cursor/rules/*.mdc`, Windsurf rules, etc.)
  and multi-language docs.
- **Global/user installs by default.** Writing `~/.claude`, `~/.agents/skills/`, etc.
  stays an explicit, separately-flagged action, never something the project-local
  default does silently.

## Background

- Prior spec `plan-2026-01-30-flowmark-agent-skill.md` delivered Phase 1 (Claude-only
  skill + `--skill`/`--install-skill`/`--agent-base`/`--docs`). That is **implemented
  today**; this spec is the cross-agent extension.
- `cli-agent-skill-patterns` §6.6 defines the portable-first multi-agent install:
  `.agents/skills/<tool>/` canonical + `.claude/skills/<tool>/` mirror + compact
  `AGENTS.md` block; copy (don’t symlink) the payload; mark generated files
  `DO NOT EDIT`; keep output deterministic and **stable under the repo’s own
  formatter**.
- That last point is sharp for flowmark: running `flowmark --auto` on a file with a
  mid-document `---/title:/---` fence rewrites it as a setext heading (this is why the
  repo now has a `.flowmarkignore` for `AGENTS.md`/`CLAUDE.md`). Any `AGENTS.md` block
  flowmark generates must therefore be flowmark-clean — no mid-document YAML
  frontmatter, canonical wrapping/quotes — so a format pass over it is a genuine no-op.
- The skill currently invokes `uvx flowmark@latest`, an unpinned runner the supply-chain
  guideline explicitly warns against; switching to a pinned invocation is part of this
  work.

## Design

### Approach

Introduce a single **compose step** that renders all install surfaces from one authored
source, then broaden the installer to write the portable location, the Claude mirror,
and the `AGENTS.md` block under tri-state targeting flags.

### Components

- **`src/flowmark/skills/SKILL.md`** — the authored source body (standard frontmatter +
  `allowed-tools`), kept portable.
  Already exists; update its invocation examples to the pinned local-first form and keep
  the Python/Rust note.
- **`src/flowmark/skill.py`** — extend:
  - `compose_skill(version) -> str`: render the final `SKILL.md` text, substituting the
    pinned version into the invocation examples.
    Deterministic.
  - `agents_md_block(version) -> str`: the compact marker-bounded block
    (`<!-- BEGIN FLOWMARK INTEGRATION format=f02 surface=agents-md -->` … `END`),
    emitted in flowmark’s own canonical format so `flowmark --auto` is a no-op on it.
    All generated artifacts (SKILL.md mirrors and this block) share a single
    monotonically-increasing `format=fNN` stamp; the `surface=` field distinguishes
    which artifact it is.
    Bump the single `FLOWMARK_FORMAT` constant whenever any artifact’s shape changes.
  - `install_skill(targets, project_root, agent_base, ...)`: write portable + Claude
    surfaces, update the `AGENTS.md` block in place (preserving content outside
    markers), idempotently; print an itemized summary (installed / upgraded / unchanged
    / user-owned / format-too-new).
  - A **forward-compatibility guard**: if an existing artifact’s `format=fNN` is newer
    than this build understands, stop and tell the user to upgrade flowmark rather than
    clobber it.
- **`skills/flowmark/SKILL.md`** (repo root) — generated discovery copy for
  `npx skills add` / indexers, produced from `compose_skill` at build/lint time; opens
  with a pinned bootstrap line so a registry install (Markdown only, no binary) still
  works.
- **CLI (`src/flowmark/cli.py`)** — add tri-state targeting: `--all`, `--claude`,
  `--codex`, `--skip-claude`, `--skip-codex` (avoid Commander-style `--no-*`). Keep
  `--install-skill`, `--skill`, `--docs`, and `--agent-base` working; `--agent-base`
  continues to scope a custom/global base.

### API Changes

- New CLI flags (additive): `--all`, `--claude`, `--codex`, `--skip-claude`,
  `--skip-codex`. Existing flags unchanged in meaning.
- `skill.py` gains `compose_skill`, `agents_md_block`, and a richer `install_skill`
  signature (target set + project root).
  The old single-base behavior remains the `--agent-base` path.
- **Behavior change (deliberate):** the installed/printed `SKILL.md` switches its
  example invocations from `uvx flowmark@latest` to a pinned local-first form.
  Call this out in release notes under *Behavior and Compatibility Changes*.

### Generated-Artifact Handling

Use **commit + drift test** (the tbd mode): the authored source lives in
`src/flowmark/skills/SKILL.md`; the generated `skills/flowmark/SKILL.md` (and any other
generated surface) is committed and a test regenerates and fails on drift.
Output must be byte-deterministic and flowmark-stable.

## Implementation Plan

### Phase 1: Compose + portable/Claude install + pinned invocation

- [ ] Add `compose_skill(version)` to `skill.py`; substitute a pinned version into the
  invocation examples (local-first: `flowmark` → `uvx --from flowmark==<version>`).
- [ ] Update `src/flowmark/skills/SKILL.md` examples to the pinned local-first form;
  keep the Python/Rust (`flowmark-rs`) note.
- [ ] Tighten the skill `description` to the two-part rule (§4.2): front-load trigger
  keywords, state capability + when-to-use; keep `allowed-tools` minimally scoped
  (`Bash(flowmark:*)`, `Read`, `Write`).
- [ ] Extend `install_skill` to write both `.agents/skills/flowmark/SKILL.md` (portable)
  and `.claude/skills/flowmark/SKILL.md` (mirror), project-local by default; copy the
  payload to both (no symlinks).
  Mark each `DO NOT EDIT` with the unified `format={FLOWMARK_FORMAT} surface=skill-md`
  stamp (same single `fNN` used on the AGENTS.md block).
- [ ] Add tri-state CLI flags (`--all`, `--claude`, `--codex`, `--skip-*`); default to
  detection-based, project-local; keep `--agent-base` for custom/global.
- [ ] Idempotency + itemized summary; forward-compat guard for too-new format stamps.
- [ ] Tests: install paths, idempotent re-run, pinned-version substitution, summary.

### Phase 2: AGENTS.md block + public discovery + drift test

- [ ] `agents_md_block(version)`: compact marker-bounded block, deterministic and
  **flowmark-`--auto`-stable** (no mid-document frontmatter).
  Install/update it in place, preserving user content; remove stale blocks; honor the
  forward-compat guard.
- [ ] Generate the repo-root `skills/flowmark/SKILL.md` discovery copy from
  `compose_skill`; open it with a pinned bootstrap line.
  Keep it flowmark-`--auto`-stable (it is committed and formatted by `make format-docs`)
  rather than adding it to `.flowmarkignore`.
- [ ] Validate the published skill: lint frontmatter (required `name`/`description`,
  length caps), confirm referenced links resolve (§4.4), and run
  `npx skills-ref validate skills/flowmark` before publishing (§6.8).
- [ ] Drift test: regenerate all committed generated artifacts and fail on difference;
  assert `flowmark --auto` over the generated `AGENTS.md` block is a no-op.
- [ ] Update README “Agent Use” section and `docs/` to document cross-agent install and
  `npx skills add jlevy/flowmark`.

## Testing Strategy

- **Unit**: target resolution (tri-state), portable + mirror write paths, marker-bounded
  `AGENTS.md` update preserves surrounding content, format-stamp parsing, forward-compat
  guard triggers on a too-new stamp.
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
