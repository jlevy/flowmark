## Publishing Releases

This is how to publish a Python package to [**PyPI**](https://pypi.org/) from GitHub
Actions, when using the
[**simple-modern-uv**](https://github.com/jlevy/simple-modern-uv) template.

Thanks to
[the dynamic versioning plugin](https://github.com/ninoseki/uv-dynamic-versioning/) and
the
[`publish.yml` workflow](https://github.com/jlevy/simple-modern-uv/blob/main/template/.github/workflows/publish.yml),
you can simply create tagged releases (using standard format for the tag name, e.g.
`v0.1.0`) on GitHub and the tag will trigger a release build, which then uploads it to
PyPI.

### First-Time Setup

This part is a little confusing the first time.
Here is the simplest way to do it.
For the purposes of this example replace OWNER and PROJECT with the right values.

1. **Get a PyPI account** at [pypi.org](https://pypi.org/) and sign in.

2. **Pick a name for the project** that isn’t already taken.

   - Go to `https://pypi.org/project/PROJECT` to see if another project with that name
     already exits.

   - If needed, update your `pyproject.toml` with the correct name.

3. **Authorize** your repository to publish to PyPI:

   - Go to [the publishing settings page](https://pypi.org/manage/account/publishing/).

   - Find “Trusted Publisher Management” and register your GitHub repo as a new
     “pending” trusted publisher.

   - Enter the project name, repo owner, repo name, and `publish.yml` as the workflow
     name. (You can leave the “environment name” field blank.)

4. **Create a release** on GitHub:

   - Commit code and make sure it’s running correctly.

   - Go to your GitHub project page, then click on Actions tab.

   - Confirm all tests are passing in the last CI workflow.
     (If you want, you can even publish this template when it’s empty as just a stub
     project, to try all this out.)

   - Go to your GitHub project page, click on Releases.

   - Fill in the tag and the release name.
     Select to create a new tag, and pick a version.
     A good option is `v0.1.0`. (It’s wise to have it start with a `v`.)

   - Submit to create the release.

5. **Confirm it publishes to PyPI**

   - Watch for the release workflow in the GitHub Actions tab.

   - If it succeeds, you should see it appear at `https://pypi.org/project/PROJECT`.

### Publishing Subsequent Releases

Follow this checklist for each new release.

#### Pre-Release Checklist

1. **Verify all changes are committed and pushed:**

   ```shell
   git status
   git log origin/main..HEAD  # should be empty if pushed
   ```

2. **Run linting and tests locally:**

   ```shell
   make lint
   make test
   ```

3. **Confirm CI is passing:**

   ```shell
   gh run list --limit 3
   ```

   Or check the Actions tab on GitHub.

4. **Determine the new version number:**

   ```shell
   # Check current/latest version:
   gh release list --limit 1
   ```

   Use [semantic versioning](https://semver.org/):

   - **Patch** (e.g., `v0.5.8` → `v0.5.9`): Bug fixes, minor changes

   - **Minor** (e.g., `v0.5.9` → `v0.6.0`): New features, backward-compatible

   - **Major** (e.g., `v0.6.0` → `v1.0.0`): Breaking changes

5. **Bump the skill’s `uvx` bootstrap pin (one source of truth):**

   The repo-root `skills/flowmark/SKILL.md` (shipped to `npx skills add jlevy/flowmark`
   users who do *not* have flowmark pre-installed) and the README’s runner examples all
   pin `uvx --from flowmark==<X.Y.Z>`. That pin must reference a real, PyPI-installable
   release — never a `<version>` placeholder or a `.dev`/local-suffix string — and it
   must be the release you are about to cut, or agents bootstrap a stale flowmark.

   There is exactly **one** place to change: the `DISCOVERY_VERSION` constant in
   `src/flowmark/skill.py`. `make format` propagates it to every shipped artifact (the
   discovery copy via `generate-skill-discovery.py`; the README runner examples via the
   `__FLOWMARK_VERSION__` placeholder in `docs/shared/flowmark-readme-shared.md`, which
   `generate-python-readme.py` substitutes).
   Bump it, regenerate, verify, and commit before tagging:

   ```shell
   # In src/flowmark/skill.py: DISCOVERY_VERSION = "<NEW_TAG without leading v>"
   make format
   make check-release-pin VERSION=<NEW_TAG without leading v>   # must print "Release pin OK"
   git add -A
   git commit -m "skill: bump DISCOVERY_VERSION to vX.Y.Z"
   ```

   Guards (no stale or non-resolvable pin can ship):

   - `tests/test_skill_artifacts.py::test_discovery_copy_has_resolvable_version_pin` —
     the pin is a real PyPI release, not a placeholder/dev string.
   - `tests/test_skill_artifacts.py::test_shipped_artifacts_pin_discovery_version` —
     every shipped artifact pins exactly `DISCOVERY_VERSION` (catches a forgotten
     `make format`).
   - `scripts/check-release-pin.py` (run in `publish.yml` against the release tag, and
     via `make check-release-pin`) — fails the publish if `DISCOVERY_VERSION` does not
     match the release being cut.

#### Create the Release

6. **Generate release notes content:**

   Review changes since the last release:

   ```shell
   # Get the last release tag:
   LAST_TAG=$(gh release list --limit 1 --json tagName -q '.[0].tagName')

   # View commits since last release:
   git log ${LAST_TAG}..HEAD --oneline

   # View full diff:
   git diff ${LAST_TAG}..HEAD
   ```

7. **Create the release with `gh`:**

   ```shell
   NEW_TAG="vX.Y.Z"  # Replace with actual version
   LAST_TAG=$(gh release list --limit 1 --json tagName -q '.[0].tagName')

   gh release create "${NEW_TAG}" \
     --title "${NEW_TAG}" \
     --notes "$(cat <<'EOF'
   ## What's Changed

   [Summarize changes here—see format guide below]

   ### Full Changelog

   https://github.com/OWNER/PROJECT/compare/${LAST_TAG}...${NEW_TAG}
   EOF
   )"
   ```

   Alternatively, use `--generate-notes` for GitHub’s auto-generated notes, or
   `--notes-file FILENAME` to read from a file.

8. **Verify the release published successfully:**

   ```shell
   # Check the release workflow:
   gh run list --workflow=publish.yml --limit 1

   # Verify on PyPI (may take a minute):
   # https://pypi.org/project/PROJECT
   ```

### Release Notes Format

Use this structure for release notes.
List sections in this order, from most to least disruptive, and **omit any section that
is empty** (do not pad with “none”):

```markdown
## What's Changed

### Breaking Changes

**Short title of breaking change**

What was removed or changed incompatibly (API signature, CLI flag, removed behavior) and
how to migrate.

### Behavior and Compatibility Changes

**Short title of behavior change**

A change to default *output* or runtime behavior that is not an API break. For example,
the formatter now produces different (but valid) Markdown for some input, line breaks
land differently, or default option values changed. Say exactly which inputs are
affected and whether the result is rendering-equivalent.

### New Features and API

**Short title of feature or new public API**

New capabilities, new CLI flags, and new public functions/types. Additive only: anything
that *changes* existing behavior belongs above, not here.

### Bug Fixes

**Short title of fix**

What was fixed and why it matters. If the fix changes output for previously-broken input,
note that here (it is a fix, not a behavior change) but be explicit that output differs.

### Full Changelog

https://github.com/OWNER/PROJECT/compare/vPREVIOUS...vNEW
```

Guidelines:

- Use `## What's Changed` as the top-level heading.

- The four categories are deliberately distinct.
  Classify each change by asking, in order:

  1. Does it remove or incompatibly change a public API, CLI flag, or documented
     behavior? → **Breaking Changes**.

  2. For the same input, does the tool now produce different output or behave
     differently (even if valid and rendering-equivalent), or did a default change?
     → **Behavior and Compatibility Changes**. This is the category most often missed: a
     formatter whose output drifts between versions is a compatibility concern (diffs,
     golden tests, re-flowed files) even when nothing is strictly “broken”.

  3. Is it purely additive (new flag, new public function/type, new capability, with no
     change to existing behavior)?
     → **New Features and API**.

  4. Did it correct previously-wrong or broken output?
     → **Bug Fixes** (and state plainly when output changes as a result).

- When in doubt between *Behavior and Compatibility* and *Bug Fixes*, prefer **Behavior
  and Compatibility** and explain why: readers diffing reformatted files care about
  *any* output change regardless of intent.

- Describe the **aggregate delta** between the previous release and this one, not
  individual commits. If a feature was added and then fixed before release, describe the
  feature as it now works rather than listing the intermediate fix separately.

- Skip **internal-only** changes that users never see: CI/tooling, pure refactors,
  test-only work, and dependency or doc housekeeping.

- Use `**bold**` for short titles of individual changes.

- Include technical details only when helpful for users.

- Always include the Full Changelog compare link at the end.

- For small releases, a simple bullet list is acceptable, but still group it under these
  headings so behavior/compatibility changes are never buried among features or fixes.

* * *

*This file was built with
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).*

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
