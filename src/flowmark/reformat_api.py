import sys
from pathlib import Path

from strif import atomic_output_file

from flowmark.linewrapping.markdown_filling import fill_markdown
from flowmark.linewrapping.text_filling import Wrap, fill_text
from flowmark.linewrapping.text_wrapping import html_md_word_splitter


def reformat_text(
    text: str,
    width: int = 88,
    plaintext: bool = False,
    semantic: bool = True,
    cleanups: bool = True,
    smartquotes: bool = False,
    ellipses: bool = False,
) -> str:
    """
    Reformat text or markdown and wrap lines. Simply a convenient wrapper
    around `fill_text()` and `fill_markdown()` with reasonable defaults.
    """
    if plaintext:
        # Plaintext mode
        result = fill_text(
            text,
            text_wrap=Wrap.WRAP,
            width=width,
            word_splitter=html_md_word_splitter,  # Still use HTML/MD aware splitter by default
        )
    else:
        # Markdown mode
        result = fill_markdown(
            text,
            width=width,
            semantic=semantic,
            cleanups=cleanups,
            smartquotes=smartquotes,
            ellipses=ellipses,
        )

    return result


def reformat_file(
    path: Path | str,
    output: Path | str | None,
    width: int = 88,
    inplace: bool = False,
    nobackup: bool = False,
    plaintext: bool = False,
    semantic: bool = False,
    cleanups: bool = True,
    smartquotes: bool = False,
    ellipses: bool = False,
    make_parents: bool = True,
) -> None:
    """
    Reformat text or markdown and wrap lines on the given files.
    Accepts "-" for stdin. Can omit output if `inplace` is True.
    Throws usual file-related exceptions if the input or output is invalid.

    Args:
        path: Path to the input file, or "-" for stdin.
        output: Path to the output file, or "-" for stdout.
        width: The width to wrap lines to.
        inplace: Whether to write the file back to the same path (atomically only on success).
        nobackup: Whether to not make a backup of the original file
        plaintext: Use plaintext instead of Markdown mode wrapping.
        semantic: Use semantic line breaks (based on sentences) heuristic.
        cleanups: Enable (safe) cleanups for common issues like accidentally boldfaced section
            headers (only applies to Markdown mode).
        smartquotes: Convert straight quotes to typographic (curly) quotes and apostrophes
            (only applies to Markdown mode).
        ellipses: Convert three dots (...) to ellipsis character (…) with normalized spacing
            (only applies to Markdown mode).
        make_parents: Whether to make parent directories if they don't exist.
    """
    read_stdin = path == "-"
    write_stdout = output == "-" or not output

    if inplace and read_stdin:
        raise ValueError("Cannot use `inplace` with stdin")

    if read_stdin:
        text = sys.stdin.read()
    else:
        text = Path(path).read_text()

    result = reformat_text(text, width, plaintext, semantic, cleanups, smartquotes, ellipses)

    if inplace:
        backup_suffix = ".orig" if not nobackup else ""
        with atomic_output_file(
            path, backup_suffix=backup_suffix, make_parents=make_parents
        ) as tmp_path:
            tmp_path.write_text(result)
    else:
        if not output or write_stdout:
            sys.stdout.write(result)
        else:
            with atomic_output_file(output, make_parents=make_parents) as tmp_path:
                tmp_path.write_text(result)


def reformat_files(
    files: list[str],
    output: str | None = None,
    width: int = 88,
    inplace: bool = False,
    nobackup: bool = False,
    plaintext: bool = False,
    semantic: bool = False,
    cleanups: bool = True,
    smartquotes: bool = False,
    ellipses: bool = False,
    make_parents: bool = True,
) -> None:
    """
    Reformat multiple files with the same options.

    Args:
        files: List of file paths to process, or ["-"] for stdin.
        output: Output file path (ignored when inplace=True, use "-" for stdout).
        width: The width to wrap lines to.
        inplace: Whether to write files back to their original paths.
        nobackup: Whether to not make backups of original files.
        plaintext: Use plaintext instead of Markdown mode wrapping.
        semantic: Use semantic line breaks (based on sentences) heuristic.
        cleanups: Enable (safe) cleanups for common issues.
        smartquotes: Convert straight quotes to typographic quotes.
        ellipses: Convert three dots to ellipsis character.
        make_parents: Whether to make parent directories if they don't exist.
    """
    if len(files) == 1 and files[0] == "-":
        # Single stdin case - use original function
        reformat_file(
            path=files[0],
            output=output,
            width=width,
            inplace=inplace,
            nobackup=nobackup,
            plaintext=plaintext,
            semantic=semantic,
            cleanups=cleanups,
            smartquotes=smartquotes,
            ellipses=ellipses,
            make_parents=make_parents,
        )
        return

    # Multiple files case
    if not inplace and output and output != "-":
        raise ValueError(
            "Cannot specify output file when processing multiple files (use --inplace instead)"
        )

    for file_path in files:
        if inplace:
            # Process each file in-place
            output = None
        else:
            # Process each file to stdout
            output = "-"
        reformat_file(
            path=file_path,
            output=output,
            width=width,
            inplace=inplace,
            nobackup=nobackup,
            plaintext=plaintext,
            semantic=semantic,
            cleanups=cleanups,
            smartquotes=smartquotes,
            ellipses=ellipses,
            make_parents=make_parents,
        )
