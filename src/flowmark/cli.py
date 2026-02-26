#!/usr/bin/env python3
"""
Flowmark: Better auto-formatting for Markdown and plaintext

Common usage:
  flowmark --auto README.md
  flowmark --auto docs/
  flowmark --auto .
  flowmark --list-files .

Agent usage:
  flowmark --skill
  Agents should run `flowmark --skill` for full Flowmark usage guidance.

Use `flowmark --docs` for full documentation.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import sys
from dataclasses import dataclass
from pathlib import Path

from flowmark.config import find_config_file, load_config, merge_cli_with_config
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
        default=[],
        help="Input files or directories (required; use '-' for stdin, '.' for current directory)",
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
        "fully auto-formatting files. Requires at least one file or directory argument (use '.' for current directory)",
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
        help="Print resolved file paths without formatting. "
        "Requires at least one file or directory argument (use '.' for current directory)",
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
    # We use argparse sentinel defaults to detect actual CLI presence rather than
    # comparing against default values (which fails when user passes the default).
    _SENTINEL = object()
    _tracked_flags: dict[str, str] = {
        # argparse dest name -> Options field name
        "width": "width",
        "semantic": "semantic",
        "cleanups": "cleanups",
        "smartquotes": "smartquotes",
        "ellipses": "ellipses",
        "list_spacing": "list_spacing",
        "extend_include": "extend_include",
        "exclude": "exclude",
        "extend_exclude": "extend_exclude",
        "no_respect_gitignore": "respect_gitignore",
        "force_exclude": "force_exclude",
        "files_max_size": "files_max_size",
    }
    # Re-parse with sentinel defaults to detect which flags were actually supplied.
    # append actions use None as sentinel (argparse creates a list when the flag is used).
    sentinel_parser = argparse.ArgumentParser(add_help=False)
    sentinel_parser.add_argument("-w", "--width", type=int, default=_SENTINEL)
    sentinel_parser.add_argument("-s", "--semantic", action="store_true", default=_SENTINEL)
    sentinel_parser.add_argument("-c", "--cleanups", action="store_true", default=_SENTINEL)
    sentinel_parser.add_argument("--smartquotes", action="store_true", default=_SENTINEL)
    sentinel_parser.add_argument("--ellipses", action="store_true", default=_SENTINEL)
    sentinel_parser.add_argument("--list-spacing", dest="list_spacing", default=_SENTINEL)
    sentinel_parser.add_argument("--extend-include", action="append", default=None)
    sentinel_parser.add_argument("--exclude", action="append", default=None)
    sentinel_parser.add_argument("--extend-exclude", action="append", default=None)
    sentinel_parser.add_argument(
        "--no-respect-gitignore",
        dest="no_respect_gitignore",
        action="store_true",
        default=_SENTINEL,
    )
    sentinel_parser.add_argument(
        "--force-exclude", dest="force_exclude", action="store_true", default=_SENTINEL
    )
    sentinel_parser.add_argument(
        "--files-max-size", type=int, dest="files_max_size", default=_SENTINEL
    )
    sentinel_opts, _ = sentinel_parser.parse_known_args(args if args is not None else sys.argv[1:])

    explicit_flags: set[str] = set()
    for dest_name, field_name in _tracked_flags.items():
        val = getattr(sentinel_opts, dest_name, _SENTINEL)
        # For append actions, None means not supplied; a list means supplied
        if dest_name in ("extend_include", "exclude", "extend_exclude"):
            if val is not None:
                explicit_flags.add(field_name)
        elif val is not _SENTINEL:
            explicit_flags.add(field_name)

    is_auto = opts.auto

    if opts.auto:
        opts.inplace = True
        opts.nobackup = True
        opts.semantic = True
        opts.cleanups = True
        opts.smartquotes = True
        opts.ellipses = True

    return (
        Options(
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
        ),
        explicit_flags,
        is_auto,
    )


def _needs_file_resolution(files: list[str]) -> bool:
    """Check if any input paths need file resolution (directories or globs)."""
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

    # Filter out stdin marker before passing to resolver
    resolvable = [f for f in options.files if f != "-"]
    stdin_present = len(resolvable) < len(options.files)

    config = FileResolverConfig(
        extend_include=options.extend_include,
        exclude=options.exclude,
        extend_exclude=options.extend_exclude,
        respect_gitignore=options.respect_gitignore,
        force_exclude=options.force_exclude,
        files_max_size=options.files_max_size,
    )
    resolver = FileResolver(config)
    resolved = resolver.resolve(resolvable)
    result = [str(p) for p in resolved]
    if stdin_present:
        result.insert(0, "-")
    return result


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

    # Require explicit file/directory arguments.
    # (Use '.' for the current directory, '-' for stdin.)
    if not options.files:
        if is_auto:
            print(
                "Error: --auto requires at least one file or directory argument"
                " (use '.' for current directory, --help for more options)",
                file=sys.stderr,
            )
            return 1
        if options.list_files:
            print(
                "Error: --list-files requires at least one file or directory argument"
                " (use '.' for current directory, --help for more options)",
                file=sys.stderr,
            )
            return 1
        print(
            "Error: No input specified. Provide files, directories (use '.' for current"
            " directory), or '-' for stdin. Use --help for more options.",
            file=sys.stderr,
        )
        return 1

    # Load and merge config file settings
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
