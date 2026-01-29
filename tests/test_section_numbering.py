"""Tests for section numbering detection and renumbering."""

from flowmark.transforms.section_numbering import (
    FormatComponent,
    NumberStyle,
    SectionNumConvention,
    SectionNumFormat,
    SectionRenumberer,
    alpha_to_int,
    apply_hierarchical_constraint,
    extract_section_prefix,
    infer_format_for_level,
    infer_section_convention,
    infer_style,
    int_to_alpha,
    int_to_roman,
    normalize_convention,
    renumber_headings,
    roman_to_int,
)

# === Phase 1: Core Data Structures ===


class TestNumberStyle:
    """Tests for NumberStyle enum."""

    def test_enum_values(self) -> None:
        """NumberStyle has all expected values."""
        assert NumberStyle.arabic == "arabic"
        assert NumberStyle.roman_upper == "roman_upper"
        assert NumberStyle.roman_lower == "roman_lower"
        assert NumberStyle.alpha_upper == "alpha_upper"
        assert NumberStyle.alpha_lower == "alpha_lower"

    def test_enum_is_string(self) -> None:
        """NumberStyle values can be used as strings."""
        assert NumberStyle.arabic.value == "arabic"
        assert NumberStyle.roman_upper.value == "roman_upper"
        # Can compare directly with strings
        assert NumberStyle.arabic == "arabic"
        assert NumberStyle.roman_upper == "roman_upper"


class TestFormatComponent:
    """Tests for FormatComponent dataclass."""

    def test_create_arabic_component(self) -> None:
        """Can create a FormatComponent with arabic style."""
        comp = FormatComponent(level=1, style=NumberStyle.arabic)
        assert comp.level == 1
        assert comp.style == NumberStyle.arabic

    def test_create_roman_component(self) -> None:
        """Can create a FormatComponent with roman style."""
        comp = FormatComponent(level=2, style=NumberStyle.roman_upper)
        assert comp.level == 2
        assert comp.style == NumberStyle.roman_upper


class TestSectionNumFormat:
    """Tests for SectionNumFormat dataclass."""

    def test_format_string_single_arabic(self) -> None:
        """format_string() returns correct format for single arabic component."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        assert fmt.format_string() == "{h1:arabic}."

    def test_format_string_two_arabic(self) -> None:
        """format_string() returns correct format for two arabic components."""
        fmt = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        assert fmt.format_string() == "{h1:arabic}.{h2:arabic}"

    def test_format_string_mixed_styles(self) -> None:
        """format_string() returns correct format for mixed styles."""
        fmt = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.roman_upper),
                FormatComponent(level=2, style=NumberStyle.alpha_upper),
            ],
            trailing="",
        )
        assert fmt.format_string() == "{h1:roman_upper}.{h2:alpha_upper}"

    def test_format_number_single_arabic(self) -> None:
        """format_number() formats single arabic number correctly."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        counters = [2, 0, 0, 0, 0, 0]
        assert fmt.format_number(counters) == "2."

    def test_format_number_two_arabic(self) -> None:
        """format_number() formats two arabic numbers correctly."""
        fmt = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        counters = [2, 3, 0, 0, 0, 0]
        assert fmt.format_number(counters) == "2.3"

    def test_format_number_roman_upper(self) -> None:
        """format_number() formats roman upper correctly."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.roman_upper)],
            trailing=".",
        )
        counters = [4, 0, 0, 0, 0, 0]
        assert fmt.format_number(counters) == "IV."

    def test_format_number_alpha_upper(self) -> None:
        """format_number() formats alpha upper correctly."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.alpha_upper)],
            trailing=".",
        )
        counters = [3, 0, 0, 0, 0, 0]
        assert fmt.format_number(counters) == "C."

    def test_format_number_mixed_roman_alpha(self) -> None:
        """format_number() formats mixed roman+alpha correctly."""
        fmt = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.roman_upper),
                FormatComponent(level=2, style=NumberStyle.alpha_upper),
            ],
            trailing="",
        )
        counters = [2, 3, 0, 0, 0, 0]
        assert fmt.format_number(counters) == "II.C"


