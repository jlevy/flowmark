"""Tests for section numbering detection and renumbering."""

from flowmark.transforms.section_numbering import (
    FormatComponent,
    NumberStyle,
    SectionNumConvention,
    SectionNumFormat,
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
