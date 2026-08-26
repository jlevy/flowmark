"""Ordered built-in recognizer metadata shared by scanner stages."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from flowmark.preservation.model import InvalidRegionError, RegionForm, RegionKind

# Lower bands win arbitration. Gaps permit additive recognizers without renumbering the
# stable precedence families used by both ports.
COMPOSITE_INLINE_PRIORITY = 10
CODE_SPAN_PRIORITY = 20
UNAMBIGUOUS_INLINE_PRIORITY = 30
DOLLAR_INLINE_PRIORITY = 40
OPAQUE_EXTENSION_BLOCK_PRIORITY = 45
BLOCK_MATH_PRIORITY = 50


class BlockRuleKind(StrEnum):
    """Stable pre-parse block rule names shared with the Rust port."""

    yaml_frontmatter = "yaml_frontmatter"
    toml_frontmatter = "toml_frontmatter"
    fenced_code = "fenced_code"
    indented_code = "indented_code"
    pandoc_multiline_table = "pandoc_multiline_table"
    obsidian_callout = "obsidian_callout"
    colon_container = "colon_container"
    definition_list = "definition_list"
    pandoc_grid_table = "pandoc_grid_table"
    math_dollar_block = "math_dollar_block"
    math_bracket_block = "math_bracket_block"
    math_environment_block = "math_environment_block"


@dataclass(frozen=True, slots=True)
class BlockRecognizerDescriptor:
    """Precedence and optional protected-region kind for a block rule."""

    kind: BlockRuleKind
    priority: int
    region_kind: RegionKind | None

    def __post_init__(self) -> None:
        if type(self.kind) is not BlockRuleKind:
            raise InvalidRegionError("block rule kind must use a stable enum value")
        if type(self.priority) is not int or self.priority < 0:
            raise InvalidRegionError("block rule priority must be a nonnegative integer")
        if self.region_kind is not None and self.region_kind not in {
            RegionKind.pandoc_multiline_table,
            RegionKind.obsidian_callout,
            RegionKind.colon_container,
            RegionKind.toml_frontmatter,
            RegionKind.definition_list,
            RegionKind.pandoc_grid_table,
            RegionKind.math_dollar_block,
            RegionKind.math_bracket_block,
            RegionKind.math_environment_block,
        }:
            raise InvalidRegionError("block rule region kind must use block treatment")


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
        RegionKind.pandoc_multiline_table,
        RegionForm.block,
        OPAQUE_EXTENSION_BLOCK_PRIORITY,
        "FM-EXT-MULTILINE-TABLE-001",
    ),
    RecognizerDescriptor(
        RegionKind.obsidian_callout,
        RegionForm.block,
        OPAQUE_EXTENSION_BLOCK_PRIORITY,
        "FM-EXT-OBSIDIAN-CALLOUT-001",
    ),
    RecognizerDescriptor(
        RegionKind.colon_container,
        RegionForm.block,
        OPAQUE_EXTENSION_BLOCK_PRIORITY,
        "FM-EXT-COLON-CONTAINER-001",
    ),
    RecognizerDescriptor(
        RegionKind.toml_frontmatter,
        RegionForm.block,
        OPAQUE_EXTENSION_BLOCK_PRIORITY,
        "FM-EXT-TOML-FRONTMATTER-001",
    ),
    RecognizerDescriptor(
        RegionKind.definition_list,
        RegionForm.block,
        OPAQUE_EXTENSION_BLOCK_PRIORITY,
        "FM-EXT-DEFINITION-LIST-001",
    ),
    RecognizerDescriptor(
        RegionKind.pandoc_grid_table,
        RegionForm.block,
        OPAQUE_EXTENSION_BLOCK_PRIORITY,
        "FM-EXT-GRID-TABLE-001",
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


# Existing opaque Markdown blocks win before registered preservation blocks. The distinct
# bands are part of the portable scanner contract; additions fit between them without
# changing existing values.
BUILTIN_BLOCK_RECOGNIZERS: Final[tuple[BlockRecognizerDescriptor, ...]] = (
    BlockRecognizerDescriptor(BlockRuleKind.yaml_frontmatter, 10, None),
    BlockRecognizerDescriptor(
        BlockRuleKind.toml_frontmatter,
        10,
        RegionKind.toml_frontmatter,
    ),
    BlockRecognizerDescriptor(BlockRuleKind.fenced_code, 20, None),
    BlockRecognizerDescriptor(BlockRuleKind.indented_code, 20, None),
    BlockRecognizerDescriptor(
        BlockRuleKind.pandoc_multiline_table,
        25,
        RegionKind.pandoc_multiline_table,
    ),
    BlockRecognizerDescriptor(
        BlockRuleKind.obsidian_callout,
        25,
        RegionKind.obsidian_callout,
    ),
    BlockRecognizerDescriptor(
        BlockRuleKind.colon_container,
        25,
        RegionKind.colon_container,
    ),
    BlockRecognizerDescriptor(
        BlockRuleKind.definition_list,
        25,
        RegionKind.definition_list,
    ),
    BlockRecognizerDescriptor(
        BlockRuleKind.pandoc_grid_table,
        25,
        RegionKind.pandoc_grid_table,
    ),
    BlockRecognizerDescriptor(
        BlockRuleKind.math_dollar_block,
        30,
        RegionKind.math_dollar_block,
    ),
    BlockRecognizerDescriptor(
        BlockRuleKind.math_bracket_block,
        30,
        RegionKind.math_bracket_block,
    ),
    BlockRecognizerDescriptor(
        BlockRuleKind.math_environment_block,
        30,
        RegionKind.math_environment_block,
    ),
)

BLOCK_RECOGNIZER_BY_KIND: Final[Mapping[BlockRuleKind, BlockRecognizerDescriptor]] = (
    MappingProxyType({descriptor.kind: descriptor for descriptor in BUILTIN_BLOCK_RECOGNIZERS})
)

if len(BLOCK_RECOGNIZER_BY_KIND) != len(BUILTIN_BLOCK_RECOGNIZERS):
    raise InvalidRegionError("built-in block recognizer kinds must be unique")
if tuple(descriptor.priority for descriptor in BUILTIN_BLOCK_RECOGNIZERS) != tuple(
    sorted(descriptor.priority for descriptor in BUILTIN_BLOCK_RECOGNIZERS)
):
    raise InvalidRegionError("built-in block recognizers must be ordered by priority")