class TestSectionNumConvention:
    """Tests for SectionNumConvention dataclass."""

    def test_max_depth_none(self) -> None:
        """max_depth returns 0 when no levels are numbered."""
        conv = SectionNumConvention(levels=(None, None, None, None, None, None))
        assert conv.max_depth == 0

    def test_max_depth_h1_only(self) -> None:
        """max_depth returns 1 when only H1 is numbered."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        conv = SectionNumConvention(levels=(fmt, None, None, None, None, None))
        assert conv.max_depth == 1

    def test_max_depth_h1_h2(self) -> None:
        """max_depth returns 2 when H1 and H2 are numbered."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, None, None, None, None))
        assert conv.max_depth == 2

    def test_is_active_false_when_no_levels(self) -> None:
        """is_active returns False when no levels are numbered."""
        conv = SectionNumConvention(levels=(None, None, None, None, None, None))
        assert conv.is_active is False

    def test_is_active_true_when_h1_numbered(self) -> None:
        """is_active returns True when H1 is numbered."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        conv = SectionNumConvention(levels=(fmt, None, None, None, None, None))
        assert conv.is_active is True

    def test_str_none(self) -> None:
        """__str__ returns 'none' when no levels are numbered."""
        conv = SectionNumConvention(levels=(None, None, None, None, None, None))
        assert str(conv) == "none"

    def test_str_h1_only(self) -> None:
        """__str__ returns H1 format when only H1 is numbered."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        conv = SectionNumConvention(levels=(fmt, None, None, None, None, None))
        assert str(conv) == "H1: {h1:arabic}."

    def test_str_h1_h2(self) -> None:
        """__str__ returns both formats when H1 and H2 are numbered."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, None, None, None, None))
        assert str(conv) == "H1: {h1:arabic}., H2: {h1:arabic}.{h2:arabic}"


# === Phase 2: Prefix Extraction (Parsing) ===


class TestRomanConversion:
    """Tests for Roman numeral conversion functions."""

    def test_int_to_roman_basic(self) -> None:
        """int_to_roman converts basic numbers correctly."""
        assert int_to_roman(1) == "I"
        assert int_to_roman(2) == "II"
        assert int_to_roman(3) == "III"
        assert int_to_roman(4) == "IV"
        assert int_to_roman(5) == "V"
        assert int_to_roman(9) == "IX"
        assert int_to_roman(10) == "X"

    def test_int_to_roman_larger(self) -> None:
        """int_to_roman converts larger numbers correctly."""
        assert int_to_roman(14) == "XIV"
        assert int_to_roman(49) == "XLIX"
        assert int_to_roman(50) == "L"
        assert int_to_roman(100) == "C"
        assert int_to_roman(500) == "D"
        assert int_to_roman(1000) == "M"

    def test_roman_to_int_basic(self) -> None:
        """roman_to_int converts basic numerals correctly."""
        assert roman_to_int("I") == 1
        assert roman_to_int("II") == 2
        assert roman_to_int("III") == 3
        assert roman_to_int("IV") == 4
        assert roman_to_int("V") == 5
        assert roman_to_int("IX") == 9
        assert roman_to_int("X") == 10

    def test_roman_to_int_lowercase(self) -> None:
        """roman_to_int handles lowercase input."""
        assert roman_to_int("iv") == 4
        assert roman_to_int("xiv") == 14


class TestAlphaConversion:
    """Tests for alphabetic conversion functions."""

    def test_int_to_alpha_basic(self) -> None:
        """int_to_alpha converts basic numbers correctly."""
        assert int_to_alpha(1) == "A"
        assert int_to_alpha(2) == "B"
        assert int_to_alpha(3) == "C"
        assert int_to_alpha(26) == "Z"

    def test_int_to_alpha_double(self) -> None:
        """int_to_alpha handles numbers beyond 26."""
        assert int_to_alpha(27) == "AA"
        assert int_to_alpha(28) == "AB"
        assert int_to_alpha(52) == "AZ"
        assert int_to_alpha(53) == "BA"

    def test_alpha_to_int_basic(self) -> None:
        """alpha_to_int converts basic letters correctly."""
        assert alpha_to_int("A") == 1
        assert alpha_to_int("B") == 2
        assert alpha_to_int("C") == 3
        assert alpha_to_int("Z") == 26

    def test_alpha_to_int_double(self) -> None:
        """alpha_to_int handles double letters."""
        assert alpha_to_int("AA") == 27
        assert alpha_to_int("AB") == 28
        assert alpha_to_int("AZ") == 52
        assert alpha_to_int("BA") == 53

    def test_alpha_to_int_lowercase(self) -> None:
        """alpha_to_int handles lowercase input."""
        assert alpha_to_int("a") == 1
        assert alpha_to_int("aa") == 27


class TestInferStyle:
    """Tests for infer_style function."""

    def test_arabic_digits(self) -> None:
        """Digits are inferred as arabic."""
        assert infer_style("1") == NumberStyle.arabic
        assert infer_style("123") == NumberStyle.arabic
        assert infer_style("10") == NumberStyle.arabic

    def test_roman_upper(self) -> None:
        """Roman numeral characters (uppercase) are inferred as roman_upper."""
        assert infer_style("I") == NumberStyle.roman_upper
        assert infer_style("IV") == NumberStyle.roman_upper
        assert infer_style("XII") == NumberStyle.roman_upper
        assert infer_style("MCMXCIV") == NumberStyle.roman_upper

    def test_roman_lower(self) -> None:
        """Roman numeral characters (lowercase) are inferred as roman_lower."""
        assert infer_style("i") == NumberStyle.roman_lower
        assert infer_style("iv") == NumberStyle.roman_lower
        assert infer_style("xii") == NumberStyle.roman_lower

    def test_alpha_upper(self) -> None:
        """Non-Roman uppercase letters are inferred as alpha_upper."""
        assert infer_style("A") == NumberStyle.alpha_upper
        assert infer_style("B") == NumberStyle.alpha_upper
        assert infer_style("AA") == NumberStyle.alpha_upper
        assert infer_style("AZ") == NumberStyle.alpha_upper

    def test_alpha_lower(self) -> None:
        """Non-Roman lowercase letters are inferred as alpha_lower."""
        assert infer_style("a") == NumberStyle.alpha_lower
        assert infer_style("b") == NumberStyle.alpha_lower
        assert infer_style("aa") == NumberStyle.alpha_lower


class TestExtractSectionPrefix:
    """Tests for extract_section_prefix function."""

    def test_arabic_single_with_period(self) -> None:
        """Extract single arabic with period trailing."""
        result = extract_section_prefix("1. Introduction")
        assert result is not None
        assert result.components == ["1"]
        assert result.styles == [NumberStyle.arabic]
        assert result.trailing == "."
        assert result.title == "Introduction"

    def test_arabic_single_with_paren(self) -> None:
        """Extract single arabic with paren trailing."""
        result = extract_section_prefix("1) Introduction")
        assert result is not None
        assert result.components == ["1"]
        assert result.styles == [NumberStyle.arabic]
        assert result.trailing == ")"
        assert result.title == "Introduction"

    def test_arabic_single_no_trailing(self) -> None:
        """Extract single arabic with no trailing char."""
        result = extract_section_prefix("1 Introduction")
        assert result is not None
        assert result.components == ["1"]
        assert result.styles == [NumberStyle.arabic]
        assert result.trailing == ""
        assert result.title == "Introduction"

    def test_arabic_decimal(self) -> None:
        """Extract decimal arabic like 1.2."""
        result = extract_section_prefix("1.2 Details")
        assert result is not None
        assert result.components == ["1", "2"]
        assert result.styles == [NumberStyle.arabic, NumberStyle.arabic]
        assert result.trailing == ""
        assert result.title == "Details"

    def test_arabic_triple(self) -> None:
        """Extract triple arabic like 1.2.3."""
        result = extract_section_prefix("1.2.3 Deep")
        assert result is not None
        assert result.components == ["1", "2", "3"]
        assert result.styles == [NumberStyle.arabic, NumberStyle.arabic, NumberStyle.arabic]
        assert result.trailing == ""
        assert result.title == "Deep"

    def test_roman_upper_single(self) -> None:
        """Extract single roman upper."""
        result = extract_section_prefix("I. Introduction")
        assert result is not None
        assert result.components == ["I"]
        assert result.styles == [NumberStyle.roman_upper]
        assert result.trailing == "."
        assert result.title == "Introduction"

    def test_roman_alpha_mixed(self) -> None:
        """Extract mixed roman+alpha like II.A."""
        result = extract_section_prefix("II.A Overview")
        assert result is not None
        assert result.components == ["II", "A"]
        assert result.styles == [NumberStyle.roman_upper, NumberStyle.alpha_upper]
        assert result.trailing == ""
        assert result.title == "Overview"

    def test_roman_lower_single(self) -> None:
        """Extract single roman lower."""
        result = extract_section_prefix("i. intro")
        assert result is not None
        assert result.components == ["i"]
        assert result.styles == [NumberStyle.roman_lower]
        assert result.trailing == "."
        assert result.title == "intro"

    def test_alpha_upper_single(self) -> None:
        """Extract single alpha upper."""
        result = extract_section_prefix("A. Introduction")
        assert result is not None
        assert result.components == ["A"]
        assert result.styles == [NumberStyle.alpha_upper]
        assert result.trailing == "."
        assert result.title == "Introduction"

    def test_alpha_arabic_mixed(self) -> None:
        """Extract mixed alpha+arabic like A.1."""
        result = extract_section_prefix("A.1 Details")
        assert result is not None
        assert result.components == ["A", "1"]
        assert result.styles == [NumberStyle.alpha_upper, NumberStyle.arabic]
        assert result.trailing == ""
        assert result.title == "Details"

    def test_alpha_lower_with_paren(self) -> None:
        """Extract alpha lower with paren."""
        result = extract_section_prefix("a) intro")
        assert result is not None
        assert result.components == ["a"]
        assert result.styles == [NumberStyle.alpha_lower]
        assert result.trailing == ")"
        assert result.title == "intro"

    def test_mixed_three_styles(self) -> None:
        """Extract mixed arabic+alpha+roman like 1.a.i."""
        result = extract_section_prefix("1.a.i Deep")
        assert result is not None
        assert result.components == ["1", "a", "i"]
        assert result.styles == [
            NumberStyle.arabic,
            NumberStyle.alpha_lower,
            NumberStyle.roman_lower,
        ]
        assert result.trailing == ""
        assert result.title == "Deep"

    def test_no_prefix(self) -> None:
        """Return None when no prefix."""
        result = extract_section_prefix("Background")
        assert result is None

    def test_number_not_at_start(self) -> None:
        """Return None when number not at start."""
        result = extract_section_prefix("The 1st Item")
        assert result is None

    def test_empty_title(self) -> None:
        """Handle empty title after prefix."""
        result = extract_section_prefix("1. ")
        # Could be None or empty title depending on implementation
        # Let's say we require a title
        assert result is None or result.title == ""


# === Phase 3: Convention Inference ===


class TestInferFormatForLevel:
    """Tests for infer_format_for_level function."""

    def test_first_two_arabic_qualifies(self) -> None:
        """First two headings with matching arabic prefix qualifies."""
        headings = [
            (1, "1. Intro"),
            (1, "2. Design"),
            (1, "3. Conclusion"),
        ]
        result = infer_format_for_level(headings, 1)
        assert result is not None
        assert result.format_string() == "{h1:arabic}."

    def test_first_two_not_both_numbered_fails(self) -> None:
        """First two must both be numbered to qualify."""
        headings = [
            (1, "1. Intro"),
            (1, "Background"),  # Not numbered
            (1, "3. Conclusion"),
        ]
        result = infer_format_for_level(headings, 1)
        assert result is None

    def test_first_not_numbered_fails(self) -> None:
        """If first heading not numbered, fails."""
        headings = [
            (1, "Intro"),
            (1, "2. Design"),
            (1, "3. Conclusion"),
        ]
        result = infer_format_for_level(headings, 1)
        assert result is None

    def test_only_one_heading_fails(self) -> None:
        """Need at least 2 headings to qualify."""
        headings = [
            (1, "1. Intro"),
        ]
        result = infer_format_for_level(headings, 1)
        assert result is None

    def test_two_thirds_66_percent_qualifies(self) -> None:
        """2/3 (66%) qualifies."""
        headings = [
            (1, "1. Intro"),
            (1, "2. Design"),
            (1, "Background"),  # Not numbered
        ]
        result = infer_format_for_level(headings, 1)
        assert result is not None

    def test_two_thirds_50_percent_fails(self) -> None:
        """2/4 (50%) does not qualify."""
        headings = [
            (1, "1. Intro"),
            (1, "2. Design"),
            (1, "Background"),
            (1, "Conclusion"),
        ]
        result = infer_format_for_level(headings, 1)
        assert result is None

    def test_two_thirds_75_percent_qualifies(self) -> None:
        """3/4 (75%) qualifies."""
        headings = [
            (1, "1. Intro"),
            (1, "2. Design"),
            (1, "3. Details"),
            (1, "Background"),
        ]
        result = infer_format_for_level(headings, 1)
        assert result is not None

    def test_two_thirds_4_of_6_qualifies(self) -> None:
        """4/6 (66%) qualifies."""
        headings = [
            (1, "1. A"),
            (1, "2. B"),
            (1, "3. C"),
            (1, "4. D"),
            (1, "E"),
            (1, "F"),
        ]
        result = infer_format_for_level(headings, 1)
        assert result is not None

    def test_two_thirds_3_of_6_fails(self) -> None:
        """3/6 (50%) does not qualify."""
        headings = [
            (1, "1. A"),
            (1, "2. B"),
            (1, "3. C"),
            (1, "D"),
            (1, "E"),
            (1, "F"),
        ]
        result = infer_format_for_level(headings, 1)
        assert result is None

    def test_different_structures_fails(self) -> None:
        """First two with different structures fails (e.g., [1] and [1,2])."""
        headings = [
            (1, "1. Intro"),
            (1, "1.2 Design"),  # Different structure
        ]
        result = infer_format_for_level(headings, 1)
        assert result is None

    def test_different_styles_fails(self) -> None:
        """First two with different styles fails (e.g., arabic and roman)."""
        headings = [
            (1, "1. Intro"),
            (1, "II. Design"),  # Different style
        ]
        result = infer_format_for_level(headings, 1)
        assert result is None

    def test_roman_upper_qualifies(self) -> None:
        """Roman uppercase headings qualify."""
        headings = [
            (1, "I. Intro"),
            (1, "II. Design"),
            (1, "III. Conclusion"),
        ]
        result = infer_format_for_level(headings, 1)
        assert result is not None
        assert result.format_string() == "{h1:roman_upper}."

    def test_alpha_upper_qualifies(self) -> None:
        """Alphabetic uppercase headings qualify."""
        headings = [
            (1, "A. Intro"),
            (1, "B. Design"),
            (1, "C. Conclusion"),
        ]
        result = infer_format_for_level(headings, 1)
        assert result is not None
        assert result.format_string() == "{h1:alpha_upper}."

    def test_h2_decimal_format(self) -> None:
        """H2 with decimal format (1.1, 1.2) infers correct format."""
        headings = [
            (2, "1.1 Background"),
            (2, "1.2 Motivation"),
            (2, "2.1 Architecture"),
        ]
        result = infer_format_for_level(headings, 2)
        assert result is not None
        assert result.format_string() == "{h1:arabic}.{h2:arabic}"

    def test_filters_by_level(self) -> None:
        """Only considers headings at the specified level."""
        headings = [
            (1, "1. Intro"),
            (2, "1.1 Background"),
            (1, "2. Design"),
            (2, "2.1 Architecture"),
        ]
        # H1 should qualify
        h1_result = infer_format_for_level(headings, 1)
        assert h1_result is not None
        assert h1_result.format_string() == "{h1:arabic}."

        # H2 should also qualify
        h2_result = infer_format_for_level(headings, 2)
        assert h2_result is not None
        assert h2_result.format_string() == "{h1:arabic}.{h2:arabic}"

    def test_roman_h1_alpha_h2(self) -> None:
        """Roman H1 + Alpha H2 format."""
        headings = [
            (2, "I.A Overview"),
            (2, "I.B Details"),
            (2, "II.A Summary"),
        ]
        result = infer_format_for_level(headings, 2)
        assert result is not None
        assert result.format_string() == "{h1:roman_upper}.{h2:alpha_upper}"


class TestLevelWideDisambiguation:
    """Tests for level-wide Roman vs Alpha disambiguation."""

    def test_pure_roman_stays_roman(self) -> None:
        """Pure Roman letters (I, V, X, C, D, M) are interpreted as Roman."""
        headings = [
            (1, "I. Intro"),
            (1, "II. Design"),
            (1, "III. More"),
            (1, "IV. End"),
        ]
        result = infer_format_for_level(headings, 1)
        assert result is not None
        # All are valid Roman → roman_upper
        assert result.format_string() == "{h1:roman_upper}."

    def test_mixed_roman_alpha_becomes_alpha(self) -> None:
        """If non-Roman letters exist, entire level is alpha."""
        headings = [
            (1, "A. Intro"),
            (1, "B. Design"),
            (1, "C. More"),  # C is Roman-only but...
            (1, "D. End"),  # D is Roman-only but A, B are not
        ]
        result = infer_format_for_level(headings, 1)
        assert result is not None
        # A and B are not Roman → entire level is alpha_upper
        assert result.format_string() == "{h1:alpha_upper}."

    def test_lowercase_mixed_becomes_alpha(self) -> None:
        """Lowercase with both Roman and non-Roman letters → alpha_lower."""
        headings = [
            (1, "a. first"),
            (1, "b. second"),
            (1, "c. third"),  # c is Roman-only
            (1, "d. fourth"),  # d is Roman-only but a, b exist
        ]
        result = infer_format_for_level(headings, 1)
        assert result is not None
        # a and b are not Roman → entire level is alpha_lower
        assert result.format_string() == "{h1:alpha_lower}."


class TestInferSectionConvention:
    """Tests for infer_section_convention function."""

    def test_h1_only_convention(self) -> None:
        """Infers H1-only convention."""
        headings = [
            (1, "1. Intro"),
            (1, "2. Design"),
            (1, "3. Conclusion"),
        ]
        conv = infer_section_convention(headings)
        assert conv.is_active
        assert conv.max_depth == 1
        assert conv.levels[0] is not None
        assert conv.levels[0].format_string() == "{h1:arabic}."
        assert conv.levels[1] is None

    def test_h1_h2_convention(self) -> None:
        """Infers H1+H2 convention."""
        headings = [
            (1, "1. Intro"),
            (2, "1.1 Background"),
            (2, "1.2 Motivation"),
            (1, "2. Design"),
            (2, "2.1 Architecture"),
        ]
        conv = infer_section_convention(headings)
        assert conv.is_active
        assert conv.max_depth == 2
        assert conv.levels[0] is not None
        assert conv.levels[1] is not None
        assert conv.levels[0].format_string() == "{h1:arabic}."
        assert conv.levels[1].format_string() == "{h1:arabic}.{h2:arabic}"

    def test_no_numbered_headings(self) -> None:
        """Returns inactive convention when no numbered headings."""
        headings = [
            (1, "Intro"),
            (1, "Design"),
            (2, "Background"),
        ]
        conv = infer_section_convention(headings)
        assert not conv.is_active
        assert conv.max_depth == 0

    def test_roman_h1_alpha_h2_convention(self) -> None:
        """Infers Roman H1 + Alpha H2 convention."""
        headings = [
            (1, "I. Chapter One"),
            (2, "I.A Overview"),
            (2, "I.B Details"),
            (1, "II. Chapter Two"),
            (2, "II.A Summary"),
            (2, "II.B Notes"),
        ]
        conv = infer_section_convention(headings)
        assert conv.is_active
        assert conv.max_depth == 2
        assert conv.levels[0] is not None
        assert conv.levels[1] is not None
        assert conv.levels[0].format_string() == "{h1:roman_upper}."
        # Note: H2s here have format like I.A where A, B are NOT Roman-only, so they stay alpha_upper
        assert conv.levels[1].format_string() == "{h1:roman_upper}.{h2:alpha_upper}"

    def test_convention_str_representation(self) -> None:
        """Convention has correct string representation."""
        headings = [
            (1, "1. Intro"),
            (2, "1.1 Background"),
            (2, "1.2 Motivation"),
            (1, "2. Design"),
            (2, "2.1 Architecture"),
        ]
        conv = infer_section_convention(headings)
        assert str(conv) == "H1: {h1:arabic}., H2: {h1:arabic}.{h2:arabic}"


# === Phase 4: Hierarchical Constraint ===


class TestApplyHierarchicalConstraint:
    """Tests for apply_hierarchical_constraint function."""

    def test_h1_h2_h3_unchanged(self) -> None:
        """Contiguous H1+H2+H3 is unchanged."""
        # Create a convention with H1, H2, H3
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        fmt3 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
                FormatComponent(level=3, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, fmt3, None, None, None))
        result = apply_hierarchical_constraint(conv)
        # Should be unchanged
        assert result.levels[0] is not None
        assert result.levels[1] is not None
        assert result.levels[2] is not None
        assert result.max_depth == 3

    def test_h1_h3_gap_at_h2(self) -> None:
        """H1+H3 with gap at H2 -> H3 becomes None."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        fmt3 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
                FormatComponent(level=3, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        conv = SectionNumConvention(levels=(fmt1, None, fmt3, None, None, None))
        result = apply_hierarchical_constraint(conv)
        # H1 should remain, H2 is None, H3 should become None
        assert result.levels[0] is not None
        assert result.levels[1] is None
        assert result.levels[2] is None
        assert result.max_depth == 1

    def test_h2_only_no_h1(self) -> None:
        """H2 only (no H1) -> all None."""
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        conv = SectionNumConvention(levels=(None, fmt2, None, None, None, None))
        result = apply_hierarchical_constraint(conv)
        # All should be None (H1 is required)
        assert result.levels[0] is None
        assert result.levels[1] is None
        assert result.max_depth == 0
        assert not result.is_active

    def test_h1_h2_h4_gap_at_h3(self) -> None:
        """H1+H2+H4 with gap at H3 -> H4 becomes None."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        fmt4 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
                FormatComponent(level=3, style=NumberStyle.arabic),
                FormatComponent(level=4, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, None, fmt4, None, None))
        result = apply_hierarchical_constraint(conv)
        # H1, H2 should remain, H3 is None, H4+ should become None
        assert result.levels[0] is not None
        assert result.levels[1] is not None
        assert result.levels[2] is None
        assert result.levels[3] is None
        assert result.max_depth == 2

    def test_h1_only_is_valid(self) -> None:
        """H1 only is a valid convention."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        conv = SectionNumConvention(levels=(fmt1, None, None, None, None, None))
        result = apply_hierarchical_constraint(conv)
        assert result.levels[0] is not None
        assert result.max_depth == 1
        assert result.is_active

    def test_all_none_stays_none(self) -> None:
        """All None stays all None."""
        conv = SectionNumConvention(levels=(None, None, None, None, None, None))
        result = apply_hierarchical_constraint(conv)
        assert result.max_depth == 0
        assert not result.is_active


# === Phase 5: Normalization ===


class TestNormalizeConvention:
    """Tests for normalize_convention function."""

    def test_paren_to_period(self) -> None:
        """Trailing ')' is normalized to '.'."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=")",
        )
        conv = SectionNumConvention(levels=(fmt, None, None, None, None, None))
        result = normalize_convention(conv)
        assert result.levels[0] is not None
        assert result.levels[0].trailing == "."

    def test_empty_to_period_for_h1(self) -> None:
        """Empty trailing for H1 is normalized to '.'."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing="",
        )
        conv = SectionNumConvention(levels=(fmt, None, None, None, None, None))
        result = normalize_convention(conv)
        assert result.levels[0] is not None
        assert result.levels[0].trailing == "."

    def test_h2_decimal_stays_empty(self) -> None:
        """H2 decimal format stays empty (no trailing period)."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing="",  # No trailing for decimal formats
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, None, None, None, None))
        result = normalize_convention(conv)
        assert result.levels[0] is not None
        assert result.levels[1] is not None
        # H1 should have trailing period
        assert result.levels[0].trailing == "."
        # H2 should have no trailing (decimal format)
        assert result.levels[1].trailing == ""

    def test_h2_paren_becomes_empty(self) -> None:
        """H2 with paren trailing becomes empty (not period)."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing=")",  # Paren should be removed for decimals
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, None, None, None, None))
        result = normalize_convention(conv)
        assert result.levels[1] is not None
        # H2 decimal should have no trailing
        assert result.levels[1].trailing == ""

    def test_mixed_separators_normalized(self) -> None:
        """Mixed separators are all normalized."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=")",  # paren -> period
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing=")",  # paren -> empty for decimal
        )
        fmt3 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
                FormatComponent(level=3, style=NumberStyle.arabic),
            ],
            trailing=".",  # period -> empty for decimal
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, fmt3, None, None, None))
        result = normalize_convention(conv)
        assert result.levels[0] is not None
        assert result.levels[1] is not None
        assert result.levels[2] is not None
        assert result.levels[0].trailing == "."
        assert result.levels[1].trailing == ""
        assert result.levels[2].trailing == ""

    def test_already_normalized_unchanged(self) -> None:
        """Already normalized convention is unchanged."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, None, None, None, None))
        result = normalize_convention(conv)
        assert result.levels[0] is not None
        assert result.levels[1] is not None
        assert result.levels[0].trailing == "."
        assert result.levels[1].trailing == ""

    def test_none_levels_skipped(self) -> None:
        """None levels are preserved as None."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=")",
        )
        conv = SectionNumConvention(levels=(fmt1, None, None, None, None, None))
        result = normalize_convention(conv)
        assert result.levels[0] is not None
        assert result.levels[1] is None
        assert result.levels[2] is None


# === Phase 6: Renumbering Logic ===


class TestSectionRenumbererArabic:
    """Tests for SectionRenumberer with Arabic numbers."""

    def test_h1_sequential(self) -> None:
        """H1 increments sequentially."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        conv = SectionNumConvention(levels=(fmt, None, None, None, None, None))
        renumberer = SectionRenumberer(conv)
        assert renumberer.next_number(1) == "1."
        assert renumberer.next_number(1) == "2."
        assert renumberer.next_number(1) == "3."

    def test_h1_h2_nested(self) -> None:
        """H1 and H2 work together."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, None, None, None, None))
        renumberer = SectionRenumberer(conv)
        assert renumberer.next_number(1) == "1."
        assert renumberer.next_number(2) == "1.1"
        assert renumberer.next_number(2) == "1.2"
        assert renumberer.next_number(1) == "2."
        assert renumberer.next_number(2) == "2.1"

    def test_h1_h2_h3_nested(self) -> None:
        """Three levels work together."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        fmt3 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
                FormatComponent(level=3, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, fmt3, None, None, None))
        renumberer = SectionRenumberer(conv)
        assert renumberer.next_number(1) == "1."
        assert renumberer.next_number(2) == "1.1"
        assert renumberer.next_number(3) == "1.1.1"
        assert renumberer.next_number(3) == "1.1.2"
        assert renumberer.next_number(2) == "1.2"
        assert renumberer.next_number(3) == "1.2.1"

    def test_deeper_levels_reset_on_shallower(self) -> None:
        """Deeper level counters reset when shallower level increments."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, None, None, None, None))
        renumberer = SectionRenumberer(conv)
        assert renumberer.next_number(1) == "1."
        assert renumberer.next_number(2) == "1.1"
        assert renumberer.next_number(2) == "1.2"
        assert renumberer.next_number(2) == "1.3"
        assert renumberer.next_number(1) == "2."  # H2 counter should reset
        assert renumberer.next_number(2) == "2.1"  # Back to 1, not 4


class TestSectionRenumbererRoman:
    """Tests for SectionRenumberer with Roman numbers."""

    def test_roman_h1_sequential(self) -> None:
        """Roman H1 increments sequentially."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.roman_upper)],
            trailing=".",
        )
        conv = SectionNumConvention(levels=(fmt, None, None, None, None, None))
        renumberer = SectionRenumberer(conv)
        assert renumberer.next_number(1) == "I."
        assert renumberer.next_number(1) == "II."
        assert renumberer.next_number(1) == "III."
        assert renumberer.next_number(1) == "IV."

    def test_roman_h1_alpha_h2(self) -> None:
        """Roman H1 + Alpha H2 work together."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.roman_upper)],
            trailing=".",
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.roman_upper),
                FormatComponent(level=2, style=NumberStyle.alpha_upper),
            ],
            trailing="",
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, None, None, None, None))
        renumberer = SectionRenumberer(conv)
        assert renumberer.next_number(1) == "I."
        assert renumberer.next_number(2) == "I.A"
        assert renumberer.next_number(2) == "I.B"
        assert renumberer.next_number(1) == "II."
        assert renumberer.next_number(2) == "II.A"


class TestSectionRenumbererMixed:
    """Tests for SectionRenumberer with mixed styles."""

    def test_arabic_alpha_roman_three_levels(self) -> None:
        """Arabic H1, alpha H2, roman H3 work together."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.alpha_lower),
            ],
            trailing="",
        )
        fmt3 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.alpha_lower),
                FormatComponent(level=3, style=NumberStyle.roman_lower),
            ],
            trailing="",
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, fmt3, None, None, None))
        renumberer = SectionRenumberer(conv)
        assert renumberer.next_number(1) == "1."
        assert renumberer.next_number(2) == "1.a"
        assert renumberer.next_number(3) == "1.a.i"
        assert renumberer.next_number(3) == "1.a.ii"
        assert renumberer.next_number(2) == "1.b"
        assert renumberer.next_number(3) == "1.b.i"


