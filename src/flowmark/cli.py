#!/usr/bin/env python3
"""
Flowmark: Better auto-formatting for Markdown and plaintext

Flowmark provides enhanced text wrapping capabilities with special handling for
Markdown content. It can:

- Format Markdown with proper line wrapping while preserving structure
  and normalizing Markdown formatting

- Optionally break lines at sentence boundaries for better diff readability

- Process plaintext with HTML-aware word splitting

It is both a library and a command-line tool.

Command-line usage examples:

  # Format all Markdown files in current directory recursively
  flowmark --auto .

  # Format all Markdown files in a specific directory
  flowmark --auto docs/

  # Format a Markdown file to stdout
  flowmark README.md

  # Format multiple Markdown files in-place
  flowmark --inplace README.md CHANGELOG.md docs/*.md

  # Format a Markdown file in-place without backups and all auto-formatting
  # options enabled
  flowmark --auto README.md

  # List files that would be formatted (without formatting)
  flowmark --list-files .

  # Format with additional file patterns
  flowmark --auto --extend-include "*.mdx" .

  # Format but skip a specific directory
  flowmark --auto --extend-exclude "drafts/" .

  # Format a Markdown file and save to a new file
  flowmark README.md -o README_formatted.md

  # Edit a file in-place (with or without making a backup)
  flowmark --inplace README.md
  flowmark --inplace --nobackup README.md

  # Process plaintext instead of Markdown
  flowmark --plaintext text.txt

  # Use semantic line breaks (based on sentences, which is helpful to reduce
  # irrelevant line wrap diffs in git history)
  flowmark --semantic README.md

For more details, see: https://github.com/jlevy/flowmark
"""

from __future__ import annotations

import argparse
import importlib.metadata
import sys
from dataclasses import dataclass

from flowmark.formats.flowmark_markdown import ListSpacing
from flowmark.reformat_api import reformat_files


@dataclass
class Options:
    """Command-line options for the flowmark tool."""

    files: list[str]
    output: str
    width: int
    plaintext: bool
    semantic: bool
    cleanups: bool
    smartquotes: bool
    ellipses: bool
    inplace: bool
    nobackup: bool
    version: bool
    list_spacing: ListSpacing
    # File discovery options
    extend_include: list[str]
    exclude: list[str] | None
    extend_exclude: list[str]
    respect_gitignore: bool
    force_exclude: bool
    list_files: bool
    files_max_size: int
    # Agent skill options
    skill_instructions: bool
    install_skill: bool
    agent_base: str | None
    docs: bool


