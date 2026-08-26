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

SENTINEL_REPEAT = "\U000f0000"
SENTINEL_END = "\U000f0001"
INDEX_START = "\U000f0002"
INDEX_END = "\U000f0003"
_BASE36_DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"


class InvalidTokenError(PreservationError):
    """A parser token stream cannot be restored without ambiguity."""


@dataclass(frozen=True, slots=True)
class ProtectedSource:
    """Parser-facing source plus its source-exact restoration side table."""

    text: str
    sentinel: str
    regions: tuple[ProtectedRegion, ...]
    tokens: tuple[str, ...]


def choose_sentinel(source: str) -> str:
    """Choose the shortest deterministic sentinel absent from finite source text."""
    run_length = 0
    maximum_before_end = 0
    for scalar in source:
        if scalar == SENTINEL_REPEAT:
            run_length += 1
        elif scalar == SENTINEL_END:
            maximum_before_end = max(maximum_before_end, run_length)
            run_length = 0
        else:
            run_length = 0
    return SENTINEL_REPEAT * (maximum_before_end + 1) + SENTINEL_END


def _validate_sentinel(sentinel: str) -> None:
    if (
        len(sentinel) < 2
        or sentinel[-1] != SENTINEL_END
        or any(scalar != SENTINEL_REPEAT for scalar in sentinel[:-1])
    ):
        raise InvalidTokenError("invalid preservation sentinel")


def _encode_base36(index: int) -> str:
    if isinstance(index, bool) or index < 0:
        raise InvalidTokenError("token index must be a nonnegative integer")
    if index == 0:
        return "0"
    digits: list[str] = []
    while index:
        index, remainder = divmod(index, 36)
        digits.append(_BASE36_DIGITS[remainder])
    return "".join(reversed(digits))


def encode_token(sentinel: str, index: int) -> str:
    """Encode one canonical lowercase-base-36 protected-region token."""
    _validate_sentinel(sentinel)
    return f"{sentinel}{INDEX_START}{_encode_base36(index)}{INDEX_END}{sentinel}"


def parse_token(token: str, sentinel: str) -> int:
    """Parse one complete canonical token or fail without a partial result."""
    _validate_sentinel(sentinel)
    prefix = sentinel + INDEX_START
    suffix = INDEX_END + sentinel
    if not token.startswith(prefix) or not token.endswith(suffix):
        raise InvalidTokenError("malformed preservation token")
    digits = token[len(prefix) : len(token) - len(suffix)]
    if (
        not digits
        or any(scalar not in _BASE36_DIGITS for scalar in digits)
        or (len(digits) > 1 and digits[0] == "0")
    ):
        raise InvalidTokenError("malformed preservation token index")
    index = int(digits, 36)
    if _encode_base36(index) != digits:
        raise InvalidTokenError("non-canonical preservation token index")
    return index


def protect_source(
    source: NormalizedSource,
    regions: tuple[ProtectedRegion, ...],
) -> ProtectedSource:
    """Replace exact protected slices with parser-inert tokens and retain a side table."""
    validate_regions(source, regions)
    sentinel = choose_sentinel(source.text)
    tokens = tuple(encode_token(sentinel, region.index) for region in regions)
    parts: list[str] = []
    previous_end = 0
    for region, token in zip(regions, tokens, strict=True):
        start_index = source.scalar_index(region.start)
        previous_index = source.scalar_index(previous_end)
        parts.append(source.text[previous_index:start_index])
        if region.form is RegionForm.block:
            if not region.source.endswith("\n"):
                raise InvalidTokenError("protected block source must end with LF")
            parts.extend((region.scaffold_prefix, token, "\n"))
        else:
            parts.append(token)
        previous_end = region.end
    parts.append(source.text[source.scalar_index(previous_end) :])
    return ProtectedSource("".join(parts), sentinel, regions, tokens)


def restore_source(rendered: str, protected: ProtectedSource) -> str:
    """Validate the complete parser token stream, then restore exact source slices."""
    _validate_sentinel(protected.sentinel)
    if len(protected.regions) != len(protected.tokens):
        raise InvalidTokenError("protected side table lengths do not match")
    for expected_index, (region, token) in enumerate(
        zip(protected.regions, protected.tokens, strict=True)
    ):
        if region.index != expected_index or token != encode_token(
            protected.sentinel, expected_index
        ):
            raise InvalidTokenError("protected side table is not canonical")

    segments = rendered.split(protected.sentinel)
    if len(segments) != 2 * len(protected.regions) + 1:
        raise InvalidTokenError("preservation token stream is missing, duplicated, or malformed")

    gaps = [segments[index] for index in range(0, len(segments), 2)]
    for expected_index, region in enumerate(protected.regions):
        token_middle = segments[2 * expected_index + 1]
        token = protected.sentinel + token_middle + protected.sentinel
        if parse_token(token, protected.sentinel) != expected_index:
            raise InvalidTokenError("preservation tokens are reordered or duplicated")
        if region.form is RegionForm.block:
            if gaps[expected_index] and not gaps[expected_index].endswith("\n"):
                raise InvalidTokenError("protected block token is not at a line boundary")
            if not gaps[expected_index + 1].startswith("\n"):
                raise InvalidTokenError("protected block token lost its structural LF")
            gaps[expected_index + 1] = gaps[expected_index + 1][1:]

    output: list[str] = [gaps[0]]
    for index, region in enumerate(protected.regions):
        output.extend((region.source, gaps[index + 1]))
    restored = "".join(output)
    if protected.sentinel in restored:
        raise InvalidTokenError("preservation sentinel remains after restoration")
    return restored
