"""Portable pre-parse scanner for source-exact protected regions."""

from __future__ import annotations

import re
from enum import Enum, auto

from flowmark.preservation.model import (
    Candidate,
    InvalidRegionError,
    NormalizedSource,
    ProtectedRegion,
    RegionForm,
    RegionKind,
    validate_regions,
)
from flowmark.preservation.registry import RECOGNIZER_BY_KIND

ByteRange = tuple[int, int]
ScalarRun = tuple[int, int]

_MYST_ROLE = "{math}"
_BEGIN_PREFIX = "\\begin{"
_END_PREFIX = "\\end{"
_TABLE_DELIMITER_CELL = re.compile(r":?-{3,}:?\Z")
_ATX_HEADING = re.compile(r" {0,3}#{1,6}(?:[ \t]+|$)")


class _DollarState(Enum):
    none = auto()
    single = auto()
    double = auto()


def escape_is_even(text: str, position: int) -> bool:
    """Return whether the backslash run before `position` has even length."""
    if position < 0 or position > len(text):
        raise InvalidRegionError("escape position is outside its text")
    preceding = position - 1
    count = 0
    while preceding >= 0 and text[preceding] == "\\":
        count += 1
        preceding -= 1
    return count % 2 == 0


def _scope_scalar_indexes(source: NormalizedSource, start: int, end: int) -> tuple[int, int]:
    start_index = source.scalar_index(start)
    end_index = source.scalar_index(end)
    if start_index >= end_index:
        raise InvalidRegionError("inline scope start must be before its end")
    return start_index, end_index


def _candidate(
    source: NormalizedSource,
    kind: RegionKind,
    start_index: int,
    end_index: int,
) -> Candidate:
    return Candidate(
        kind=kind,
        form=RegionForm.inline,
        start=source.byte_offset(start_index),
        end=source.byte_offset(end_index),
    )


def _active_dollar_runs(text: str, start: int, end: int) -> tuple[ScalarRun, ...]:
    runs: list[ScalarRun] = []
    index = start
    while index < end:
        if text[index] != "$" or not escape_is_even(text, index):
            index += 1
            continue
        run_start = index
        index += 1
        while index < end and text[index] == "$":
            index += 1
        runs.append((run_start, index))
    return tuple(runs)


def scan_dollar_runs(source: NormalizedSource, start: int, end: int) -> tuple[Candidate, ...]:
    """Scan the normative single/double-dollar state machine in one scope."""
    start_index, end_index = _scope_scalar_indexes(source, start, end)
    candidates: list[Candidate] = []
    state = _DollarState.none
    single_start: int | None = None
    double_start: int | None = None
    fallback_start: int | None = None

    for run_start, run_end in _active_dollar_runs(source.text, start_index, end_index):
        position = run_start
        while position < run_end:
            remaining = run_end - position
            if state is _DollarState.none:
                if remaining >= 2:
                    state = _DollarState.double
                    double_start = position
                    fallback_start = None
                    position += 2
                else:
                    state = _DollarState.single
                    single_start = position
                    position += 1
                continue

            if state is _DollarState.single:
                if single_start is None:
                    raise InvalidRegionError("single-dollar scanner lost its opener")
                candidates.append(
                    _candidate(
                        source,
                        RegionKind.math_dollar_inline,
                        single_start,
                        position + 1,
                    )
                )
                state = _DollarState.none
                single_start = None
                position += 1
                continue

            if remaining >= 2:
                if double_start is None:
                    raise InvalidRegionError("double-dollar scanner lost its opener")
                candidates.append(
                    _candidate(
                        source,
                        RegionKind.math_double_dollar_inline,
                        double_start,
                        position + 2,
                    )
                )
                state = _DollarState.none
                double_start = None
                fallback_start = None
                position += 2
            else:
                if fallback_start is None:
                    fallback_start = position
                else:
                    candidates.append(
                        _candidate(
                            source,
                            RegionKind.math_dollar_inline,
                            fallback_start,
                            position + 1,
                        )
                    )
                    fallback_start = None
                position += 1

    return tuple(candidates)


