import sys
from pathlib import Path

from strif import atomic_output_file

from flowmark.formats.flowmark_markdown import ListSpacing
from flowmark.linewrapping.markdown_filling import fill_markdown
from flowmark.linewrapping.text_filling import Wrap, fill_text
from flowmark.linewrapping.text_wrapping import get_html_md_word_splitter
from flowmark.preservation.model import InvalidUtf8Error


def _decode_utf8(data: bytes, path: str | None = None) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InvalidUtf8Error(path) from error


def _read_stdin_bytes() -> bytes:
    stream = getattr(sys.stdin, "buffer", None)
    return stream.read() if stream is not None else sys.stdin.read().encode("utf-8")


def _write_stdout_bytes(data: bytes) -> None:
    stream = getattr(sys.stdout, "buffer", None)
    if stream is not None:
        stream.write(data)
    else:
        sys.stdout.write(data.decode("utf-8"))


def reformat_text(
    text: str,
    width: int = 88,
    plaintext: bool = False,
    semantic: bool = True,
    cleanups: bool = True,
    smartquotes: bool = False,
    ellipses: bool = False,
    list_spacing: ListSpacing = ListSpacing.preserve,
) -> str:
    """
    Reformat text or markdown and wrap lines. Simply a convenient wrapper
    around `fill_text()` and `fill_markdown()` with reasonable defaults. Markdown input
    is never implicitly dedented; call `fill_markdown(dedent_input=True)` explicitly for
    docstring-style source.
    """
    if plaintext:
        # Plaintext mode
        result = fill_text(
            text,
            text_wrap=Wrap.WRAP,
            width=width,
            word_splitter=get_html_md_word_splitter(),
        )
    else:
        # Markdown mode
        result = fill_markdown(
            text,
            dedent_input=False,
            width=width,
            semantic=semantic,
            cleanups=cleanups,
            smartquotes=smartquotes,
            ellipses=ellipses,
            list_spacing=list_spacing,
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
    list_spacing: ListSpacing = ListSpacing.preserve,
    check: bool = False,
) -> bool:
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
        list_spacing: Control list spacing: "preserve" (default), "loose", or "tight".
        check: Check-only mode. Do not write any output; just report whether the content
            would change.

    Returns:
        True if the formatted output differs from the input (i.e. the file would change),
        False otherwise.
    """
    read_stdin = path == "-"
    write_stdout = output == "-" or not output

    if inplace and read_stdin and not check:
        raise ValueError("Cannot use `inplace` with stdin")

    if read_stdin:
        input_bytes = _read_stdin_bytes()
    else:
        input_bytes = Path(path).read_bytes()
    text = _decode_utf8(input_bytes, None if read_stdin else str(path))

    result = reformat_text(
        text, width, plaintext, semantic, cleanups, smartquotes, ellipses, list_spacing
    )

    result_bytes = result.encode("utf-8")
    would_change = result_bytes != input_bytes

    # In check mode, never write — only report whether the content would change.
    if check:
        return would_change

    if inplace:
        backup_suffix = ".orig" if not nobackup else ""
        with atomic_output_file(
            path, backup_suffix=backup_suffix, make_parents=make_parents
        ) as tmp_path:
            tmp_path.write_bytes(result_bytes)
    else:
        if not output or write_stdout:
            _write_stdout_bytes(result_bytes)
        else:
            with atomic_output_file(output, make_parents=make_parents) as tmp_path:
                tmp_path.write_bytes(result_bytes)

    return would_change


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
    list_spacing: ListSpacing = ListSpacing.preserve,
    check: bool = False,
) -> list[str]:
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
        list_spacing: Control list spacing: "preserve" (default), "loose", or "tight".
        check: Check-only mode. Do not write any output; just report which files
            would change.

    Returns:
        The list of input paths whose content would change (always empty unless any
        file differs from its formatted output). In check mode nothing is written.
    """
    changed: list[str] = []

    if len(files) == 1 and files[0] == "-":
        # Single stdin case - use original function
        if reformat_file(
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
            list_spacing=list_spacing,
            check=check,
        ):
            changed.append(files[0])
        return changed

    # Check mode never writes, so the multi-file output guard (which only concerns
    # writing) does not apply. A single direct file may use an explicit output path.
    if len(files) > 1 and not inplace and not check and output and output != "-":
        raise ValueError(
            "Cannot specify output file when processing multiple files (use --inplace instead)"
        )

    for file_path in files:
        if inplace:
            # Process each file in-place
            file_output = None
        elif len(files) == 1:
            # A single direct file may use either an explicit path or stdout.
            file_output = output
        else:
            # Process each file to stdout
            file_output = "-"
        if reformat_file(
            path=file_path,
            output=file_output,
            width=width,
            inplace=inplace,
            nobackup=nobackup,
            plaintext=plaintext,
            semantic=semantic,
            cleanups=cleanups,
            smartquotes=smartquotes,
            ellipses=ellipses,
            make_parents=make_parents,
            list_spacing=list_spacing,
            check=check,
        ):
            changed.append(file_path)

    return changed
