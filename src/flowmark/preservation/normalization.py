"""Portable UTF-8, BOM, newline, and scalar-width normalization."""

from __future__ import annotations

from flowmark.preservation.model import (
    InvalidUtf8Error,
    NormalizedSource,
)

UTF8_BOM = b"\xef\xbb\xbf"
UNICODE_BOM = "\ufeff"


def _normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _canonicalize_terminal_lf(text: str) -> str:
    return text.rstrip("\n") + "\n"


def normalize_source(source: str | bytes) -> NormalizedSource:
    """Decode and normalize source into the shared scanner coordinate space."""
    if isinstance(source, bytes):
        had_bom = source.startswith(UTF8_BOM)
        payload = source[len(UTF8_BOM) :] if had_bom else source
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise InvalidUtf8Error() from error
    else:
        had_bom = source.startswith(UNICODE_BOM)
        text = source.removeprefix(UNICODE_BOM)
        try:
            text.encode("utf-8")
        except UnicodeEncodeError as error:
            raise InvalidUtf8Error() from error

    text = _canonicalize_terminal_lf(_normalize_line_endings(text))
    utf8 = text.encode("utf-8")
    return NormalizedSource(
        text=text,
        utf8=utf8,
        had_bom=had_bom,
    )


def finalize_output(source: NormalizedSource, output: str) -> str:
    """Apply canonical LF output and restore the recorded leading BOM once."""
    try:
        output.encode("utf-8")
    except UnicodeEncodeError as error:
        raise InvalidUtf8Error() from error
    finalized = _canonicalize_terminal_lf(_normalize_line_endings(output))
    return f"{UNICODE_BOM if source.had_bom else ''}{finalized}"


def scalar_width(text: str) -> int:
    """Count Unicode scalars, not UTF-8 bytes or terminal display cells."""
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise InvalidUtf8Error() from error
    return len(text)


def scalar_widths(text: str) -> tuple[int, ...]:
    """Return the scalar width of every LF-separated physical fragment."""
    return tuple(scalar_width(fragment) for fragment in text.split("\n"))