def _backtick_runs(text: str, start: int, end: int) -> tuple[ScalarRun, ...]:
    runs: list[ScalarRun] = []
    index = start
    while index < end:
        if text[index] != "`":
            index += 1
            continue
        run_start = index
        index += 1
        while index < end and text[index] == "`":
            index += 1
        runs.append((run_start, index))
    return tuple(runs)


def scan_backtick_runs(source: NormalizedSource, start: int, end: int) -> tuple[Candidate, ...]:
    """Pair general code spans by exact delimiter-run length."""
    start_index, end_index = _scope_scalar_indexes(source, start, end)
    pending: dict[int, int] = {}
    candidates: list[Candidate] = []
    for run_start, run_end in _backtick_runs(source.text, start_index, end_index):
        run_length = run_end - run_start
        opener = pending.pop(run_length, None)
        if opener is None:
            pending[run_length] = run_start
        else:
            candidates.append(_candidate(source, RegionKind.code_span, opener, run_end))
    return tuple(candidates)


def scan_composite_math(source: NormalizedSource, start: int, end: int) -> tuple[Candidate, ...]:
    """Scan GitLab dollar-backtick and MyST role-backtick math."""
    start_index, end_index = _scope_scalar_indexes(source, start, end)
    gitlab_pending: dict[int, int] = {}
    myst_pending: dict[int, int] = {}
    candidates: list[Candidate] = []
    text = source.text

    for run_start, run_end in _backtick_runs(text, start_index, end_index):
        run_length = run_end - run_start

        gitlab_opener = gitlab_pending.get(run_length)
        closes_gitlab = (
            run_end < end_index and text[run_end] == "$" and escape_is_even(text, run_end)
        )
        if gitlab_opener is not None and closes_gitlab:
            candidates.append(
                _candidate(
                    source,
                    RegionKind.math_gitlab_inline,
                    gitlab_opener,
                    run_end + 1,
                )
            )
            del gitlab_pending[run_length]
        elif (
            run_start > start_index
            and text[run_start - 1] == "$"
            and escape_is_even(text, run_start - 1)
            and run_length not in gitlab_pending
        ):
            gitlab_pending[run_length] = run_start - 1

        myst_opener = myst_pending.pop(run_length, None)
        if myst_opener is not None:
            candidates.append(_candidate(source, RegionKind.math_myst_inline, myst_opener, run_end))
        else:
            role_start = run_start - len(_MYST_ROLE)
            if role_start >= start_index and text[role_start:run_start] == _MYST_ROLE:
                myst_pending[run_length] = role_start

    return tuple(candidates)


def scan_paren_math(source: NormalizedSource, start: int, end: int) -> tuple[Candidate, ...]:
    """Pair active LaTeX parenthesis delimiters within one inline scope."""
    start_index, end_index = _scope_scalar_indexes(source, start, end)
    text = source.text
    opener: int | None = None
    candidates: list[Candidate] = []
    index = start_index
    while index + 1 < end_index:
        delimiter = text[index : index + 2]
        if delimiter == "\\(" and escape_is_even(text, index):
            if opener is None:
                opener = index
            index += 2
            continue
        if delimiter == "\\)" and escape_is_even(text, index):
            if opener is not None:
                candidates.append(
                    _candidate(source, RegionKind.math_paren_inline, opener, index + 2)
                )
                opener = None
            index += 2
            continue
        index += 1
    return tuple(candidates)


