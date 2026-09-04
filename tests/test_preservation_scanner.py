from flowmark.preservation.model import Candidate, RegionForm, RegionKind
from flowmark.preservation.normalization import normalize_source
from flowmark.preservation.registry import BlockRuleKind
from flowmark.preservation.scanner import (
    _may_contain_protected_syntax,  # pyright: ignore[reportPrivateUsage]
    arbitrate_candidates,
    build_container_view,
    escape_is_even,
    scan_angle_spans,
    scan_dollar_runs,
    scan_existing_opaque_blocks,
    scan_inline_scope,
    scan_protected_regions,
    scan_wikilinks,
)


def _sources(text: str) -> list[str]:
    source = normalize_source(text)
    return [
        candidate.to_region(source, index=index).source
        for index, candidate in enumerate(scan_inline_scope(source, 0, source.byte_length))
    ]


def test_preservation_admission_filter_covers_every_syntax_family() -> None:
    for source in (
        "`code`",
        "$math$",
        r"\(math\)",
        "[[page]]",
        "> [!NOTE] callout",
        "<span>raw</span>",
        "text{#id}",
        "header | cell\n--- | ---",
        "::: note\n:::",
        "+++\ntitle = 'x'\n+++",
        ">>>\nquote\n>>>",
        "---\nvalue\n---",
        "term\n: definition",
        "> 1. ~ definition",
        "[issue:123]",
    ):
        assert _may_contain_protected_syntax(source), source

    assert not _may_contain_protected_syntax(
        "ordinary prose: punctuation, [links](target), and hyphen-words"
    )


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
        "``code ` body``",
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

    assert arbitrate_candidates(candidates, start=0, end=15) == (
        candidates[1],
        candidates[3],
    )


def test_default_scopes_never_pair_across_blank_lines() -> None:
    source = normalize_source("first $a\n\nsecond and $c$")

    assert [region.source for region in scan_protected_regions(source)] == ["$c$"]


def test_default_scopes_separate_headings_and_structural_table_cells() -> None:
    heading = normalize_source("# heading $a\nparagraph and $c$")
    assert [region.source for region in scan_protected_regions(heading)] == ["$c$"]

    table = normalize_source("| First | Second |\n| --- | --- |\n| $a | plain and $c$ |")
    assert [region.source for region in scan_protected_regions(table)] == ["$c$"]


def test_container_view_tracks_item_identity_and_nested_prefix_order() -> None:
    source = normalize_source(
        "> $$\n> body\n> $$\n\n- $$\n  body\n  $$\n\n1. > \\[\n   > body\n   > \\]\n\n- $$\n- $$"
    )
    lines = build_container_view(source)

    assert lines[0].container_key == lines[1].container_key == lines[2].container_key
    assert lines[0].context.blockquote_depth == 1
    assert lines[4].container_key == lines[5].container_key == lines[6].container_key
    assert lines[4].context.list_depth == 1
    assert lines[4].context.content_column == 2
    assert lines[8].container_key == lines[9].container_key == lines[10].container_key
    assert lines[8].context.blockquote_depth == 1
    assert lines[8].context.list_depth == 1
    assert lines[8].context.content_column == 3
    assert lines[12].container_key != lines[13].container_key

    lazy_source = normalize_source("> quote $a +\nb$ tail\n\n- list $c +\nd$ tail")
    lazy_lines = build_container_view(lazy_source)
    assert lazy_lines[1].lazy
    assert lazy_lines[0].container_key == lazy_lines[1].container_key
    assert lazy_lines[4].lazy
    assert lazy_lines[3].container_key == lazy_lines[4].container_key
    lazy_regions = scan_protected_regions(lazy_source)
    assert [region.container.blockquote_depth for region in lazy_regions] == [1, 0]
    assert [region.container.list_depth for region in lazy_regions] == [0, 1]


