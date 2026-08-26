"""Private source-preservation primitives for Flowmark's formatting pipeline."""

from flowmark.preservation.model import (
    Candidate,
    ContainerContext,
    InvalidRegionError,
    InvalidUtf8Error,
    NormalizedSource,
    PreservationError,
    ProtectedRegion,
    RegionForm,
    RegionKind,
    validate_regions,
)
from flowmark.preservation.normalization import (
    finalize_output,
    normalize_source,
    scalar_width,
    scalar_widths,
)
from flowmark.preservation.registry import (
    BLOCK_RECOGNIZER_BY_KIND,
    BUILTIN_BLOCK_RECOGNIZERS,
    BUILTIN_RECOGNIZERS,
    RECOGNIZER_BY_KIND,
    BlockRecognizerDescriptor,
    BlockRuleKind,
    RecognizerDescriptor,
)
from flowmark.preservation.scanner import (
    ContainerLine,
    InlineScope,
    OpaqueBlock,
    build_container_view,
    scan_protected_regions,
)

__all__ = [
    "BLOCK_RECOGNIZER_BY_KIND",
    "BUILTIN_BLOCK_RECOGNIZERS",
    "BUILTIN_RECOGNIZERS",
    "RECOGNIZER_BY_KIND",
    "BlockRecognizerDescriptor",
    "BlockRuleKind",
    "Candidate",
    "ContainerContext",
    "ContainerLine",
    "InlineScope",
    "InvalidRegionError",
    "InvalidUtf8Error",
    "NormalizedSource",
    "OpaqueBlock",
    "PreservationError",
    "ProtectedRegion",
    "RecognizerDescriptor",
    "RegionForm",
    "RegionKind",
    "build_container_view",
    "finalize_output",
    "normalize_source",
    "scalar_width",
    "scalar_widths",
    "scan_protected_regions",
    "validate_regions",
]
