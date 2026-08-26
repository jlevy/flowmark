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
    BUILTIN_RECOGNIZERS,
    RECOGNIZER_BY_KIND,
    RecognizerDescriptor,
)

__all__ = [
    "BUILTIN_RECOGNIZERS",
    "RECOGNIZER_BY_KIND",
    "Candidate",
    "ContainerContext",
    "InvalidRegionError",
    "InvalidUtf8Error",
    "NormalizedSource",
    "PreservationError",
    "ProtectedRegion",
    "RecognizerDescriptor",
    "RegionForm",
    "RegionKind",
    "finalize_output",
    "normalize_source",
    "scalar_width",
    "scalar_widths",
    "validate_regions",
]