class TestSectionRenumbererFormatHeading:
    """Tests for SectionRenumberer.format_heading method."""

    def test_format_h1_heading(self) -> None:
        """format_heading creates correct H1 heading."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        conv = SectionNumConvention(levels=(fmt, None, None, None, None, None))
        renumberer = SectionRenumberer(conv)
        assert renumberer.format_heading(1, "Introduction") == "1. Introduction"
        assert renumberer.format_heading(1, "Design") == "2. Design"

    def test_format_h2_heading(self) -> None:
        """format_heading creates correct H2 heading."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        fmt2 = SectionNumFormat(
            components=[
                FormatComponent(level=1, style=NumberStyle.arabic),
                FormatComponent(level=2, style=NumberStyle.arabic),
            ],
            trailing="",
        )
        conv = SectionNumConvention(levels=(fmt1, fmt2, None, None, None, None))
        renumberer = SectionRenumberer(conv)
        assert renumberer.format_heading(1, "First") == "1. First"
        assert renumberer.format_heading(2, "Details") == "1.1 Details"
        assert renumberer.format_heading(2, "More") == "1.2 More"

    def test_format_roman_heading(self) -> None:
        """format_heading works with Roman numerals."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.roman_upper)],
            trailing=".",
        )
        conv = SectionNumConvention(levels=(fmt, None, None, None, None, None))
        renumberer = SectionRenumberer(conv)
        assert renumberer.format_heading(1, "Chapter") == "I. Chapter"
        assert renumberer.format_heading(1, "Chapter Two") == "II. Chapter Two"

    def test_format_unnumbered_level(self) -> None:
        """format_heading returns title only for unnumbered level."""
        fmt1 = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        conv = SectionNumConvention(levels=(fmt1, None, None, None, None, None))
        renumberer = SectionRenumberer(conv)
        renumberer.next_number(1)  # Advance H1 counter
        # H2 is not numbered, should return title only
        assert renumberer.format_heading(2, "Background") == "Background"


# === Phase 7: Integration with fill_markdown ===


class TestRenumberHeadingsHighLevel:
    """Tests for renumber_headings top-level function."""

    def test_simple_h1_renumber(self) -> None:
        """Simple H1 renumbering."""
        headings = [
            (1, "1. Intro"),
            (1, "3. Middle"),
            (1, "2. End"),
        ]
        result = renumber_headings(headings)
        assert result == [
            (1, "1. Intro"),
            (1, "2. Middle"),
            (1, "3. End"),
        ]

    def test_nested_h1_h2_renumber(self) -> None:
        """Nested H1+H2 renumbering."""
        headings = [
            (1, "1. First"),
            (2, "1.1 Sub A"),
            (2, "1.3 Sub B"),
            (1, "3. Second"),
            (2, "3.1 Sub C"),
        ]
        result = renumber_headings(headings)
        assert result == [
            (1, "1. First"),
            (2, "1.1 Sub A"),
            (2, "1.2 Sub B"),
            (1, "2. Second"),
            (2, "2.1 Sub C"),
        ]

    def test_unnumbered_passes_through(self) -> None:
        """Unnumbered headings pass through unchanged."""
        headings = [
            (1, "1. Intro"),
            (1, "2. Design"),
            (1, "Background"),  # Unnumbered
        ]
        result = renumber_headings(headings)
        assert result == [
            (1, "1. Intro"),
            (1, "2. Design"),
            (1, "Background"),  # Unchanged
        ]

    def test_no_numbered_headings(self) -> None:
        """Document with no numbered headings passes through unchanged."""
        headings = [
            (1, "Intro"),
            (1, "Design"),
            (2, "Background"),
        ]
        result = renumber_headings(headings)
        assert result == headings  # Unchanged

    def test_separator_normalization(self) -> None:
        """Separators are normalized to period."""
        headings = [
            (1, "1) Intro"),
            (1, "3) End"),
        ]
        result = renumber_headings(headings)
        assert result == [
            (1, "1. Intro"),
            (1, "2. End"),
        ]

    def test_roman_numerals(self) -> None:
        """Roman numeral renumbering."""
        headings = [
            (1, "I. Introduction"),
            (1, "III. Middle"),
            (1, "II. End"),
        ]
        result = renumber_headings(headings)
        assert result == [
            (1, "I. Introduction"),
            (1, "II. Middle"),
            (1, "III. End"),
        ]

    def test_roman_h1_alpha_h2(self) -> None:
        """Roman H1 + Alpha H2 renumbering."""
        headings = [
            (1, "I. Chapter One"),
            (2, "I.A Overview"),
            (2, "I.C Details"),
            (1, "III. Chapter Two"),
            (2, "III.A Summary"),
        ]
        result = renumber_headings(headings)
        assert result == [
            (1, "I. Chapter One"),
            (2, "I.A Overview"),
            (2, "I.B Details"),
            (1, "II. Chapter Two"),
            (2, "II.A Summary"),
        ]

    def test_below_two_thirds_threshold(self) -> None:
        """Below 2/3 threshold does not renumber."""
        headings = [
            (1, "1. Intro"),
            (1, "2. Design"),
            (1, "Background"),
            (1, "Conclusion"),  # 2/4 = 50% < 66%
        ]
        result = renumber_headings(headings)
        # First-two passes but 2/3 fails - no renumbering
        assert result == headings

    def test_h2_below_threshold_h1_renumbered(self) -> None:
        """H1 renumbered but H2 below threshold stays unchanged."""
        headings = [
            (1, "1. Intro"),  # index 0
            (2, "1.1 Sub A"),  # index 1
            (2, "Background"),  # index 2
            (2, "Details"),  # index 3
            (1, "3. Design"),  # index 4
            (2, "3.1 Arch"),  # index 5
            (2, "Overview"),  # index 6
            (2, "Notes"),  # index 7
        ]
        # H1s: 2/2 numbered → renumbered
        # H2s: 2/6 numbered (33%) → NOT renumbered (below threshold)
        result = renumber_headings(headings)
        # H1 gets renumbered (3 -> 2)
        # H2s pass through unchanged (below threshold)
        assert result[0] == (1, "1. Intro")
        assert result[4] == (1, "2. Design")  # Was "3. Design", at index 4
        # H2s unchanged because below threshold
        assert result[1] == (2, "1.1 Sub A")  # Original preserved
        assert result[5] == (2, "3.1 Arch")  # Original preserved


class TestFillMarkdownIntegration:
    """Integration tests for fill_markdown with renumber_sections."""

    def test_simple_renumber_via_fill_markdown(self) -> None:
        """Basic renumbering via fill_markdown."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# 1. Intro

