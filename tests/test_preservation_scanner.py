from flowmark.preservation.model import Candidate, RegionForm, RegionKind
from flowmark.preservation.normalization import normalize_source
from flowmark.preservation.scanner import (
    arbitrate_candidates,
    escape_is_even,
    scan_dollar_runs,
    scan_inline_scope,
    scan_protected_regions,
)


def _sources(text: str) -> list[str]:
    source = normalize_source(text)
    return [
        candidate.to_region(source, index=index).source
        for index, candidate in enumerate(scan_inline_scope(source, 0, source.byte_length))
    ]


def test_escape_parity_uses_the_immediately_preceding_backslash_run() -> None:
    text = r"\$ \\$ \\\$ \\\\$"
    dollar_positions = [index for index, scalar in enumerate(text) if scalar == "$"]

    assert [escape_is_even(text, position) for position in dollar_positions] == [
        False,
        True,
        False,
        True,
    ]


def test_dollar_state_machine_consumes_runs_and_retains_fallback_singles() -> None:
    assert _sources("$a$$b$ $$x$$ $$$$") == ["$a$", "$b$", "$$x$$", "$$$$"]

    source = normalize_source("$$ unmatched $a$ tail")
    candidates = scan_dollar_runs(source, 0, source.byte_length)
    assert [
        candidate.to_region(source, index=index).source
        for index, candidate in enumerate(candidates)
    ] == ["$a$"]


def test_composites_and_code_use_exact_backtick_run_lengths() -> None:
    text = "$``a ` b``$ {math}``x ` y`` ``code ` body`` and $z$"

    assert _sources(text) == [
        "$``a ` b``$",
        "{math}``x ` y``",
        "``code ` body``",
        "$z$",
    ]

    protected = scan_protected_regions(normalize_source(text))
    assert [region.source for region in protected] == [
        "$``a ` b``$",
        "{math}``x ` y``",
        "$z$",
    ]


def test_paren_and_nested_environment_candidates_are_source_exact() -> None:
    text = r"α \(a + b\) \begin{outer}\begin{inner}x\end{inner}\end{outer}"

    source = normalize_source(text)
    regions = scan_protected_regions(source)

    assert [region.source for region in regions] == [
        r"\(a + b\)",
        r"\begin{outer}\begin{inner}x\end{inner}\end{outer}",
    ]
    assert regions[0].start == len("α ".encode())

    unmatched = normalize_source(r"\begin{outer}\begin{inner}x\end{inner} tail")
    assert [region.source for region in scan_protected_regions(unmatched)] == [
        r"\begin{inner}x\end{inner}"
    ]

    malformed = normalize_source(r"\begin{bad\begin{good}x\end{good}")
    assert [region.source for region in scan_protected_regions(malformed)] == [
        r"\begin{good}x\end{good}"
    ]


def test_arbitration_uses_start_priority_length_and_kind() -> None:
    candidates = (
        Candidate(RegionKind.math_dollar_inline, RegionForm.inline, 0, 9),
        Candidate(RegionKind.code_span, RegionForm.inline, 0, 5),
        Candidate(RegionKind.math_double_dollar_inline, RegionForm.inline, 0, 11),
        Candidate(RegionKind.math_dollar_inline, RegionForm.inline, 12, 15),
    )

    assert arbitrate_candidates(candidates) == (candidates[1], candidates[3])


def test_default_scopes_never_pair_across_blank_lines() -> None:
    source = normalize_source("first $a\n\nsecond and $c$")

    assert [region.source for region in scan_protected_regions(source)] == ["$c$"]


def test_default_scopes_separate_headings_and_structural_table_cells() -> None:
    heading = normalize_source("# heading $a\nparagraph and $c$")
    assert [region.source for region in scan_protected_regions(heading)] == ["$c$"]

    table = normalize_source("| First | Second |\n| --- | --- |\n| $a | plain and $c$ |")
    assert [region.source for region in scan_protected_regions(table)] == ["$c$"]
