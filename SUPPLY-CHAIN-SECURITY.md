# Supply-Chain Security Policy

This repo follows a supply-chain hardening policy.
**Read this before adding or upgrading any dependency.** The full cross-ecosystem policy
and rationale are in the
[Supply Chain Hardening guidebook](https://github.com/jlevy/supply-chain-hardening);
this file is the repo-specific summary for a `uv`-managed Python project.

## The default: a 14-day cool-off

**Never add or upgrade to a package version less than 14 days old** unless a documented
exception applies.
Malicious releases are typically detected and yanked within minutes to
days, so waiting costs only slightly staler dependencies.

With `uv`, gate resolution by publish date:

```bash
export UV_EXCLUDE_NEWER="14 days"   # exclude anything published in the last 14 days
uv lock --upgrade                   # re-resolve under the cool-off
```

To check one version’s publish time before pinning it:

```bash
uv pip index versions <pkg>         # or: curl -s https://pypi.org/pypi/<pkg>/json
```

The cool-off applies to runtime `dependencies` **and** the `[dependency-groups] dev`
group (build/test tooling runs with full privileges and is historically a more dangerous
vector). Pins already in `uv.lock` before this policy are grandfathered until their next
planned upgrade.

## Install rules

1. **Never install unthinkingly.** Confirm the package is needed, the name is spelled
   correctly (typosquats are common), and the version clears the cool-off.
2. **Prefer wheels; be wary of sdist builds.** A source build runs arbitrary code.
   Set `UV_NO_BUILD_ISOLATION=0` defaults aside and prefer binary wheels; review any
   package that must build from sdist.
3. **Commit the lockfile; install frozen.** `uv.lock` is committed and CI runs
   `uv sync --frozen`. Never let an upgrade slip in unreviewed — treat a `uv.lock` diff
   like a code diff.
4. **Audit after changes.** Run `uv run pip-audit` (also wired into CI) and address
   findings before continuing.
5. **Don’t update for its own sake.** The safest update is the one you skip.
   Bump only for a concrete reason (a needed fix or a CVE patch), not on a schedule.
6. **No unpinned zero-install runners.** Pin `uvx`/`npx`/`pnpm dlx` invocations to an
   explicit `@version` (e.g. CI and the `Makefile` pin `tryscript`), never `@latest`.
7. **No `curl | sh` from untrusted sources.** Verify the installer URL belongs to the
   documented project; check checksums/signatures where available.

## Exceptions

When a version inside the 14-day window is genuinely needed (e.g. a same-week CVE
patch):

- State the reason in the commit/PR — the CVE ID or vulnerability description and a
  `Reviewed-by:` sign-off.
- Pin the exact `package==version` (not a range) and verify it against OSV / GHSA / the
  maintainer postmortem.
- Leave a marker next to the pin and a follow-up to confirm the version was not yanked.

**Agents never self-approve an exception** — prepare the record and a human signs off.

## What this does and doesn’t cover

A cool-off plus lockfile discipline neutralizes the dominant fast-yanked-incident
pattern. It does **not** stop long-lived typosquats, a lockfile that already captured a
bad version, payloads that fire on import/build, or publish-pipeline compromises.
Publishing here uses PyPI OIDC trusted publishing (`publish.yml`); keep release tooling
and GitHub Actions reviewed.
