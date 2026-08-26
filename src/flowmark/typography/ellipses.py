import re
from re import Pattern

ELLIPSIS_PATTERN: Pattern[str] = re.compile(
    r"(^|[\w\"\'“”‘’])(\s*)(\.\.\.)([.,:;?!)\-—\"\'”’]?)(\s*)",
    re.MULTILINE,
)
ELLIPSIS_FOLLOW_BOUNDARY_PATTERN: Pattern[str] = re.compile(r"[\w,:;?!)\-—\"'”’>]")


def ellipses(text: str) -> str:
    r"""
    Replace three consecutive dots with a proper ellipsis character (…).

    Rules:
    - `...` must be preceded by start of line OR a word character (with optional space)
    - `...` must be followed by word character (with optional space) OR punctuation OR end of line
    - If immediately before the `...` is a word character (no whitespace), a space is inserted before it.
    - If immediately after the `...` is a word character (no whitespace), a space is inserted after it.
    - If quote punctuation immediately precedes the ellipsis, there is no space between the
      punctuation and the ellipsis.
    - If punctuation [.,:;?!)\-—] follows the ellipsis, there is no space between the ellipsis and
      the punctuation.
    """

    def replace_match(match: re.Match[str]) -> str:
        prefix = match.group(1)
        spaces_before = match.group(2)
        punct = match.group(4)
        spaces_after = match.group(5)

        # Get what follows the match
        end_pos = match.end()
        remaining = text[end_pos:] if end_pos < len(text) else ""
        next_char = remaining[0] if remaining else ""

        # Check boundary: allow prose or punctuation, but not a longer dot run.
        if remaining and not ELLIPSIS_FOLLOW_BOUNDARY_PATTERN.match(next_char):
            return match.group(0)

        result = prefix

        # Add space before ellipsis if word char with no existing space
        if prefix and re.match(r"\w", prefix) and not spaces_before:
            result += " "
        else:
            result += spaces_before

        result += "…" + punct

        # Add space after ellipsis if word char follows with no space and no punct
        if next_char and re.match(r"\w", next_char) and not spaces_after and not punct:
            result += " "
        else:
            result += spaces_after

        return result

    return ELLIPSIS_PATTERN.sub(replace_match, text)