def test_block_math_preserves_raw_container_prefixes_and_suffixes() -> None:
    source = normalize_source(
        "> $$\n> quoted\n> $$ (label)\n\n"
        "- $$\n  listed\n  $$ {#id .wide}\n\n"
        "1. > \\[\n   > nested\n   > \\]"
    )
    regions = scan_protected_regions(source)

    assert [region.kind for region in regions] == [
        RegionKind.math_dollar_block,
        RegionKind.math_dollar_block,
        RegionKind.math_bracket_block,
    ]
    assert [region.source for region in regions] == [
        "> $$\n> quoted\n> $$ (label)\n",
        "- $$\n  listed\n  $$ {#id .wide}\n",
        "1. > \\[\n   > nested\n   > \\]\n",
    ]
    assert [region.scaffold_prefix for region in regions] == ["> ", "- ", "1. > "]


def test_block_scaffold_excludes_optional_markdown_indent() -> None:
    source = normalize_source("  $$\n  body\n  $$\n\n>   $$\n>   quoted\n>   $$")
    regions = scan_protected_regions(source)

    assert [region.source for region in regions] == [
        "  $$\n  body\n  $$\n",
        ">   $$\n>   quoted\n>   $$\n",
    ]
    assert [region.scaffold_prefix for region in regions] == ["", "> "]


def test_attribute_groups_require_valid_attributes_and_compatible_placement() -> None:
    source = normalize_source(
        '# Heading {#id .wide key="raw ..."}\n\n'
        "[link](url){.button}{#second} ordinary {.detached}\n\n"
        '{.standalone data-ü="välue"}\n\n'
        "[bad](url){#} [nested](url){.outer {#inner}}"
    )
    regions = scan_protected_regions(source)

    assert [region.kind for region in regions] == [
        RegionKind.attribute_group_inline,
        RegionKind.attribute_group_inline,
        RegionKind.attribute_group_inline,
        RegionKind.attribute_group_block,
    ]
    assert [region.source for region in regions] == [
        '{#id .wide key="raw ..."}',
        "{.button}",
        "{#second}",
        '{.standalone data-ü="välue"}\n',
    ]


def test_line_blocks_require_active_spaced_bars_and_do_not_claim_tables() -> None:
    source = normalize_source(
        "| first\n|\n| third $x$\n\n"
        "> | quoted\n> | continued\n\n"
        "| Header | Value |\n| --- | --- |\n| one | two |\n\n"
        "\\| escaped\n|unspaced\n    | code"
    )
    regions = scan_protected_regions(source)

    assert [region.kind for region in regions] == [
        RegionKind.pandoc_line_block,
        RegionKind.pandoc_line_block,
    ]
    assert [region.source for region in regions] == [
        "| first\n|\n| third $x$\n",
        "> | quoted\n> | continued\n",
    ]


def test_line_blocks_do_not_claim_single_column_gfm_tables() -> None:
    source = normalize_source("| Header |\n| --- |\n| There’s a value |\n")

    assert scan_protected_regions(source) == ()


def test_general_myst_roles_and_wikilinks_preserve_priority_and_nesting() -> None:
    source = normalize_source(
        "{ref}`target` {custom:name}``body `tick` `` {math}`x_y`\n\n"
        "[[Note]] ![[Page#A|Alias]] [[outer [[inner]] tail]]\n\n"
        "``{ref}`inside` `` \\[[escaped]] [[]] {bad role}`x`"
    )
    regions = scan_protected_regions(source)

    assert [region.kind for region in regions] == [
        RegionKind.myst_role_inline,
        RegionKind.myst_role_inline,
        RegionKind.math_myst_inline,
        RegionKind.wikilink_inline,
        RegionKind.wikilink_inline,
        RegionKind.wikilink_inline,
        RegionKind.code_span,
        RegionKind.code_span,
    ]
    assert [region.source for region in regions[:6]] == [
        "{ref}`target`",
        "{custom:name}``body `tick` ``",
        "{math}`x_y`",
        "[[Note]]",
        "![[Page#A|Alias]]",
        "[[outer [[inner]] tail]]",
    ]


def test_wikilink_closability_preserves_nested_and_overlapping_fallbacks() -> None:
    nested = normalize_source("[[ [[ y ]] x")
    nested_candidates = scan_wikilinks(nested, 0, nested.byte_length)
    assert [candidate.to_region(nested, index=0).source for candidate in nested_candidates] == [
        "[[ y ]]"
    ]

    overlapping = normalize_source("[[[[x]]")
    overlapping_candidates = scan_wikilinks(overlapping, 0, overlapping.byte_length)
    assert [
        candidate.to_region(overlapping, index=0).source for candidate in overlapping_candidates
    ] == ["[[[x]]"]

    unclosed = normalize_source("[[" * 32_768)
    assert scan_wikilinks(unclosed, 0, unclosed.byte_length) == ()