Some text.

# 3. Middle

More text.

# 2. End

Final text.
"""
        result = fill_markdown(input_text, renumber_sections=True)
        assert "# 1. Intro" in result
        assert "# 2. Middle" in result
        assert "# 3. End" in result
        # The old numbers should be replaced
        assert "# 3. Middle" not in result
        assert "# 2. End" not in result

    def test_nested_renumber_via_fill_markdown(self) -> None:
        """Nested H1+H2 renumbering via fill_markdown."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# 1. First

## 1.1 Sub A

## 1.3 Sub B

# 3. Second

## 3.1 Sub C
"""
        result = fill_markdown(input_text, renumber_sections=True)
        assert "# 1. First" in result
        assert "## 1.1 Sub A" in result
        assert "## 1.2 Sub B" in result  # Was 1.3
        assert "# 2. Second" in result  # Was 3
        assert "## 2.1 Sub C" in result  # Was 3.1

    def test_no_renumber_when_disabled(self) -> None:
        """No renumbering when renumber_sections=False."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# 1. Intro

# 3. Middle

# 2. End
"""
        result = fill_markdown(input_text, renumber_sections=False)
        # Numbers should be preserved as-is
        assert "# 1. Intro" in result
        assert "# 3. Middle" in result
        assert "# 2. End" in result


# === Phase 9: End-to-End Tests from Spec ===


class TestEndToEndFromSpec:
    """End-to-end tests from the spec document."""

    def test_first_two_and_two_thirds_qualifies(self) -> None:
        """First two numbered, 2/3 total → qualifies."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# 1. Intro

