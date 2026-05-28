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

# Format version for all flowmark-generated artifacts (skill SKILL.md mirrors and
# the AGENTS.md block). One monotonically-increasing `fNN` across the project: every
# artifact stamps with the same current value; the `surface=` field distinguishes
# which artifact. Bump this whenever the shape of any generated artifact changes —
# a future flowmark uses the stamp to detect older shapes and safely upgrade them
# (and refuses to clobber a newer format it doesn't understand).
FLOWMARK_FORMAT = "f02"

# Placeholder in the authored SKILL.md, replaced by `compose_skill` with a concrete
# version pin for the local-first runner fallback (see SKILL.md).
_VERSION_PLACEHOLDER = "__FLOWMARK_VERSION__"

# Literal pin shown in committed/published artifacts (the in-repo discovery copy), where
# embedding a concrete version would churn on every release. Real installs substitute the
# installed version instead.
DOC_VERSION_PIN = "<version>"


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


def flowmark_version() -> str:
    """The installed flowmark version, or the doc placeholder if it can't be determined."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("flowmark")
    except PackageNotFoundError:
        return DOC_VERSION_PIN


def compose_skill(version: str | None = None) -> str:
    """
    Render the SKILL.md template into a final skill document.

    `version` is substituted into the pinned-runner fallback. Pass an explicit string
    (e.g. `DOC_VERSION_PIN` for the committed discovery copy) for a stable, drift-free
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
    `npx skills add` and skill indexers. Pinned to the stable `<version>` placeholder so
    it never churns across releases; install-time copies pin the real installed version.
    """
    return render_skill_file(DOC_VERSION_PIN)


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
_AGENTS_FORMAT_RE = re.compile(re.escape(AGENTS_BEGIN_PREFIX) + r"\s+format=f(\d+)")


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


def update_agents_md(path: Path, version: str | None = None) -> InstallResult:
    """
    Insert or refresh the flowmark block in `AGENTS.md`, preserving all content outside
    the markers. Idempotent; honors the forward-compatibility guard.
    """
    surface = "AGENTS.md (flowmark block)"
    existing = path.read_text(encoding="utf-8") if path.is_file() else None

    if existing is not None and (m := _AGENTS_FORMAT_RE.search(existing)):
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
        new_content = _AGENTS_BLOCK_RE.sub(lambda _: block, existing, count=1)

    if existing == new_content:
        return InstallResult(surface, path, "unchanged")
    action = "updated" if existing is not None else "installed"
    path.write_text(new_content, encoding="utf-8")
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
    skill_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return InstallResult(surface, target, action)


def install_skill(
    agent_base: str | None = None,
    *,
    project_root: Path | str | None = None,
    claude: bool = True,
    codex: bool = True,
) -> list[InstallResult]:
    """
    Install the flowmark skill, version-pinned to the installed flowmark.

    With `agent_base` set, does a single-base install to `{agent_base}/skills/flowmark/`
    (explicit/global, e.g. `~/.claude`). Otherwise installs project-locally under
    `project_root` (default: cwd): the portable `.agents/skills/flowmark/` surface when
    `codex` is set and the `.claude/skills/flowmark/` mirror when `claude` is set.

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

    results: list[InstallResult] = []
    try:
        if agent_base is not None:
            base = Path(agent_base).resolve()
            results.append(_write_surface(base / "skills" / SKILL_DIRNAME, str(base), content))
        else:
            root = Path(project_root).resolve() if project_root is not None else Path.cwd()
            if codex:
                results.append(
                    _write_surface(root / PORTABLE_SKILL_REL, ".agents/skills (portable)", content)
                )
                results.append(update_agents_md(root / "AGENTS.md"))
            if claude:
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
        description="Install flowmark Claude Code skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                        # Project-local: .agents/skills + .claude/skills
  %(prog)s --agent-base ~/.claude # Single explicit base (global): ~/.claude/skills
        """,
    )

    parser.add_argument(
        "--agent-base",
        dest="agent_base",
        metavar="DIR",
        help="agent config directory (defaults to ~/.claude)",
    )

    args = parser.parse_args()

    install_skill(agent_base=args.agent_base)


if __name__ == "__main__":
    main()