def _environment_event(text: str, index: int, end: int) -> tuple[tuple[str, str, int] | None, int]:
    command = ""
    name_start = index
    if text.startswith(_BEGIN_PREFIX, index, end):
        command = "begin"
        name_start = index + len(_BEGIN_PREFIX)
    elif text.startswith(_END_PREFIX, index, end):
        command = "end"
        name_start = index + len(_END_PREFIX)
    else:
        return None, index + 1
    if not escape_is_even(text, index):
        return None, index + 1

    cursor = name_start
    while cursor < end and text[cursor] not in "{}\n":
        cursor += 1
    if cursor >= end or text[cursor] != "}" or cursor == name_start:
        if cursor < end and text[cursor] == "{":
            for prefix in (_BEGIN_PREFIX, _END_PREFIX):
                nested_start = cursor - len(prefix) + 1
                if (
                    nested_start > index
                    and text.startswith(prefix, nested_start, end)
                    and escape_is_even(text, nested_start)
                ):
                    # The nested opener's brace proves the outer lexical event invalid.
                    # Revisit only this fixed-size prefix so malformed nesting stays
                    # linear without suppressing a valid inner environment.
                    return None, nested_start
        return None, min(cursor + 1, end)
    event_end = cursor + 1
    return (command, text[name_start:cursor], event_end), event_end


def scan_inline_environments(
    source: NormalizedSource, start: int, end: int
) -> tuple[Candidate, ...]:
    """Scan exact, case-sensitive nested LaTeX environments in one scope."""
    start_index, end_index = _scope_scalar_indexes(source, start, end)
    stack: list[tuple[str, int]] = []
    candidates: list[Candidate] = []
    index = start_index
    while index < end_index:
        if source.text[index] != "\\":
            index += 1
            continue
        event, next_index = _environment_event(source.text, index, end_index)
        if event is None:
            index = next_index
            continue
        command, name, event_end = event
        if command == "begin":
            stack.append((name, index))
        elif stack and stack[-1][0] == name:
            _, opener = stack.pop()
            candidates.append(
                _candidate(
                    source,
                    RegionKind.math_environment_inline,
                    opener,
                    event_end,
                )
            )
        index = event_end
    return tuple(candidates)


def arbitrate_candidates(candidates: tuple[Candidate, ...]) -> tuple[Candidate, ...]:
    """Select the earliest, highest-priority, longest non-overlapping candidates."""
    ordered = sorted(
        candidates,
        key=lambda candidate: (
            candidate.start,
            RECOGNIZER_BY_KIND[candidate.kind].priority,
            -(candidate.end - candidate.start),
            candidate.kind.value,
        ),
    )
    selected: list[Candidate] = []
    previous_end = 0
    for candidate in ordered:
        if selected and candidate.start < previous_end:
            continue
        selected.append(candidate)
        previous_end = candidate.end
    return tuple(selected)


def scan_inline_scope(source: NormalizedSource, start: int, end: int) -> tuple[Candidate, ...]:
    """Propose and arbitrate every built-in inline recognizer in one scope."""
    candidates = (
        *scan_composite_math(source, start, end),
        *scan_backtick_runs(source, start, end),
        *scan_paren_math(source, start, end),
        *scan_inline_environments(source, start, end),
        *scan_dollar_runs(source, start, end),
    )
    return arbitrate_candidates(candidates)


def _line_scalar_ranges(text: str) -> tuple[ScalarRun, ...]:
    ranges: list[ScalarRun] = []
    start = 0
    for line in text.splitlines(keepends=True):
        end = start + len(line)
        ranges.append((start, end))
        start = end
    return tuple(ranges)


def _line_content(text: str, start: int, end: int) -> str:
    return text[start:end].removesuffix("\n")


def _is_blank_line(text: str, start: int, end: int) -> bool:
    return _line_content(text, start, end).strip(" \t") == ""


def _is_table_delimiter(line: str) -> bool:
    stripped = line.strip(" \t").strip("|")
    cells = [cell.strip(" \t") for cell in stripped.split("|")]
    return len(cells) >= 2 and all(_TABLE_DELIMITER_CELL.fullmatch(cell) for cell in cells)