# 2. Design

# Background
"""
        result = fill_markdown(input_text, renumber_sections=True)
        # First two H1s numbered ✓, 2/3 total ✓ → H1 qualifies
        assert "# 1. Intro" in result
        assert "# 2. Design" in result
        assert "# Background" in result

    def test_first_two_fails(self) -> None:
        """First two not both numbered → does NOT qualify."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# 1. Intro

# Background

# 3. Conclusion
"""
        result = fill_markdown(input_text, renumber_sections=True)
        # First two H1s: only first is numbered → first-two fails
        # Document left unchanged
        assert "# 1. Intro" in result
        assert "# Background" in result
        assert "# 3. Conclusion" in result

    def test_two_thirds_fails(self) -> None:
        """First two numbered, but only 2/4 total → does NOT qualify."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# 1. Intro

# 2. Design

# Background

# Conclusion
"""
        result = fill_markdown(input_text, renumber_sections=True)
        # First two H1s numbered ✓, but only 2/4 = 50% < 66% → 2/3 fails
        # Document left unchanged
        assert "# 1. Intro" in result
        assert "# 2. Design" in result
        assert "# Background" in result
        assert "# Conclusion" in result

    def test_first_two_and_two_thirds_renumbers(self) -> None:
        """First two numbered, 3/4 total → qualifies and renumbers."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# 1. Intro

