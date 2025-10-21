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

  # Format a Markdown file to stdout
  flowmark README.md

  # Format multiple Markdown files in-place
  flowmark --inplace README.md CHANGELOG.md docs/*.md

  # Format a Markdown file in-place without backups and all auto-formatting
  # options enabled
  flowmark --auto README.md

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


def _parse_args(args: list[str] | None = None) -> Options:
    """Parse command-line arguments for the flowmark tool."""
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
        help="Input files (use '-' for stdin, multiple files supported)",
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
        "fully auto-formatting files",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit",
    )
    opts = parser.parse_args(args)

    if opts.auto:
        opts.inplace = True
        opts.nobackup = True
        opts.semantic = True
        opts.cleanups = True
        opts.smartquotes = True
        opts.ellipses = True

    return Options(
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
    )


def main(args: list[str] | None = None) -> int:
    """
    Main entry point for the flowmark CLI.

    Args:
        args: Command-line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    options = _parse_args(args)

    # Display version information if requested
    if options.version:
        try:
            version = importlib.metadata.version("flowmark")
            print(f"v{version}")
        except importlib.metadata.PackageNotFoundError:
            print("unknown (package not installed)")
        return 0

    try:
        reformat_files(
            files=options.files,
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
