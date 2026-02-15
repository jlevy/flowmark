"""
Claude Code skill installation for flowmark.

This module provides functionality to install the flowmark skill for Claude Code,
making it available either globally across all projects or within a specific project.
"""

from __future__ import annotations

import sys
from pathlib import Path


def get_skill_content() -> str:
    """Read SKILL.md from package data.

    Returns:
        The content of the SKILL.md file as a string.

    Raises:
        ImportError: If package resources cannot be accessed.
        FileNotFoundError: If SKILL.md cannot be found in package data.
    """
    # importlib.resources.files() is available in Python 3.9+
    # This project requires Python 3.10+, so no fallback needed
    from importlib.resources import files

    skill_file = files("flowmark").joinpath("skills/SKILL.md")
    return skill_file.read_text(encoding="utf-8")


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


def install_skill(agent_base: str | None = None) -> None:
    """Install flowmark skill for Claude Code.

    Args:
        agent_base: The agent's configuration directory where skills are stored.
            The skill will be installed to {agent_base}/skills/flowmark/SKILL.md
            - None (default): Install globally to ~/.claude/skills/flowmark
            - './.claude': Install to current project's .claude/skills/flowmark
            - Any path: Install to that agent base directory

    The skill will be installed as SKILL.md in the appropriate directory,
    making it automatically available to Claude Code.
    """
    # Determine installation directory
    if agent_base is None:
        # Default: global install to ~/.claude
        base_dir = Path.home() / ".claude"
        location_desc = "globally"
        location_path = "~/.claude/skills/flowmark"
    else:
        # User-specified agent base directory
        base_dir = Path(agent_base).resolve()
        location_desc = f"to {base_dir}"
        location_path = str(base_dir / "skills" / "flowmark")

    skill_dir = base_dir / "skills" / "flowmark"

    # Load skill content from package data
    try:
        skill_content = get_skill_content()
    except (ImportError, FileNotFoundError) as e:
        print(f"\n✗ Error: Could not load skill content: {e}", file=sys.stderr)
        print("\nThis command requires flowmark to be installed as a package.", file=sys.stderr)
        print("Install with: uv tool install flowmark", file=sys.stderr)
        sys.exit(1)

    # Create directory and install
    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"

        skill_file.write_text(skill_content, encoding="utf-8")

        print("\n" + "=" * 70)
        print(f"✓ Flowmark skill installed {location_desc}")
        print("=" * 70)
        print(f"\nLocation: {skill_file}")
        print(f"          ({location_path})")
        print("\nClaude Code will now automatically use flowmark for Markdown formatting.")
        print(f"To uninstall, remove this directory: {skill_dir}")

        # Show tip for project installs (when not using default global location)
        if agent_base is not None:
            print("\n" + "-" * 70)
            print("Tip: Commit .claude/skills/ to share this skill with your team.")
            print("-" * 70)

        print()  # Blank line for clean output

    except PermissionError as e:
        print(f"\n✗ Permission denied: {e}", file=sys.stderr)
        print(f"\nCould not write to {skill_dir}", file=sys.stderr)
        print("Check directory permissions and try again.", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"\n✗ Installation failed: {e}", file=sys.stderr)
        sys.exit(1)


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
  %(prog)s                        # Install globally (~/.claude/skills)
  %(prog)s --agent-base ./.claude # Install in current project (./.claude/skills)
  %(prog)s --agent-base /path     # Install to /path/skills
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