# 3. Design

# Background

# 5. Conclusion
"""
        result = fill_markdown(input_text, renumber_sections=True)
        # First two H1s numbered ✓, 3/4 = 75% ✓ → H1 qualifies, renumbered
        # Unnumbered H1 ("Background") passes through unchanged
        assert "# 1. Intro" in result
        assert "# 2. Design" in result  # Was 3
        assert "# Background" in result
        assert "# 3. Conclusion" in result  # Was 5

    def test_h1_numbered_h2_not(self) -> None:
        """H1 numbered, H2 not numbered."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# 1. Intro

## Background

## Details

# 3. Conclusion

## Summary
"""
        result = fill_markdown(input_text, renumber_sections=True)
        # Only H1s are renumbered; H2s have no numbers so they stay as-is
        assert "# 1. Intro" in result
        assert "## Background" in result
        assert "## Details" in result
        assert "# 2. Conclusion" in result  # Was 3
        assert "## Summary" in result

    def test_separator_normalized_to_period(self) -> None:
        """Separator normalization - always use period."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# 1) Intro

# 3) End
"""
        result = fill_markdown(input_text, renumber_sections=True)
        # Parenthesis separator normalized to period
        assert "# 1. Intro" in result
        assert "# 2. End" in result

    def test_three_level_numbering(self) -> None:
        """Three-level numbering."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# 1. First

