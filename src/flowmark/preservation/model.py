"""Typed source-preservation records and their fail-closed invariants."""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field
from enum import StrEnum


class PreservationError(ValueError):
    """Base error for deterministic preservation failures."""


class InvalidUtf8Error(PreservationError):
    """Input cannot be represented as valid UTF-8."""

    def __init__(self) -> None:
        super().__init__("input is not valid UTF-8")


class InvalidRegionError(PreservationError):
    """A protected-region record violates the portable data contract."""


class RegionKind(StrEnum):
    """Stable recognizer kinds shared with the Rust port."""

    math_gitlab_inline = "math_gitlab_inline"
    math_myst_inline = "math_myst_inline"
    code_span = "code_span"
    math_paren_inline = "math_paren_inline"
    math_environment_inline = "math_environment_inline"
    math_dollar_inline = "math_dollar_inline"
    math_double_dollar_inline = "math_double_dollar_inline"
    math_dollar_block = "math_dollar_block"
    math_bracket_block = "math_bracket_block"
    math_environment_block = "math_environment_block"


class RegionForm(StrEnum):
    """Whether a region participates in inline wrapping or block rendering."""

    inline = "inline"
    block = "block"


_INLINE_REGION_KINDS = frozenset(
    {
        RegionKind.math_gitlab_inline,
        RegionKind.math_myst_inline,
        RegionKind.code_span,
        RegionKind.math_paren_inline,
        RegionKind.math_environment_inline,
        RegionKind.math_dollar_inline,
        RegionKind.math_double_dollar_inline,
    }
)
_BLOCK_REGION_KINDS = frozenset(
    {
        RegionKind.math_dollar_block,
        RegionKind.math_bracket_block,
        RegionKind.math_environment_block,
    }
)


def _validate_kind_form(kind: RegionKind, form: RegionForm) -> None:
    if type(kind) is not RegionKind or type(form) is not RegionForm:
        raise InvalidRegionError("region kind and form must use stable enum values")
    if (form is RegionForm.inline and kind not in _INLINE_REGION_KINDS) or (
        form is RegionForm.block and kind not in _BLOCK_REGION_KINDS
    ):
        raise InvalidRegionError(f"region kind {kind!s} cannot use {form!s} treatment")


def build_scalar_byte_offsets(text: str) -> tuple[int, ...]:
    offsets = [0]
    byte_offset = 0
    try:
        for scalar in text:
            byte_offset += len(scalar.encode("utf-8"))
            offsets.append(byte_offset)
    except UnicodeEncodeError as error:
        raise InvalidUtf8Error() from error
    return tuple(offsets)


def _nonnegative_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


@dataclass(frozen=True, slots=True)
class ContainerContext:
    """Container coordinates retained for compatible block matching."""

    blockquote_depth: int = 0
    list_depth: int = 0
    content_column: int = 0

    def __post_init__(self) -> None:
        for name, value in (
            ("blockquote depth", self.blockquote_depth),
            ("list depth", self.list_depth),
            ("content column", self.content_column),
        ):
            if not _nonnegative_integer(value):
                raise InvalidRegionError(f"{name} must be a nonnegative integer")
        if self.list_depth > 0 and self.content_column == 0:
            raise InvalidRegionError("list content column must be positive")


@dataclass(frozen=True, slots=True)
class NormalizedSource:
    """Valid UTF-8 source in the scanner's normalized coordinate space."""

    text: str
    utf8: bytes
    had_bom: bool
    scalar_byte_offsets: tuple[int, ...]

    def __post_init__(self) -> None:
        if "\r" in self.text:
            raise InvalidRegionError("normalized source contains a carriage return")
        if not self.text.endswith("\n") or self.text.endswith("\n\n"):
            raise InvalidRegionError("normalized source must end with exactly one LF")
        try:
            encoded = self.text.encode("utf-8")
        except UnicodeEncodeError as error:
            raise InvalidUtf8Error() from error
        if encoded != self.utf8:
            raise InvalidRegionError("normalized UTF-8 bytes do not match text")
        if self.scalar_byte_offsets != build_scalar_byte_offsets(self.text):
            raise InvalidRegionError("scalar byte offsets do not match normalized text")

    @property
    def byte_length(self) -> int:
        """Return the normalized UTF-8 length."""
        return len(self.utf8)

    @property
    def scalar_length(self) -> int:
        """Return the normalized Unicode-scalar length."""
        return len(self.text)

    def byte_offset(self, scalar_index: int) -> int:
        """Translate a Unicode-scalar boundary to its UTF-8 byte offset."""
        if not _nonnegative_integer(scalar_index) or scalar_index >= len(self.scalar_byte_offsets):
            raise InvalidRegionError("scalar index is outside normalized source")
        return self.scalar_byte_offsets[scalar_index]

    def scalar_index(self, byte_offset: int) -> int:
        """Translate a UTF-8 byte boundary to its Unicode-scalar index."""
        if not _nonnegative_integer(byte_offset) or byte_offset > self.byte_length:
            raise InvalidRegionError("byte offset is outside normalized source")
        index = bisect_left(self.scalar_byte_offsets, byte_offset)
        if index == len(self.scalar_byte_offsets) or self.scalar_byte_offsets[index] != byte_offset:
            raise InvalidRegionError("byte offset is not a UTF-8 scalar boundary")
        return index

    def slice_text(self, start: int, end: int) -> str:
        """Return a source slice after validating both UTF-8 boundaries."""
        start_index = self.scalar_index(start)
        end_index = self.scalar_index(end)
        if start_index >= end_index:
            raise InvalidRegionError("region start must be before region end")
        return self.text[start_index:end_index]


