from dataclasses import replace

import pytest

from flowmark.preservation.model import (
    Candidate,
    ContainerContext,
    InvalidRegionError,
    InvalidUtf8Error,
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
    BlockRuleKind,
)


def test_normalization_has_one_bom_and_terminal_lf() -> None:
    normalized = normalize_source(b"\xef\xbb\xbfalpha\r\nbeta\rgamma\r\n\r\n")

    assert normalized.text == "alpha\nbeta\ngamma\n"
    assert normalized.utf8 == b"alpha\nbeta\ngamma\n"
    assert normalized.had_bom
    assert finalize_output(normalized, "result\r\n\r\n") == "\ufeffresult\n"

    assert normalize_source("").text == "\n"
    assert normalize_source("unterminated").text == "unterminated\n"
    assert normalize_source("trailing space \n\n").text == "trailing space \n"


def test_normalization_rejects_invalid_utf8_and_surrogates() -> None:
    with pytest.raises(InvalidUtf8Error, match="input is not valid UTF-8"):
        normalize_source(b"before\xffafter")

    with pytest.raises(InvalidUtf8Error, match="input is not valid UTF-8"):
        normalize_source("before\ud800after")


def test_region_enums_render_stable_values_on_every_supported_python() -> None:
    assert str(RegionKind.math_dollar_inline) == "math_dollar_inline"
    assert str(RegionForm.inline) == "inline"


def test_scalar_width_and_utf8_boundaries_are_distinct() -> None:
    normalized = normalize_source("a水😀")

    assert normalized.scalar_byte_offsets == (0, 1, 4, 8, 9)
    assert normalized.byte_offset(3) == 8
    assert normalized.scalar_index(8) == 3
    assert scalar_width("a水😀") == 3
    assert scalar_widths("a水\n😀") == (2, 1)

    with pytest.raises(InvalidRegionError, match="UTF-8 scalar boundary"):
        normalized.scalar_index(2)


def test_candidate_builds_a_source_exact_region() -> None:
    normalized = normalize_source("α $x_1$ tail")
    start = normalized.byte_offset(2)
    end = normalized.byte_offset(7)
    candidate = Candidate(
        kind=RegionKind.math_dollar_inline,
        form=RegionForm.inline,
        start=start,
        end=end,
    )

    region = candidate.to_region(normalized, index=0)

    assert region.source == "$x_1$"
    assert region.logical_widths == (5,)
    assert validate_regions(normalized, (region,)) == (region,)


def test_block_region_retains_its_exact_parser_scaffold() -> None:
    normalized = normalize_source("\t- $$\n\t  x\n\t  $$")
    candidate = Candidate(
        kind=RegionKind.math_dollar_block,
        form=RegionForm.block,
        start=0,
        end=normalized.byte_length,
        scaffold_prefix="\t- ",
    )

    region = candidate.to_region(normalized, index=0)

    assert region.scaffold_prefix == "\t- "
    assert region.source == normalized.text

    with pytest.raises(InvalidRegionError, match="must match"):
        replace(region, scaffold_prefix="> ")

    with pytest.raises(InvalidRegionError, match="cannot define"):
        ProtectedRegion(
            index=0,
            kind=RegionKind.math_dollar_inline,
            form=RegionForm.inline,
            start=0,
            end=3,
            source="$x$",
            logical_widths=(3,),
            scaffold_prefix="- ",
        )


def test_region_validation_rejects_overlap_source_drift_and_bad_indexes() -> None:
    normalized = normalize_source("$a$ and $b$")
    first = Candidate(
        kind=RegionKind.math_dollar_inline,
        form=RegionForm.inline,
        start=0,
        end=3,
    ).to_region(normalized, index=0)
    second = Candidate(
        kind=RegionKind.math_dollar_inline,
        form=RegionForm.inline,
        start=8,
        end=11,
    ).to_region(normalized, index=1)

    assert validate_regions(normalized, (first, second)) == (first, second)

    overlapping = ProtectedRegion(
        index=1,
        kind=RegionKind.math_dollar_inline,
        form=RegionForm.inline,
        start=2,
        end=11,
        source="$ and $b$",
        logical_widths=(9,),
    )
    with pytest.raises(InvalidRegionError, match="overlap"):
        validate_regions(normalized, (first, overlapping))

    with pytest.raises(InvalidRegionError, match="source slice"):
        validate_regions(normalized, (first, replace(second, source="$c$")))

    with pytest.raises(InvalidRegionError, match="contiguous source-order indexes"):
        validate_regions(normalized, (first, replace(second, index=2)))


def test_container_and_registry_invariants_are_portable() -> None:
    assert ContainerContext(blockquote_depth=2, list_depth=1, content_column=4)

    assert ContainerContext(content_column=3)

    with pytest.raises(InvalidRegionError, match="positive"):
        ContainerContext(list_depth=1, content_column=0)

    with pytest.raises(InvalidRegionError, match="cannot use inline treatment"):
        Candidate(
            kind=RegionKind.math_dollar_block,
            form=RegionForm.inline,
            start=0,
            end=2,
        )

    kinds = [descriptor.kind for descriptor in BUILTIN_RECOGNIZERS]
    assert len(kinds) == len(set(kinds))
    assert tuple(descriptor.priority for descriptor in BUILTIN_RECOGNIZERS) == tuple(
        sorted(descriptor.priority for descriptor in BUILTIN_RECOGNIZERS)
    )
    assert set(RECOGNIZER_BY_KIND) == set(kinds)
    assert (
        RECOGNIZER_BY_KIND[RegionKind.math_gitlab_inline].priority
        < RECOGNIZER_BY_KIND[RegionKind.code_span].priority
    )
    assert (
        RECOGNIZER_BY_KIND[RegionKind.code_span].priority
        < RECOGNIZER_BY_KIND[RegionKind.math_dollar_inline].priority
    )
    block_kinds = [descriptor.kind for descriptor in BUILTIN_BLOCK_RECOGNIZERS]
    assert set(BLOCK_RECOGNIZER_BY_KIND) == set(block_kinds)
    assert (
        BLOCK_RECOGNIZER_BY_KIND[BlockRuleKind.fenced_code].priority
        < BLOCK_RECOGNIZER_BY_KIND[BlockRuleKind.math_dollar_block].priority
    )