def test_gitlab_references_are_allowlisted_and_fail_closed() -> None:
    source = normalize_source(
        '[issue:_123_] [cadence:"plan a"] [wiki_page:首页] '
        "[unknown:_123_] [issue:] \\[issue:_456_] `[issue:_789_]`"
    )

    regions = scan_protected_regions(source)

    assert [region.kind for region in regions] == [
        RegionKind.gitlab_reference_inline,
        RegionKind.gitlab_reference_inline,
        RegionKind.gitlab_reference_inline,
        RegionKind.code_span,
    ]
    assert [region.source for region in regions] == [
        "[issue:_123_]",
        '[cadence:"plan a"]',
        "[wiki_page:首页]",
        "`[issue:_789_]`",
    ]


def test_gitlab_reference_pipe_is_not_a_table_cell_boundary() -> None:
    source = normalize_source(
        '| Kind | Reference |\n| --- | --- |\n| Cadence | [cadence:"plan | a"] |'
    )

    regions = scan_protected_regions(source)

    assert [region.source for region in regions] == ['[cadence:"plan | a"]']


def test_gitlab_multiline_blockquotes_require_compatible_paired_fences() -> None:
    source = normalize_source(
        ">>>\nroot\n\nsecond root block\n>>>\n\n"
        "- >>>\n  list body\n  >>>\n\n"
        "> >>>\n> nested body\n> >>>\n\n"
        ">>> unmatched\n\n    >>>\n    code\n    >>>\n\n>>>"
    )

    regions = scan_protected_regions(source)

    assert [region.kind for region in regions] == [
        RegionKind.gitlab_multiline_blockquote,
        RegionKind.gitlab_multiline_blockquote,
        RegionKind.gitlab_multiline_blockquote,
    ]
    assert [region.source for region in regions] == [
        ">>>\nroot\n\nsecond root block\n>>>\n",
        "- >>>\n  list body\n  >>>\n",
        "> >>>\n> nested body\n> >>>\n",
    ]


def test_existing_opaque_blocks_win_before_math_scanning() -> None:
    source = normalize_source(
        "---\nitems:\n- one\nmath: $not_inline$\n---\n\n"
        "```math\n$$\nnot display\n$$\n```\n\n"
        "    $$\n    indented\n    $$\n\n"
        "$$\nreal display\n$$"
    )
    opaque = scan_existing_opaque_blocks(source)

    assert [block.kind for block in opaque] == [
        BlockRuleKind.yaml_frontmatter,
        BlockRuleKind.fenced_code,
        BlockRuleKind.indented_code,
    ]
    assert [region.source for region in scan_protected_regions(source)] == [
        "$$\nreal display\n$$\n"
    ]


def test_multiline_table_requires_a_complete_structural_pair() -> None:
    source = normalize_source(
        "-----\nHeader A   Header B\n--- ---\nvalue      value\n\nnext       row\n-----\n\n---"
    )

    regions = scan_protected_regions(source)

    assert [region.kind for region in regions] == [RegionKind.pandoc_multiline_table]
    assert regions[0].source.endswith("next       row\n-----\n")


def test_callout_marker_must_be_the_first_line_of_its_quote() -> None:
    source = normalize_source(
        "> ordinary first line\n> [!note] too late\n\n> [!tip]- valid\ncontinued lazily"
    )

    regions = scan_protected_regions(source)

    assert [region.kind for region in regions] == [RegionKind.obsidian_callout]
    assert regions[0].source == "> [!tip]- valid\ncontinued lazily\n"


def test_colon_container_closers_ignore_run_length_and_fenced_code() -> None:
    source = normalize_source(":::: outer\n```text\n:::\n```\n::: inner\nbody\n:::::\n:::\n")

    regions = scan_protected_regions(source)

    assert [region.kind for region in regions] == [RegionKind.colon_container]
    assert regions[0].source == source.text


