"""
Agent skill installation for flowmark.

Installs the flowmark `SKILL.md` so AI coding agents can discover and use it. By default
this installs project-locally into both the portable `.agents/skills/flowmark/` location
(read by Codex, Gemini CLI, pi) and the `.claude/skills/flowmark/` mirror (Claude Code
reads only that path). A legacy single-base install (`agent_base`, e.g. `~/.claude`) is
kept for explicit/global installs.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

from strif import atomic_output_file

# Format version for all flowmark-generated artifacts (skill SKILL.md mirrors and
# the AGENTS.md block). One monotonically-increasing `fNN` across the project: every
# artifact stamps with the same current value; the `surface=` field distinguishes
# which artifact. Bump this whenever the shape of any generated artifact changes —
# a future flowmark uses the stamp to detect older shapes and safely upgrade them
# (and refuses to clobber a newer format it doesn't understand).
FLOWMARK_FORMAT = "f02"

# ─────────────────────────────────────────────────────────────────────────────
# CROSS-IMPLEMENTATION PORTING CONTRACT (read before porting to flowmark-rs)
#
# This file is auto-ported to the Rust implementation (github.com/jlevy/flowmark-rs)
# by an LLM following the rust-porting playbook. The version pin below and the
# `uvx --from <pkg>==<X.Y.Z>` bootstrap line in SKILL.md are PER-IMPLEMENTATION and
# MUST NOT be copied verbatim across the port:
#
#   - Python flowmark   pins  `uvx --from flowmark==<this package's version>`
#   - Rust   flowmark-rs pins  `uvx --from flowmark-rs==<flowmark-rs's own version>`
#
# `flowmark` and `flowmark-rs` are separate PyPI packages with INDEPENDENT, DIFFERENTLY
# NUMBERED release histories (the Python version is the reference and is often ahead).
# When porting, substitute BOTH the package name (`flowmark` -> `flowmark-rs`) AND the
# version (use flowmark-rs's own current release, NOT this file's number). Each pin must
# always be a real, installable release of *that* package. Pinning the Rust skill to a
# Python version number (or vice versa) is a bug: the `uvx --from` would resolve to the
# wrong package's release or fail outright.
# ─────────────────────────────────────────────────────────────────────────────

# Placeholder in the authored SKILL.md, replaced by `compose_skill` with a concrete
# version pin for the local-first runner fallback (see SKILL.md).
_VERSION_PLACEHOLDER = "__FLOWMARK_VERSION__"

# Concrete released-version pin baked into the committed repo-root discovery copy
# (`skills/flowmark/SKILL.md`), the artifact `npx skills add jlevy/flowmark` and
# skill indexers consume without flowmark needing to be pre-installed. Must be a
# real, PyPI-installable version — never a `<version>` placeholder or a `.dev`/
# local-suffix string — so the bootstrap `uvx --from flowmark==<X.Y.Z>` example
# in the discovery copy actually runs. Bump this together with the published
# version (see docs/publishing.md release checklist) and re-run `make format`.
# Rust port: this becomes flowmark-rs's own release version — see the porting
# contract above.
DISCOVERY_VERSION = "0.7.1"


def get_skill_content() -> str:
    """Read the authored SKILL.md template from package data.

    The returned text still contains the version placeholder; use `compose_skill` to
    render an installable/publishable copy.

    Raises:
        ImportError: If package resources cannot be accessed.
        FileNotFoundError: If SKILL.md cannot be found in package data.
    """
    # importlib.resources.files() is available in Python 3.9+
    # This project requires Python 3.10+, so no fallback needed
    from importlib.resources import files

    skill_file = files("flowmark").joinpath("skills/SKILL.md")
    return skill_file.read_text(encoding="utf-8")


# An exact-pinnable published PyPI release: a plain release segment (digits and
# dots), optionally a `.postN` suffix. PEP 440 dev (`.devN`), pre-release
# (`aN`/`bN`/`rcN`/`cN`), and local (`+<hash>`) versions — what editable/dev
# checkouts report (e.g. `0.7.1.dev29+c40ee1b`) — are deliberately rejected:
# they were never uploaded to PyPI, so an `uvx --from flowmark==<pin>` against
# them cannot resolve.
_PYPI_RELEASE_RE = re.compile(r"^\d+(?:\.\d+)*(?:\.post\d+)?$")


def is_pypi_release(version_str: str) -> bool:
    """Whether `version_str` is a real, exact-pinnable published PyPI release.

    Used to decide whether the installed version is safe to bake into the
    `uvx --from flowmark==<pin>` bootstrap line; see `flowmark_version`.
    """
    return bool(_PYPI_RELEASE_RE.match(version_str))


def flowmark_version() -> str:
    """The version to pin in the `uvx --from flowmark==<pin>` bootstrap line.

    Returns the installed version when it is a real PyPI release, otherwise the
    DISCOVERY_VERSION fallback. A dev or editable checkout reports a PEP 440
    dev/local version (e.g. `0.7.1.dev29+c40ee1b`) that was never published, so
    pinning uvx to it would fail to resolve; fall back to the last known
    published release instead. Same reasoning when flowmark isn't installed as a
    distribution at all.

    Rust port: this must query the flowmark-rs package and pin
    `flowmark-rs==<its own version>`, not `flowmark==…`. See the cross-implementation
    porting contract near DISCOVERY_VERSION.
    """
    from importlib.metadata import PackageNotFoundError, version

    try:
        installed = version("flowmark")
    except PackageNotFoundError:
        return DISCOVERY_VERSION
    return installed if is_pypi_release(installed) else DISCOVERY_VERSION


def compose_skill(version: str | None = None) -> str:
    """
    Render the SKILL.md template into a final skill document.

    `version` is substituted into the pinned-runner fallback. Pass an explicit string
    (e.g. `DISCOVERY_VERSION` for the committed discovery copy) for a stable, drift-free
    artifact; pass `None` to pin to the installed flowmark version (used when installing
    into an agent on a user's machine). Deterministic: same inputs always yield identical
    output.
    """
    pin = flowmark_version() if version is None else version
    return get_skill_content().replace(_VERSION_PLACEHOLDER, pin)


def get_docs_content() -> str:
    """Read README.md from the repository root.

    Returns:
        The content of the README.md file as a string.
    """
    # Find README.md relative to this file (src/flowmark/skill.py -> repo root)
    current_file = Path(__file__).resolve()
    repo_root = current_file.parent.parent.parent
    readme_path = repo_root / "README.md"

    if readme_path.exists():
        return readme_path.read_text(encoding="utf-8")

    # Fallback: return basic help text with link to online docs
    return """# Flowmark Documentation

Run `flowmark --help` for command-line options.

For full documentation, visit: https://github.com/jlevy/flowmark
"""


SKILL_DIRNAME = "flowmark"
# Project-local skill surfaces, relative to the project root.
PORTABLE_SKILL_REL = Path(".agents") / "skills" / SKILL_DIRNAME
CLAUDE_SKILL_REL = Path(".claude") / "skills" / SKILL_DIRNAME

# Surface identifiers. These match the `surface=` field on every generated artifact's
# format stamp (see FLOWMARK_FORMAT above) and the CLI's `--surfaces` flag values, so
# one vocabulary covers user-facing flags, on-disk metadata, and library calls.
SURFACE_PORTABLE = "portable"  # .agents/skills/flowmark/SKILL.md — Codex, Gemini CLI, pi
SURFACE_CLAUDE = "claude"  # .claude/skills/flowmark/SKILL.md — Claude Code mirror
SURFACE_AGENTS_MD = "agents-md"  # marker-bounded block in AGENTS.md
ALL_SURFACES = frozenset({SURFACE_PORTABLE, SURFACE_CLAUDE, SURFACE_AGENTS_MD})

_FORMAT_RE = re.compile(r"format=f(\d+)")


def _format_num() -> int:
    return int(FLOWMARK_FORMAT.lstrip("f"))


def _generated_marker() -> str:
    # No internal `.` so flowmark’s sentence-wrap leaves the line intact.
    return f"<!-- DO NOT EDIT — `flowmark --install-skill` (format={FLOWMARK_FORMAT} surface=skill-md) -->"


def render_skill_file(version: str | None = None) -> str:
    """
    The skill document to write to disk: `compose_skill` plus a `DO NOT EDIT` +
    format-version marker inserted after the YAML frontmatter (so frontmatter stays
    first and the marker survives a `flowmark --auto` pass).
    """
    composed = compose_skill(version)
    marker = _generated_marker()
    delimiter = "\n---\n"
    if composed.startswith("---\n") and (end := composed.find(delimiter, 4)) != -1:
        head = composed[: end + len(delimiter)]
        body = composed[end + len(delimiter) :]
        return f"{head}{marker}\n\n{body}"
    return f"{marker}\n\n{composed}"


def discovery_skill_text() -> str:
    """
    The committed repo-root discovery copy (`skills/flowmark/SKILL.md`) used by
    `npx skills add` and skill indexers. Pinned to `DISCOVERY_VERSION` (a real
    PyPI-installable release) so the `uvx --from flowmark==<X.Y.Z>` bootstrap line
    in the published copy is directly runnable without flowmark pre-installed.
    Install-time copies, by contrast, pin to the actually-installed version.
    """
    return render_skill_file(DISCOVERY_VERSION)


def _existing_format(path: Path) -> int | None:
    """Format number stamped on an existing generated file; 0 if unmarked; None if absent."""
    if not path.is_file():
        return None
    match = _FORMAT_RE.search(path.read_text(encoding="utf-8"))
    return int(match.group(1)) if match else 0


AGENTS_BEGIN_PREFIX = "<!-- BEGIN FLOWMARK INTEGRATION"
AGENTS_END_MARKER = "<!-- END FLOWMARK INTEGRATION -->"
_AGENTS_BLOCK_RE = re.compile(
    re.escape(AGENTS_BEGIN_PREFIX) + r".*?" + re.escape(AGENTS_END_MARKER), re.DOTALL
)
# Regex for the format stamp parsed off the AGENTS.md BEGIN marker line — anchored
# on the BEGIN prefix so a stray `format=fXX` elsewhere in the file can't fool the
# forward-compat guard. Same `format=fNN` shape as on every other surface.
_AGENTS_BEGIN_STAMP_RE = re.compile(re.escape(AGENTS_BEGIN_PREFIX) + r"\s+format=f(\d+)")


def agents_md_block(version: str | None = None) -> str:
    """
    The compact, marker-bounded flowmark block for a project's `AGENTS.md`.

    Short lines and no mid-document frontmatter, so a `flowmark --auto` pass over the
    host `AGENTS.md` leaves it unchanged. The format version lives on the begin-marker
    line so a later flowmark can upgrade or refuse it.
    """
    pin = flowmark_version() if version is None else version
    return (
        f"{AGENTS_BEGIN_PREFIX} format={FLOWMARK_FORMAT} surface=agents-md -->\n"
        "## flowmark\n"
        "\n"
        "Auto-format Markdown with `flowmark` for clean, semantic git diffs.\n"
        "\n"
        "- Run `flowmark --auto <files>` on Markdown you create or edit.\n"
        "- Run `flowmark --docs` for full usage and `flowmark --skill` for the skill.\n"
        f"- If `flowmark` is not on `PATH`, run `uvx --from flowmark=={pin} flowmark`.\n"
        "\n"
        f"{AGENTS_END_MARKER}"
    )


class InstallResult(NamedTuple):
    surface: str
    path: Path
    # "installed" | "updated" | "unchanged" | "blocked-newer"
    action: str


def _replace_all_flowmark_blocks(existing: str, block: str) -> str:
    """Replace every flowmark BEGIN/END region in `existing` with a single fresh block.

    Preserves user-authored content outside the markers; collapses duplicate or stale
    blocks (e.g. left behind by an older install) to exactly one current block at the
    location of the first removed region.
    """
    matches = list(_AGENTS_BLOCK_RE.finditer(existing))
    if not matches:
        return existing
    head = existing[: matches[0].start()]
    tail_parts = [
        existing[matches[i - 1].end() : matches[i].start()] for i in range(1, len(matches))
    ]
    tail_parts.append(existing[matches[-1].end() :])
    tail = "".join(tail_parts)
    return head + block + tail


def update_agents_md(path: Path, version: str | None = None) -> InstallResult:
    """
    Insert or refresh the flowmark block in `AGENTS.md`, preserving all content outside
    the markers. Idempotent; honors the forward-compatibility guard; collapses duplicate
    or stale flowmark blocks to one current block.
    """
    surface = "AGENTS.md (flowmark block)"
    existing = path.read_text(encoding="utf-8") if path.is_file() else None

    if existing is not None and (m := _AGENTS_BEGIN_STAMP_RE.search(existing)):
        if int(m.group(1)) > _format_num():
            return InstallResult(surface, path, "blocked-newer")

    block = agents_md_block(version)
    if existing is None or AGENTS_BEGIN_PREFIX not in existing:
        if not existing:
            new_content = block + "\n"
        else:
            sep = "\n" if existing.endswith("\n") else "\n\n"
            new_content = existing + sep + block + "\n"
    else:
        new_content = _replace_all_flowmark_blocks(existing, block)

    if existing == new_content:
        return InstallResult(surface, path, "unchanged")
    action = "updated" if existing is not None else "installed"
    with atomic_output_file(path, make_parents=True) as tmp:
        Path(tmp).write_text(new_content, encoding="utf-8")
    return InstallResult(surface, path, action)


def _write_surface(skill_dir: Path, surface: str, content: str) -> InstallResult:
    target = skill_dir / "SKILL.md"
    existing = _existing_format(target)
    # Forward-compatibility guard: never clobber an artifact stamped with a newer format.
    if existing is not None and existing > _format_num():
        return InstallResult(surface, target, "blocked-newer")
    if target.is_file() and target.read_text(encoding="utf-8") == content:
        return InstallResult(surface, target, "unchanged")
    action = "updated" if target.exists() else "installed"
    with atomic_output_file(target, make_parents=True) as tmp:
        Path(tmp).write_text(content, encoding="utf-8")
    return InstallResult(surface, target, action)


def install_skill(
    agent_base: str | None = None,
    *,
    project_root: Path | str | None = None,
    surfaces: frozenset[str] | None = None,
) -> list[InstallResult]:
    """
    Install the flowmark skill, version-pinned to the installed flowmark.

    With `agent_base` set, does a single-base install to `{agent_base}/skills/flowmark/`
    (explicit/global, e.g. `~/.claude`) and `surfaces` is ignored.

    Otherwise installs project-locally under `project_root` (default: cwd). `surfaces`
    selects which of the three project-local surfaces to write — any subset of
    {`SURFACE_PORTABLE`, `SURFACE_CLAUDE`, `SURFACE_AGENTS_MD`}. Pass `None` (default)
    for all three.

    Idempotent (re-running an up-to-date install reports "unchanged") and returns a
    per-surface result list.
    """
    try:
        content = render_skill_file()
    except (ImportError, FileNotFoundError) as e:
        print(f"\n✗ Error: Could not load skill content: {e}", file=sys.stderr)
        print("\nThis command requires flowmark to be installed as a package.", file=sys.stderr)
        print("Install with: uv tool install flowmark", file=sys.stderr)
        sys.exit(1)

    selected = ALL_SURFACES if surfaces is None else frozenset(surfaces)

    results: list[InstallResult] = []
    try:
        if agent_base is not None:
            base = Path(agent_base).resolve()
            results.append(_write_surface(base / "skills" / SKILL_DIRNAME, str(base), content))
        else:
            root = Path(project_root).resolve() if project_root is not None else Path.cwd()
            if SURFACE_PORTABLE in selected:
                results.append(
                    _write_surface(root / PORTABLE_SKILL_REL, ".agents/skills (portable)", content)
                )
            if SURFACE_AGENTS_MD in selected:
                results.append(update_agents_md(root / "AGENTS.md"))
            if SURFACE_CLAUDE in selected:
                results.append(
                    _write_surface(root / CLAUDE_SKILL_REL, ".claude/skills (Claude Code)", content)
                )
    except PermissionError as e:
        print(f"\n✗ Permission denied: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"\n✗ Installation failed: {e}", file=sys.stderr)
        sys.exit(1)

    _print_install_summary(results)
    return results


def _print_install_summary(results: list[InstallResult]) -> None:
    print("\nFlowmark skill installation:")
    for r in results:
        if r.action == "blocked-newer":
            print(f"  ‼️  {r.surface}: {r.path} was generated by a NEWER flowmark.")
            print("      Upgrade flowmark (e.g. `uv tool install --upgrade flowmark`) and retry.")
        else:
            print(f"  ✅ {r.action:<9} {r.surface}: {r.path}")
    print()


def main() -> None:
    """Command-line interface for skill installation.

    Can be run directly for testing:
        python -m flowmark.skill
        python -m flowmark.skill --agent-base ./.claude
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Install the cross-agent flowmark skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                        # Project-local: .agents/skills + .claude/skills + AGENTS.md
  %(prog)s --agent-base ~/.claude # Single explicit base (global): ~/.claude/skills
        """,
    )

    parser.add_argument(
        "--agent-base",
        dest="agent_base",
        metavar="DIR",
        help="explicit single-base install (e.g. ~/.claude); bypasses project-local default",
    )

    args = parser.parse_args()

    install_skill(agent_base=args.agent_base)


if __name__ == "__main__":
    main()
