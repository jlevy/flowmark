"""Ordered built-in recognizer metadata shared by scanner stages."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from flowmark.preservation.model import InvalidRegionError, RegionForm, RegionKind

# Lower bands win arbitration. Gaps permit additive recognizers without renumbering the
# stable precedence families used by both ports.
COMPOSITE_INLINE_PRIORITY = 10
CODE_SPAN_PRIORITY = 20
UNAMBIGUOUS_INLINE_PRIORITY = 30
DOLLAR_INLINE_PRIORITY = 40
BLOCK_MATH_PRIORITY = 50


@dataclass(frozen=True, slots=True)
class RecognizerDescriptor:
    """Stable kind, treatment form, arbitration priority, and porting ID."""

    kind: RegionKind
    form: RegionForm
    priority: int
    change_id: str

    def __post_init__(self) -> None:
        if type(self.priority) is not int:
            raise InvalidRegionError("recognizer priority must be an integer")
        if self.priority < 0:
            raise InvalidRegionError("recognizer priority must be nonnegative")
        if not self.change_id.startswith("FM-"):
            raise InvalidRegionError("recognizer change ID must be stable")


BUILTIN_RECOGNIZERS: Final[tuple[RecognizerDescriptor, ...]] = (
    RecognizerDescriptor(
        RegionKind.math_gitlab_inline,
        RegionForm.inline,
        COMPOSITE_INLINE_PRIORITY,
        "FM-MATH-INLINE-001",
    ),
    RecognizerDescriptor(
        RegionKind.math_myst_inline,
        RegionForm.inline,
        COMPOSITE_INLINE_PRIORITY,
        "FM-MATH-INLINE-001",
    ),
    RecognizerDescriptor(
        RegionKind.code_span,
        RegionForm.inline,
        CODE_SPAN_PRIORITY,
        "FM-CODE-SPAN-001",
    ),
    RecognizerDescriptor(
        RegionKind.math_paren_inline,
        RegionForm.inline,
        UNAMBIGUOUS_INLINE_PRIORITY,
        "FM-MATH-INLINE-001",
    ),
    RecognizerDescriptor(
        RegionKind.math_environment_inline,
        RegionForm.inline,
        UNAMBIGUOUS_INLINE_PRIORITY,
        "FM-MATH-INLINE-001",
    ),
    RecognizerDescriptor(
        RegionKind.math_dollar_inline,
        RegionForm.inline,
        DOLLAR_INLINE_PRIORITY,
        "FM-MATH-INLINE-001",
    ),
    RecognizerDescriptor(
        RegionKind.math_double_dollar_inline,
        RegionForm.inline,
        DOLLAR_INLINE_PRIORITY,
        "FM-MATH-INLINE-001",
    ),
    RecognizerDescriptor(
        RegionKind.math_dollar_block,
        RegionForm.block,
        BLOCK_MATH_PRIORITY,
        "FM-MATH-BLOCK-001",
    ),
    RecognizerDescriptor(
        RegionKind.math_bracket_block,
        RegionForm.block,
        BLOCK_MATH_PRIORITY,
        "FM-MATH-BLOCK-001",
    ),
    RecognizerDescriptor(
        RegionKind.math_environment_block,
        RegionForm.block,
        BLOCK_MATH_PRIORITY,
        "FM-MATH-BLOCK-001",
    ),
)

RECOGNIZER_BY_KIND: Final[Mapping[RegionKind, RecognizerDescriptor]] = MappingProxyType(
    {descriptor.kind: descriptor for descriptor in BUILTIN_RECOGNIZERS}
)

if len(RECOGNIZER_BY_KIND) != len(BUILTIN_RECOGNIZERS):
    raise InvalidRegionError("built-in recognizer kinds must be unique")
if tuple(descriptor.priority for descriptor in BUILTIN_RECOGNIZERS) != tuple(
    sorted(descriptor.priority for descriptor in BUILTIN_RECOGNIZERS)
):
    raise InvalidRegionError("built-in recognizers must be ordered by priority")
