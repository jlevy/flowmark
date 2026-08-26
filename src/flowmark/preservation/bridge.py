"""Collision-safe parser substitution and fail-closed source restoration."""

from __future__ import annotations

from dataclasses import dataclass

from flowmark.preservation.model import (
    NormalizedSource,
    PreservationError,
    ProtectedRegion,
    RegionForm,
    validate_regions,
)

ESCAPE_MARKER = "\U000f0000"
TOKEN_START = "\U000f0001"
TOKEN_END = "\U000f0002"
ESCAPED_ESCAPE = "\U000f0003"
ESCAPED_START = "\U000f0004"
ESCAPED_END = "\U000f0005"
INDEX_SCALAR_START = "\U000f0100"
INDEX_SCALAR_END = "\U000f01ff"
INDEX_WIDTH = 8
TOKEN_LENGTH = INDEX_WIDTH + 2
_MAX_INDEX = 1 << (8 * INDEX_WIDTH)
_ESCAPE_CODES = {
    ESCAPE_MARKER: ESCAPED_ESCAPE,
    TOKEN_START: ESCAPED_START,
    TOKEN_END: ESCAPED_END,
}
_UNESCAPE_CODES = {code: marker for marker, code in _ESCAPE_CODES.items()}


class InvalidTokenError(PreservationError):
    """A parser token stream cannot be restored without ambiguity."""


@dataclass(frozen=True, slots=True)
class ProtectedSource:
    """Parser-facing source plus its source-exact restoration side table."""

    text: str
    regions: tuple[ProtectedRegion, ...]
    tokens: tuple[str, ...]


def _escape_authored_markers(text: str) -> str:
    """Escape token-control scalars without making parser-facing text superlinear."""
    parts: list[str] = []
    previous = 0
    for index, scalar in enumerate(text):
        escape_code = _ESCAPE_CODES.get(scalar)
        if escape_code is None:
            continue
        parts.extend((text[previous:index], ESCAPE_MARKER, escape_code))
        previous = index + 1
    if not parts:
        return text
    parts.append(text[previous:])
    return "".join(parts)


def encode_token(index: int) -> str:
    """Encode one protected-region index as a fixed-width private-use token."""
    if isinstance(index, bool) or index < 0 or index >= _MAX_INDEX:
        raise InvalidTokenError("token index must be an unsigned 64-bit integer")
    digits = "".join(chr(ord(INDEX_SCALAR_START) + byte) for byte in index.to_bytes(8, "big"))
    return TOKEN_START + digits + TOKEN_END


def parse_token(token: str) -> int:
    """Parse one complete fixed-width token or fail without a partial result."""
    if (
        len(token) != TOKEN_LENGTH
        or not token.startswith(TOKEN_START)
        or not token.endswith(TOKEN_END)
    ):
        raise InvalidTokenError("malformed preservation token")
    digit_values = [ord(scalar) - ord(INDEX_SCALAR_START) for scalar in token[1:-1]]
    if any(value < 0 or value > 255 for value in digit_values):
        raise InvalidTokenError("malformed preservation token index")
    return int.from_bytes(bytes(digit_values), "big")


def _parse_rendered_stream(rendered: str) -> tuple[list[str], list[int]]:
    """Decode authored markers and collect complete tokens in one validation pass."""
    gaps: list[str] = []
    indexes: list[int] = []
    gap: list[str] = []
    position = 0
    while position < len(rendered):
        scalar = rendered[position]
        if scalar == ESCAPE_MARKER:
            if position + 1 >= len(rendered):
                raise InvalidTokenError("malformed preservation marker escape")
            decoded = _UNESCAPE_CODES.get(rendered[position + 1])
            if decoded is None:
                raise InvalidTokenError("malformed preservation marker escape")
            gap.append(decoded)
            position += 2
            continue
        if scalar == TOKEN_START:
            token_end = position + TOKEN_LENGTH
            token = rendered[position:token_end]
            indexes.append(parse_token(token))
            gaps.append("".join(gap))
            gap.clear()
            position = token_end
            continue
        if scalar == TOKEN_END:
            raise InvalidTokenError("malformed preservation token")
        gap.append(scalar)
        position += 1
    gaps.append("".join(gap))
    return gaps, indexes


def protect_source(
    source: NormalizedSource,
    regions: tuple[ProtectedRegion, ...],
) -> ProtectedSource:
    """Replace exact protected slices with parser-inert tokens and retain a side table."""
    validate_regions(source, regions)
    tokens = tuple(encode_token(region.index) for region in regions)
    parts: list[str] = []
    previous_end = 0
    for region, token in zip(regions, tokens, strict=True):
        start_index = source.scalar_index(region.start)
        previous_index = source.scalar_index(previous_end)
        parts.append(_escape_authored_markers(source.text[previous_index:start_index]))
        if region.form is RegionForm.block:
            if not region.source.endswith("\n"):
                raise InvalidTokenError("protected block source must end with LF")
            parts.extend((region.scaffold_prefix, token, "\n"))
        else:
            parts.append(token)
        previous_end = region.end
    parts.append(_escape_authored_markers(source.text[source.scalar_index(previous_end) :]))
    return ProtectedSource("".join(parts), regions, tokens)


def restore_source(rendered: str, protected: ProtectedSource) -> str:
    """Validate the complete parser token stream, then restore exact source slices."""
    if len(protected.regions) != len(protected.tokens):
        raise InvalidTokenError("protected side table lengths do not match")
    for expected_index, (region, token) in enumerate(
        zip(protected.regions, protected.tokens, strict=True)
    ):
        if region.index != expected_index or token != encode_token(expected_index):
            raise InvalidTokenError("protected side table is not canonical")

    gaps, indexes = _parse_rendered_stream(rendered)
    if len(indexes) != len(protected.regions):
        raise InvalidTokenError("preservation token stream is missing, duplicated, or malformed")
    if indexes != list(range(len(protected.regions))):
        raise InvalidTokenError("preservation tokens are reordered or duplicated")
    for expected_index, region in enumerate(protected.regions):
        if region.form is RegionForm.block:
            if gaps[expected_index] and not gaps[expected_index].endswith("\n"):
                raise InvalidTokenError("protected block token is not at a line boundary")
            if not gaps[expected_index + 1].startswith("\n"):
                raise InvalidTokenError("protected block token lost its structural LF")
            gaps[expected_index + 1] = gaps[expected_index + 1][1:]

    output: list[str] = [gaps[0]]
    for index, region in enumerate(protected.regions):
        output.extend((region.source, gaps[index + 1]))
    return "".join(output)
