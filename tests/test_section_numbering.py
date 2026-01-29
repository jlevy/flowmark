"""Tests for section numbering detection and renumbering."""

from flowmark.transforms.section_numbering import (
    FormatComponent,
    NumberStyle,
    SectionNumConvention,
    SectionNumFormat,
    alpha_to_int,
    extract_section_prefix,
    infer_style,
    int_to_alpha,
    int_to_roman,
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
        conv = SectionNumConvention(
            levels=(None, None, None, None, None, None)
        )
        assert conv.max_depth == 0

    def test_max_depth_h1_only(self) -> None:
        """max_depth returns 1 when only H1 is numbered."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        conv = SectionNumConvention(
            levels=(fmt, None, None, None, None, None)
        )
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
        conv = SectionNumConvention(
            levels=(fmt1, fmt2, None, None, None, None)
        )
        assert conv.max_depth == 2

    def test_is_active_false_when_no_levels(self) -> None:
        """is_active returns False when no levels are numbered."""
        conv = SectionNumConvention(
            levels=(None, None, None, None, None, None)
        )
        assert conv.is_active is False

    def test_is_active_true_when_h1_numbered(self) -> None:
        """is_active returns True when H1 is numbered."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        conv = SectionNumConvention(
            levels=(fmt, None, None, None, None, None)
        )
        assert conv.is_active is True

    def test_str_none(self) -> None:
        """__str__ returns 'none' when no levels are numbered."""
        conv = SectionNumConvention(
            levels=(None, None, None, None, None, None)
        )
        assert str(conv) == "none"

    def test_str_h1_only(self) -> None:
        """__str__ returns H1 format when only H1 is numbered."""
        fmt = SectionNumFormat(
            components=[FormatComponent(level=1, style=NumberStyle.arabic)],
            trailing=".",
        )
        conv = SectionNumConvention(
            levels=(fmt, None, None, None, None, None)
        )
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
        conv = SectionNumConvention(
            levels=(fmt1, fmt2, None, None, None, None)
        )
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
        assert result.styles == [NumberStyle.arabic, NumberStyle.alpha_lower, NumberStyle.roman_lower]
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