def test_toml_frontmatter_requires_exact_root_delimiters() -> None:
    valid = scan_protected_regions(normalize_source('+++\ntitle = "raw"\n+++\nbody'))
    indented = scan_protected_regions(normalize_source(' +++\ntitle = "ordinary"\n+++'))

    assert [region.kind for region in valid] == [RegionKind.toml_frontmatter]
    assert not any(region.kind is RegionKind.toml_frontmatter for region in indented)


def test_definition_lists_require_marker_columns_and_stop_before_plain_suffix() -> None:
    source = normalize_source(
        "Term\n: Definition\n\n  Continued block\n\nSuffix\n\nNot a term\n   : over-indented"
    )
    regions = scan_protected_regions(source)

    assert [region.kind for region in regions] == [RegionKind.definition_list]
    assert regions[0].source == "Term\n: Definition\n\n  Continued block\n"


def test_grid_tables_require_compatible_outer_borders() -> None:
    source = normalize_source(
        "+-----+-----+\n| A   | B   |\n+=====+=====+\n| 1   | 2   |\n+-----+-----+\n\n"
        "+---+---+\nnot a table\n+---+---+"
    )
    regions = scan_protected_regions(source)

    assert [region.kind for region in regions] == [RegionKind.pandoc_grid_table]
    assert regions[0].source.endswith("| 1   | 2   |\n+-----+-----+\n")


def test_raw_html_uses_explicit_and_blank_line_end_conditions() -> None:
    source = normalize_source(
        "<!-- raw\n\n-->\n\n<div>\n*raw*\n</div>\n\nFollowing\n\n"
        "paragraph\n<x-card>\nnot type seven\n\n- item\n<!-- closing -->"
    )
    regions = scan_protected_regions(source)

    assert [region.kind for region in regions] == [
        RegionKind.raw_html_block,
        RegionKind.raw_html_block,
        RegionKind.raw_html_inline,
        RegionKind.raw_html_block,
    ]
    assert regions[0].source == "<!-- raw\n\n-->\n"
    assert regions[1].source == "<div>\n*raw*\n</div>\n"
    assert regions[2].source == "<x-card>"
    assert regions[3].source == "<!-- closing -->\n"
    assert regions[3].container.list_depth == 0


def test_angle_scanner_rejects_comparisons_and_accepts_html_and_autolinks() -> None:
    source = normalize_source(
        "| Fast | Slow |\n"
        "| --- | --- |\n"
        "| <15min | >25min |\n"
        "| <1.5x | >2.5x |\n\n"
        "[link](<foo\nbar>) "
        '<x-card data-label="raw"> <https://example.com/a> <7@example.com> '
        "<!DOCTYPE html>"
    )

    assert [region.source for region in scan_protected_regions(source)] == [
        "<foo\nbar>",
        '<x-card data-label="raw">',
        "<https://example.com/a>",
        "<7@example.com>",
        "<!DOCTYPE html>",
    ]


def test_angle_scanner_handles_many_unclosed_prose_comparisons() -> None:
    degenerate = normalize_source("<?>")
    assert scan_angle_spans(degenerate, 0, degenerate.byte_length) == ()
    complete = normalize_source("<??>")
    assert [
        candidate.to_region(complete, index=0).source
        for candidate in scan_angle_spans(complete, 0, complete.byte_length)
    ] == ["<??>"]

    source = normalize_source("The build takes <15min and speedup is <1.5x.\n" * 8_192)
    assert scan_angle_spans(source, 0, source.byte_length) == ()


def test_unmatched_outer_block_retains_closed_inner_and_not_sibling_closers() -> None:
    source = normalize_source("\\begin{outer}\n\\begin{inner}\nbody\n\\end{inner}\n\n- $$\n- $$")

    assert [region.source for region in scan_protected_regions(source)] == [
        "\\begin{inner}\nbody\n\\end{inner}\n"
    ]


def test_non_nesting_bracket_display_uses_first_opener_and_next_closer() -> None:
    source = normalize_source("\\[\n\\[\nbody\n\\]")

    assert [region.source for region in scan_protected_regions(source)] == ["\\[\n\\[\nbody\n\\]\n"]