## 1.1 Sub A

### 1.1.1 Detail X

### 1.1.3 Detail Y

## 1.2 Sub B

# 2. Second
"""
        result = fill_markdown(input_text, renumber_sections=True)
        assert "# 1. First" in result
        assert "## 1.1 Sub A" in result
        assert "### 1.1.1 Detail X" in result
        assert "### 1.1.2 Detail Y" in result  # Was 1.1.3
        assert "## 1.2 Sub B" in result
        assert "# 2. Second" in result

    def test_decimal_without_period(self) -> None:
        """Decimal without trailing period normalized."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# 1 Intro

## 1.1 Details

# 2 Conclusion
"""
        result = fill_markdown(input_text, renumber_sections=True)
        # Missing periods are added
        assert "# 1. Intro" in result
        assert "## 1.1 Details" in result
        assert "# 2. Conclusion" in result

    def test_roman_numeral_renumber(self) -> None:
        """Roman numeral renumbering."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# I. Introduction

# III. Middle

# II. End
"""
        result = fill_markdown(input_text, renumber_sections=True)
        # Roman numerals renumbered sequentially
        assert "# I. Introduction" in result
        assert "# II. Middle" in result  # Was III
        assert "# III. End" in result  # Was II

    def test_roman_h1_alpha_h2(self) -> None:
        """Roman H1 with alphabetic H2."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# I. Chapter One