def _parse_args(args: list[str] | None = None) -> tuple[Options, set[str], bool]:
    """
    Parse command-line arguments.

    Returns a tuple of (options, explicit_flags, is_auto) where `explicit_flags`
    tracks which flags the user explicitly passed (for config merge precedence)
    and `is_auto` indicates whether --auto was used.
    """
    # Use the module's docstring as the description
    module_doc = __doc__ or ""
    doc_parts = module_doc.split("\n\n")
    description = doc_parts[0]
    epilog = "\n\n".join(doc_parts[1:])

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=str,
        default=["-"],
        help="Input files or directories (use '-' for stdin, '.' for current directory)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="-",
        help="Output file (use '-' for stdout)",
    )
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=88,
        help="Line width to wrap to, or 0 to disable line wrapping (default: %(default)s)",
    )
    parser.add_argument(
        "-p", "--plaintext", action="store_true", help="Process as plaintext (no Markdown parsing)"
    )
    parser.add_argument(
        "-s",
        "--semantic",
        action="store_true",
        default=False,
        help="Enable semantic (sentence-based) line breaks (only applies to Markdown mode)",
    )
    parser.add_argument(
        "-c",
        "--cleanups",
        action="store_true",
        default=False,
        help="Enable (safe) cleanups for common issues like accidentally boldfaced section "
        "headers (only applies to Markdown mode)",
    )
    parser.add_argument(
        "--smartquotes",
        action="store_true",
        default=False,
        help="Convert straight quotes to typographic (curly) quotes and apostrophes "
        "(only applies to Markdown mode)",
    )
    parser.add_argument(
        "--ellipses",
        action="store_true",
        default=False,
        help="Convert three dots (...) to ellipsis character (…) with normalized spacing "
        "(only applies to Markdown mode)",
    )
    parser.add_argument(
        "--list-spacing",
        type=str,
        choices=["preserve", "loose", "tight"],
        default="preserve",
        help="Control list spacing: 'preserve' keeps original tight/loose formatting, "
        "'loose' adds blank lines between all items, 'tight' removes blank lines where possible "
        "(default: %(default)s)",
    )
    parser.add_argument(
        "-i", "--inplace", action="store_true", help="Edit the file in place (ignores --output)"
    )
    parser.add_argument(
        "--nobackup",
        action="store_true",
        help="Do not make a backup of the original file when using --inplace",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Same as `--inplace --nobackup --semantic --cleanups --smartquotes --ellipses`, as a convenience for "
        "fully auto-formatting files. With no file arguments, defaults to '.' (current directory)",
    )
    # File discovery options
    parser.add_argument(
        "--extend-include",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Additional file patterns to include (e.g., '*.mdx'). Can be repeated",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        metavar="PATTERN",
        help="Replace all default exclusion patterns. Can be repeated",
    )
    parser.add_argument(
        "--extend-exclude",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Add to default exclusion patterns (e.g., 'drafts/'). Can be repeated",
    )
    parser.add_argument(
        "--no-respect-gitignore",
        action="store_true",
        dest="no_respect_gitignore",
        help="Disable .gitignore integration",
    )
    parser.add_argument(
        "--force-exclude",
        action="store_true",
        dest="force_exclude",
        help="Apply exclusion patterns even to files named explicitly on the command line",
    )
    parser.add_argument(
        "--list-files",
        action="store_true",
        dest="list_files",
        help="Print resolved file paths without formatting (useful for debugging)",
    )
    parser.add_argument(
        "--files-max-size",
        type=int,
        default=1_048_576,
        dest="files_max_size",
        metavar="BYTES",
        help="Skip files larger than this size in bytes (0 = no limit, default: %(default)s)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit",
    )
    # Agent skill options
    parser.add_argument(
        "--skill",
        action="store_true",
        dest="skill_instructions",
        help="Print skill instructions (SKILL.md content) for Claude Code",
    )
    parser.add_argument(
        "--install-skill",
        action="store_true",
        dest="install_skill",
        help="Install Claude Code skill for flowmark",
    )
    parser.add_argument(
        "--agent-base",
        type=str,
        dest="agent_base",
        metavar="DIR",
        help="Agent config directory for skill installation (default: ~/.claude)",
    )
    parser.add_argument(
        "--docs",
        action="store_true",
        help="Print full documentation",
    )
    opts = parser.parse_args(args)

    # Track which flags the user explicitly set (for config merge precedence).
    # argparse doesn't track this natively, so we compare against defaults.
    _flag_defaults: dict[str, object] = {
        "width": 88,
        "semantic": False,
        "cleanups": False,
        "smartquotes": False,
        "ellipses": False,
        "list_spacing": "preserve",
        "extend_include": [],
        "exclude": None,
        "extend_exclude": [],
        "no_respect_gitignore": False,
        "force_exclude": False,
        "files_max_size": 1_048_576,
    }
    explicit_flags: set[str] = set()
    for flag_name, default_val in _flag_defaults.items():
        actual = getattr(opts, flag_name, None)
        if actual != default_val:
            # Map argparse dest names to Options field names
            field_name = flag_name
            if flag_name == "no_respect_gitignore":
                field_name = "respect_gitignore"
            explicit_flags.add(field_name)

    is_auto = opts.auto

    if opts.auto:
        opts.inplace = True
        opts.nobackup = True
        opts.semantic = True
        opts.cleanups = True
        opts.smartquotes = True
        opts.ellipses = True
        # When --auto is used with no file args, default to current directory
        if opts.files == ["-"]:
            opts.files = ["."]

    return (Options(
        files=opts.files,
        output=opts.output,
        width=opts.width,
        plaintext=opts.plaintext,
        semantic=opts.semantic,
        cleanups=opts.cleanups,
        smartquotes=opts.smartquotes,
        ellipses=opts.ellipses,
        inplace=opts.inplace,
        nobackup=opts.nobackup,
        version=opts.version,
        list_spacing=ListSpacing(opts.list_spacing),
        extend_include=opts.extend_include,
        exclude=opts.exclude,
        extend_exclude=opts.extend_exclude,
        respect_gitignore=not opts.no_respect_gitignore,
        force_exclude=opts.force_exclude,
        list_files=opts.list_files,
        files_max_size=opts.files_max_size,
        skill_instructions=opts.skill_instructions,
        install_skill=opts.install_skill,
        agent_base=opts.agent_base,
        docs=opts.docs,
    ), explicit_flags, is_auto)


