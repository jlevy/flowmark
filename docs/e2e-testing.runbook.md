# End-to-End Testing Runbook

This is a step-by-step guide for an agent (or human) doing a **full validation pass** of
flowmark — the kind of pass worth running before a release, after large merges, or when
the developer or skill-install experience feels off.

It is intentionally written in prose, not as a script.
Anything that can be mechanized already lives in the automated test suite (`pytest` +
the tryscript golden tests), and this runbook points at those tests by name so you can
confirm coverage rather than re-checking by hand.
What remains here is the connective tissue and the checks CI genuinely cannot do: things
that need a real PyPI release, a real `uvx` fetch, or a real coding agent picking up the
installed skill.

Principle: **if you find a gap that a test could cover, add the test** (see
[development.md](development.md) for where tests live) rather than only documenting the
manual step.

## 0. Orientation: How Anyone — or Any Agent — Gets Oriented

The first thing to confirm is that flowmark is self-describing: someone who has only the
binary, with no docs open, can find out what it does and how to use it.

- `flowmark --help` — argument reference and common-usage examples.
- `flowmark --version` — version (see §1 for why this matters).
- `flowmark --skill` — prints the full `SKILL.md`. This is the contract: an agent
  pointed at flowmark runs this to learn how to use it and how to install the skill.
- `flowmark --docs` — prints the full README documentation.

Confirm the same works **without any install**, straight from PyPI, which is how most
agents will first encounter it:

```shell
uvx flowmark --help
uvx flowmark --skill
# Pinned (what the skill's own bootstrap line recommends — reproducible):
uvx --from flowmark==<X.Y.Z> flowmark --auto FILE
```

Pass criterion: a reader who runs `--skill` learns (a) how to format Markdown, (b) how
to install the skill into their agent, and (c) how to run flowmark via `uvx` if it is
not on `PATH`. If any of those is missing or wrong, the skill text needs fixing before
release.

## 1. Developer Environment Sanity

Set up and run the standard developer loop (full details in
[development.md](development.md)):

```shell
make install   # uv sync --all-extras
make           # format + install + lint + test
```

### Gotcha: stale virtualenv after a moved or renamed repo

`uv` console-script shebangs (`.venv/bin/codespell`, `ruff`, `basedpyright`, `flowmark`,
…) contain an **absolute** path to `.venv/bin/python`. If the repo directory is moved or
renamed, those shebangs point at a path that no longer exists.
The tools then fail to exec with a misleading error — Python surfaces a dead interpreter
as `FileNotFoundError: [Errno 2] No such file or directory: 'codespell'`, which looks
like a missing dependency but is not.
A plain `uv sync` does **not** fix it (the packages are installed; only the shebangs are
stale).

Recovery:

```shell
make clean && make      # make clean removes .venv; the rebuild writes correct shebangs
# or, equivalently:
rm -rf .venv && uv sync --all-extras
```

### Gotcha: stale dynamic version in an editable install