## I.A Overview

## I.C Details

# III. Chapter Two

## III.A Summary
"""
        result = fill_markdown(input_text, renumber_sections=True)
        # Roman H1 + Alpha H2, both renumbered
        assert "# I. Chapter One" in result
        assert "## I.A Overview" in result
        assert "## I.B Details" in result  # Was I.C
        assert "# II. Chapter Two" in result  # Was III
        assert "## II.A Summary" in result  # Was III.A

    def test_mixed_styles_three_levels(self) -> None:
        """Mixed styles: Arabic H1, alpha_lower H2, roman_lower H3."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# 1. First

## 1.a Sub A

### 1.a.i Detail X

### 1.a.iii Detail Y

## 1.b Sub B

# 3. Second
"""
        result = fill_markdown(input_text, renumber_sections=True)
        assert "# 1. First" in result
        assert "## 1.a Sub A" in result
        assert "### 1.a.i Detail X" in result
        assert "### 1.a.ii Detail Y" in result  # Was 1.a.iii
        assert "## 1.b Sub B" in result
        assert "# 2. Second" in result  # Was 3

    def test_lowercase_roman(self) -> None:
        """Lowercase Roman numerals."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# i. first

# iii. second

# ii. third
"""
        result = fill_markdown(input_text, renumber_sections=True)
        assert "# i. first" in result
        assert "# ii. second" in result  # Was iii
        assert "# iii. third" in result  # Was ii

    def test_alpha_uppercase_only(self) -> None:
        """Alphabetic only (uppercase)."""
        from flowmark.linewrapping.markdown_filling import fill_markdown

        input_text = """\
# A. Introduction

# C. Middle

# B. Conclusion
"""
        result = fill_markdown(input_text, renumber_sections=True)
        assert "# A. Introduction" in result
        assert "# B. Middle" in result  # Was C
        assert "# C. Conclusion" in result  # Was B