def _plain_block_scopes(text: str, lines: tuple[ScalarRun, ...]) -> tuple[ScalarRun, ...]:
    scopes: list[ScalarRun] = []
    paragraph_start: int | None = None
    paragraph_end = 0
    for line_start, line_end in lines:
        if _ATX_HEADING.match(_line_content(text, line_start, line_end)):
            if paragraph_start is not None:
                scopes.append((paragraph_start, paragraph_end))
                paragraph_start = None
            scopes.append((line_start, line_end))
        else:
            if paragraph_start is None:
                paragraph_start = line_start
            paragraph_end = line_end
    if paragraph_start is not None:
        scopes.append((paragraph_start, paragraph_end))
    return tuple(scopes)


def _table_cell_ranges(
    source: NormalizedSource, line_start: int, line_end: int
) -> tuple[ScalarRun, ...]:
    text = source.text
    code_candidates = arbitrate_candidates(
        scan_backtick_runs(
            source,
            source.byte_offset(line_start),
            source.byte_offset(line_end),
        )
    )
    code_ranges = tuple(
        (source.scalar_index(candidate.start), source.scalar_index(candidate.end))
        for candidate in code_candidates
    )
    boundaries = [line_start]
    code_index = 0
    for index in range(line_start, line_end):
        while code_index < len(code_ranges) and index >= code_ranges[code_index][1]:
            code_index += 1
        inside_code = (
            code_index < len(code_ranges)
            and code_ranges[code_index][0] <= index < code_ranges[code_index][1]
        )
        if text[index] == "|" and escape_is_even(text, index) and not inside_code:
            boundaries.append(index)
            boundaries.append(index + 1)
    boundaries.append(line_end)
    return tuple(
        (cell_start, cell_end)
        for cell_start, cell_end in zip(boundaries[::2], boundaries[1::2], strict=True)
        if cell_start < cell_end
    )


def _block_inline_scopes(
    source: NormalizedSource, lines: tuple[ScalarRun, ...]
) -> tuple[ByteRange, ...]:
    text = source.text
    separator_index: int | None = None
    for index in range(1, len(lines)):
        line_start, line_end = lines[index]
        header_start, header_end = lines[index - 1]
        if _is_table_delimiter(_line_content(text, line_start, line_end)) and "|" in _line_content(
            text, header_start, header_end
        ):
            separator_index = index
            break

    scalar_scopes: list[ScalarRun] = []
    if separator_index is None:
        scalar_scopes.extend(_plain_block_scopes(text, lines))
    else:
        header_index = separator_index - 1
        if header_index > 0:
            scalar_scopes.append((lines[0][0], lines[header_index - 1][1]))
        for line_start, line_end in lines[header_index:]:
            scalar_scopes.extend(_table_cell_ranges(source, line_start, line_end))

    return tuple(
        (source.byte_offset(start), source.byte_offset(end))
        for start, end in scalar_scopes
        if start < end
    )


def _default_inline_scopes(source: NormalizedSource) -> tuple[ByteRange, ...]:
    scopes: list[ByteRange] = []
    block: list[ScalarRun] = []
    for line_range in _line_scalar_ranges(source.text):
        if _is_blank_line(source.text, *line_range):
            if block:
                scopes.extend(_block_inline_scopes(source, tuple(block)))
                block.clear()
        else:
            block.append(line_range)
    if block:
        scopes.extend(_block_inline_scopes(source, tuple(block)))
    return tuple(scopes)


def scan_protected_regions(
    source: NormalizedSource,
    *,
    inline_scopes: tuple[ByteRange, ...] | None = None,
) -> tuple[ProtectedRegion, ...]:
    """Scan inline scopes and emit sorted source-exact math regions."""
    scopes = _default_inline_scopes(source) if inline_scopes is None else inline_scopes
    selected: list[Candidate] = []
    previous_scope_end = 0
    for start, end in scopes:
        if start < previous_scope_end or end > source.byte_length:
            raise InvalidRegionError("inline scopes overlap or leave normalized source")
        selected.extend(scan_inline_scope(source, start, end))
        previous_scope_end = end

    math_candidates = tuple(
        candidate for candidate in selected if candidate.kind is not RegionKind.code_span
    )
    regions = tuple(
        candidate.to_region(source, index=index) for index, candidate in enumerate(math_candidates)
    )
    return validate_regions(source, regions)