flowmark’s version is computed at build time from git tags by
[uv-dynamic-versioning](https://github.com/ninoseki/uv-dynamic-versioning/). `uv` caches
the built package keyed by source *content*, not by git HEAD, so advancing the git
history (for example past a new tag) does **not** automatically recompute the editable
install’s version. You can end up with `flowmark --version` reporting an old
`X.Y.Z.devN+<hash>` from a commit several tags back.

Confirm and, if needed, force a recompute:

```shell
git describe --tags                       # source of truth, e.g. v0.7.0-29-gc40ee1b
uv run flowmark --version                 # should agree (e.g. 0.7.1.dev29+...)
uv sync --reinstall-package flowmark      # rebuild + recompute if they disagree
```

This is a local developer-experience wrinkle only.
It does **not** affect published releases (those are built fresh from a clean tagged
checkout in CI), and it does not affect the `uvx` pin written into installed skills —
see §4.

## 2. Full Automated Suite (What CI Runs)

These are mechanized; run them and confirm green.
Do not hand-verify what they cover.

```shell
make lint                 # codespell, ruff check/format, basedpyright
make test                 # uv run pytest + the tryscript golden suite
make test-golden-coverage # tryscript coverage/quality gates
```

Notable suites:

- `tests/test_skill.py` — skill composition, install across surfaces, idempotency,
  forward-compat guard, and the `uvx` version-pin behavior (§4).
- `tests/test_skill_artifacts.py` — the committed discovery copy stays in sync with the
  generator and always pins a PyPI-installable version.
- `tests/tryscript/*.tryscript.md` — CLI golden tests, including `--install-skill`
  across every surface (`verbose-docs.tryscript.md`).

## 3. Skill Installation — Manual Cross-Agent Validation

flowmark installs its skill across **three surfaces**, so it works regardless of which
agent the user runs.
Know which is which:

| Surface | Path | Read by |
| --- | --- | --- |
| portable | `.agents/skills/flowmark/SKILL.md` | Codex, Gemini CLI, and other agents that read the portable location |
| Claude | `.claude/skills/flowmark/SKILL.md` | Claude Code (reads only this path) |
| AGENTS.md | a marker-bounded block in `AGENTS.md` | agents that read `AGENTS.md` for project guidance |

Default `--install-skill` writes all three; `--surfaces=portable,claude,agents-md` (or
`all`) selects a subset; `--agent-base DIR` does a single explicit/global install (e.g.
`~/.claude`).

> **Always run install tests in a scratch directory, never in the repo root.** Running
> `flowmark --install-skill` with the flowmark repo as the working directory writes the
> three surfaces into the repo itself (including modifying the tracked `AGENTS.md`). Use
> a `mktemp -d` sandbox:

```shell
SCRATCH=$(mktemp -d)
( cd "$SCRATCH" && git init -q . && flowmark --install-skill )
find "$SCRATCH" -name 'SKILL.md' -o -name 'AGENTS.md'
```

Verify, in the scratch directory:

1. **All three surfaces exist** and each `SKILL.md` starts with valid frontmatter
   (`---\nname: flowmark\n…`) so the agent can parse it.
2. **The format stamp is present** — each artifact carries `format=fNN surface=…` on its
   marker line. This is the forward-compatibility handle: a future flowmark uses it to
   upgrade older shapes and to refuse to clobber a newer shape it does not understand.
3. **Idempotency** — run `flowmark --install-skill` a second time.
   It must report `unchanged` for every surface and leave the files byte-identical.
   (Automated: `test_install_is_idempotent`, `test_update_is_idempotent`.)
4. **Forward-compat guard** — hand-edit one surface’s stamp to a higher number (e.g.
   `format=f99`) and re-run.
   It must report `blocked-newer` and leave that file untouched.
   (Automated: `test_forward_compat_guard_blocks_newer_format`,
   `test_update_guard_blocks_newer_format`.)
5. **AGENTS.md hygiene** — the block is marker-bounded, user content around it is
   preserved, duplicate stale blocks collapse to one, and a `flowmark --auto` pass over
   the host `AGENTS.md` leaves the block unchanged.
   (Automated: `test_update_*`, `test_block_is_flowmark_auto_stable`.)

## 4. Cross-Version Safety of the `uvx` Pin

This is the subtlest correctness property, so check it deliberately.

Every installed surface (and the committed discovery copy) contains a bootstrap line:

```
uvx --from flowmark==<X.Y.Z> flowmark
```

That pin **must always be a real, PyPI-installable release**. It must never be a
`.dev`/local version such as `0.7.1.dev29+c40ee1b`, because that version was never
uploaded to PyPI and the `uvx` command would fail to resolve.
There are two independent sources of the pin, each with its own guard:

- **Committed discovery copy** (`skills/flowmark/SKILL.md`, consumed by
  `npx skills add jlevy/flowmark`): pinned to the `DISCOVERY_VERSION` constant in
  [src/flowmark/skill.py](../src/flowmark/skill.py).
  Bump it as part of every release — see the checklist in
  [publishing.md](publishing.md).
  Guarded by `test_skill_artifacts.py::test_discovery_copy_has_resolvable_version_pin`.
- **Install-time copies** (`flowmark --install-skill` on a user’s machine): pinned to
  the *installed* version via `flowmark_version()`. When flowmark is running from a dev
  or editable checkout, the installed version is a `.dev`/local string;
  `flowmark_version()` detects this (`is_pypi_release()`) and falls back to
  `DISCOVERY_VERSION` so the emitted pin is still installable.
  Guarded by `TestVersionPin` in `tests/test_skill.py`.

Manual confirmation from a dev checkout:

```shell
SCRATCH=$(mktemp -d)
( cd "$SCRATCH" && flowmark --install-skill >/dev/null
  grep -h 'uvx --from flowmark==' .agents/skills/flowmark/SKILL.md AGENTS.md )
# Expect the released pin (e.g. flowmark==0.7.0), NOT the dev version,
# even though `flowmark --version` reports the dev version.
```

## 5. Real End-to-End via PyPI (Genuinely Manual, Post-Release)

CI cannot test against a release that does not exist yet.
After publishing (see [publishing.md](publishing.md)), confirm the real path that users
and agents take:

1. **Fresh `uvx` from PyPI** — on a machine without flowmark installed:

   ```shell
   uvx --from flowmark==<JUST_RELEASED> flowmark --auto sample.md
   ```

   This exercises the exact bootstrap line the skill hands to agents.

2. **Real agent pickup** — in a scratch project, run `flowmark --install-skill`, then
   open that project in **Claude Code** and in **Codex** (or another portable-surface
   agent) and confirm each discovers the flowmark skill and can format a Markdown file
   on request. This is the ultimate check that the surface paths and frontmatter are
   right for each agent.

## 6. Pre-Release Gate (Condensed)

Before tagging a release, confirm:

- [ ] `make` is fully green (lint + pytest + golden), from a clean `.venv` if the repo
  was recently moved (§1).
- [ ] `flowmark --version` agrees with `git describe --tags` (§1).
- [ ] `DISCOVERY_VERSION` bumped to the about-to-be-released version and `make format`
  re-run, so the committed discovery copy pins the new release (§4 and
  [publishing.md](publishing.md)).
- [ ] Skill install verified in a scratch dir: three surfaces, idempotent,
  forward-compat guard, AGENTS.md hygiene (§3).
- [ ] `uvx` pin is a real release on both the discovery copy and a dev-checkout install
  (§4).
- [ ] After publishing: real `uvx`-from-PyPI run and real agent pickup (§5).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