def _needs_file_resolution(files: list[str]) -> bool:
    """Check if any input paths need file resolution (directories or globs)."""
    from pathlib import Path

    for f in files:
        if f == "-":
            continue
        if Path(f).is_dir():
            return True
        if any(c in f for c in "*?["):
            return True
    return False


def _resolve_files(options: Options) -> list[str]:
    """
    If inputs include directories or globs, use FileResolver to expand them.
    Otherwise, pass through unchanged for backward compatibility.
    """
    if not _needs_file_resolution(options.files) and not options.list_files:
        return options.files

    from flowmark.file_resolver import FileResolver, FileResolverConfig

    config = FileResolverConfig(
        extend_include=options.extend_include,
        exclude=options.exclude,
        extend_exclude=options.extend_exclude,
        respect_gitignore=options.respect_gitignore,
        force_exclude=options.force_exclude,
        files_max_size=options.files_max_size,
    )
    resolver = FileResolver(config)
    resolved = resolver.resolve(options.files)
    return [str(p) for p in resolved]


def main(args: list[str] | None = None) -> int:
    """
    Main entry point for the flowmark CLI.

    Args:
        args: Command-line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    options, explicit_flags, is_auto = _parse_args(args)

    # Display version information if requested
    if options.version:
        try:
            version = importlib.metadata.version("flowmark")
            print(f"v{version}")
        except importlib.metadata.PackageNotFoundError:
            print("unknown (package not installed)")
        return 0

    # Handle skill-related options (early exit)
    if options.install_skill:
        from flowmark.skill import install_skill

        install_skill(agent_base=options.agent_base)
        return 0

    if options.skill_instructions:
        from flowmark.skill import get_skill_content

        print(get_skill_content())
        return 0

    if options.docs:
        from flowmark.skill import get_docs_content

        print(get_docs_content())
        return 0

    # Load and merge config file settings
    from pathlib import Path

    from flowmark.config import find_config_file, load_config, merge_cli_with_config

    config_path = find_config_file(Path.cwd())
    if config_path:
        config = load_config(config_path)
        merge_cli_with_config(options, config, is_auto, explicit_flags)

    # Resolve files if any input is a directory, glob, or --list-files is used
    resolved_files = _resolve_files(options)

    # Handle --list-files mode (print and exit)
    if options.list_files:
        for f in resolved_files:
            print(f)
        return 0

    try:
        reformat_files(
            files=resolved_files,
            output=options.output,
            width=options.width,
            inplace=options.inplace,
            nobackup=options.nobackup,
            plaintext=options.plaintext,
            semantic=options.semantic,
            cleanups=options.cleanups,
            smartquotes=options.smartquotes,
            ellipses=options.ellipses,
            make_parents=True,
            list_spacing=options.list_spacing,
        )
    except ValueError as e:
        # Handle errors reported by reformat_file, like using --inplace with stdin.
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        # Catch other potential file or processing errors.
        print(f"Error: {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