@dataclass(frozen=True, slots=True)
class ProtectedRegion:
    """One source-exact region selected after candidate arbitration."""

    index: int
    kind: RegionKind
    form: RegionForm
    start: int
    end: int
    source: str
    logical_widths: tuple[int, ...] = ()
    container: ContainerContext = field(default_factory=ContainerContext)
    scaffold_prefix: str = ""

    def __post_init__(self) -> None:
        _validate_kind_form(self.kind, self.form)
        if not _nonnegative_integer(self.index):
            raise InvalidRegionError("region index must be a nonnegative integer")
        if not _nonnegative_integer(self.start) or not _nonnegative_integer(self.end):
            raise InvalidRegionError("region offsets must be nonnegative integers")
        if self.start >= self.end:
            raise InvalidRegionError("region start must be before region end")
        try:
            source_length = len(self.source.encode("utf-8"))
        except UnicodeEncodeError as error:
            raise InvalidUtf8Error() from error
        if source_length != self.end - self.start:
            raise InvalidRegionError("region byte length does not match its source")
        if self.form is RegionForm.inline:
            if self.scaffold_prefix:
                raise InvalidRegionError("inline regions cannot define a block scaffold prefix")
            expected_widths = tuple(len(fragment) for fragment in self.source.split("\n"))
            if self.logical_widths != expected_widths:
                raise InvalidRegionError("inline logical widths do not match its source")
        else:
            if self.logical_widths:
                raise InvalidRegionError("block regions cannot define inline logical widths")
            if "\n" in self.scaffold_prefix or "\r" in self.scaffold_prefix:
                raise InvalidRegionError("block scaffold prefix must fit on the opening line")
            if not self.source.startswith(self.scaffold_prefix):
                raise InvalidRegionError("block scaffold prefix must match the source opening line")


@dataclass(frozen=True, slots=True)
class Candidate:
    """A complete scanner proposal before overlap arbitration."""

    kind: RegionKind
    form: RegionForm
    start: int
    end: int
    container: ContainerContext = field(default_factory=ContainerContext)
    scaffold_prefix: str = ""

    def __post_init__(self) -> None:
        _validate_kind_form(self.kind, self.form)
        if not _nonnegative_integer(self.start) or not _nonnegative_integer(self.end):
            raise InvalidRegionError("candidate offsets must be nonnegative integers")
        if self.start >= self.end:
            raise InvalidRegionError("candidate start must be before candidate end")
        if self.form is RegionForm.inline and self.scaffold_prefix:
            raise InvalidRegionError("inline candidates cannot define a block scaffold prefix")
        if "\n" in self.scaffold_prefix or "\r" in self.scaffold_prefix:
            raise InvalidRegionError("candidate scaffold prefix must fit on one line")

    def to_region(self, source: NormalizedSource, *, index: int) -> ProtectedRegion:
        """Materialize this candidate from the exact normalized source slice."""
        region_source = source.slice_text(self.start, self.end)
        logical_widths = (
            tuple(len(fragment) for fragment in region_source.split("\n"))
            if self.form is RegionForm.inline
            else ()
        )
        return ProtectedRegion(
            index=index,
            kind=self.kind,
            form=self.form,
            start=self.start,
            end=self.end,
            source=region_source,
            logical_widths=logical_widths,
            container=self.container,
            scaffold_prefix=self.scaffold_prefix,
        )


def validate_regions(
    source: NormalizedSource, regions: tuple[ProtectedRegion, ...]
) -> tuple[ProtectedRegion, ...]:
    """Validate source order, byte boundaries, overlap, and exact slices."""
    previous_end = 0
    for expected_index, region in enumerate(regions):
        if region.index != expected_index:
            raise InvalidRegionError("regions require contiguous source-order indexes")
        if region.start < previous_end:
            raise InvalidRegionError("protected regions overlap or are out of source order")
        if region.end > source.byte_length:
            raise InvalidRegionError("protected region ends outside normalized source")
        if source.slice_text(region.start, region.end) != region.source:
            raise InvalidRegionError("protected region does not match its source slice")
        previous_end = region.end
    return regions
