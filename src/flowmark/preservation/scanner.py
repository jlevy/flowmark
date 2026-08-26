"""Portable pre-parse scanner for source-exact protected regions."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import cast

from flowmark.preservation.model import (
    Candidate,
    ContainerContext,
    InvalidRegionError,
    NormalizedSource,
    ProtectedRegion,
    RegionForm,
    RegionKind,
    validate_regions,
)
from flowmark.preservation.registry import RECOGNIZER_BY_KIND, BlockRuleKind

ByteRange = tuple[int, int]
ScalarRun = tuple[int, int]

_MYST_ROLE = "{math}"
_BEGIN_PREFIX = "\\begin{"
_END_PREFIX = "\\end{"
_TABLE_DELIMITER_CELL = re.compile(r":?-{3,}:?\Z")
_ATX_HEADING = re.compile(r" {0,3}#{1,6}(?:[ \t]+|$)")
_THEMATIC_BREAK = re.compile(r"(?:(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|(?:-[ \t]*){3,})\Z")
_MULTILINE_TABLE_RULE = re.compile(r"-{3,}(?:[ \t]+-{3,})*\Z")
_TABLE_CAPTION = re.compile(r"(?:(?:Table|table):|:)(?:[ \t]+|\Z)")
_OBSIDIAN_CALLOUT = re.compile(r"\[![A-Za-z0-9][A-Za-z0-9_-]*\][+-]?(?:[ \t]+.*)?\Z")
_COLON_FENCE = re.compile(r"(:{3,})(.*)\Z")


class _DollarState(Enum):
    none = auto()
    single = auto()
    double = auto()


class _ContainerKind(Enum):
    quote = auto()
    list_item = auto()


@dataclass(frozen=True, slots=True)
class _ContainerFrame:
    kind: _ContainerKind
    identity: int
    content_column: int = 0


@dataclass(frozen=True, slots=True)
class ContainerLine:
    """One raw line plus its portable logical container view."""

    index: int
    start: int
    end: int
    content_start: int
    content_end: int
    logical_column: int
    context: ContainerContext
    container_key: tuple[tuple[str, int, int], ...]
    frames: tuple[_ContainerFrame, ...]
    lazy: bool = False

    def __post_init__(self) -> None:
        if self.start > self.content_start or self.content_start > self.content_end:
            raise InvalidRegionError("container line offsets are out of order")
        if self.content_end > self.end:
            raise InvalidRegionError("container line content ends outside its raw line")
        if self.logical_column < 0:
            raise InvalidRegionError("container line column must be nonnegative")


@dataclass(frozen=True, slots=True)
class OpaqueBlock:
    """Existing Markdown block excluded from preservation recognition."""

    kind: BlockRuleKind
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.kind not in {
            BlockRuleKind.yaml_frontmatter,
            BlockRuleKind.fenced_code,
            BlockRuleKind.indented_code,
        }:
            raise InvalidRegionError("opaque block uses a non-opaque rule kind")
        if self.start < 0 or self.start >= self.end:
            raise InvalidRegionError("opaque block offsets are invalid")


@dataclass(frozen=True, slots=True)
class InlineScope:
    """One parser-independent paragraph, heading, or table-cell scan scope."""

    start: int
    end: int
    context: ContainerContext

    def __post_init__(self) -> None:
        if self.start < 0 or self.start >= self.end:
            raise InvalidRegionError("inline scope offsets are invalid")


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


def arbitrate_candidates(
    candidates: tuple[Candidate, ...],
    *,
    start: int,
    end: int,
) -> tuple[Candidate, ...]:
    """Select candidates with a fixed-pass radix order over UTF-8 byte starts."""
    if start < 0 or start > end or end >= 1 << 64:
        raise InvalidRegionError("arbitration scope is invalid")
    for candidate in candidates:
        if candidate.start < start or candidate.end > end:
            raise InvalidRegionError("candidate leaves its arbitration scope")
    if len(candidates) < 2:
        return candidates

    ordered = list(candidates)
    for shift in range(0, 64, 8):
        counts = [0] * 256
        for candidate in ordered:
            counts[(candidate.start >> shift) & 0xFF] += 1
        next_position = 0
        for bucket, count in enumerate(counts):
            counts[bucket] = next_position
            next_position += count
        pass_output: list[Candidate | None] = [None] * len(ordered)
        for candidate in ordered:
            bucket = (candidate.start >> shift) & 0xFF
            pass_output[counts[bucket]] = candidate
            counts[bucket] += 1
        ordered = cast(list[Candidate], pass_output)

    selected: list[Candidate] = []
    previous_end = start
    candidate_index = 0
    while candidate_index < len(ordered):
        candidate = ordered[candidate_index]
        candidate_index += 1
        candidate_key = (
            RECOGNIZER_BY_KIND[candidate.kind].priority,
            -(candidate.end - candidate.start),
            candidate.kind.value,
        )
        while candidate_index < len(ordered) and ordered[candidate_index].start == candidate.start:
            alternate = ordered[candidate_index]
            alternate_key = (
                RECOGNIZER_BY_KIND[alternate.kind].priority,
                -(alternate.end - alternate.start),
                alternate.kind.value,
            )
            if alternate_key < candidate_key:
                candidate = alternate
                candidate_key = alternate_key
            candidate_index += 1
        if candidate.start >= previous_end:
            selected.append(candidate)
            previous_end = candidate.end
    return tuple(selected)


def scan_inline_scope(
    source: NormalizedSource,
    start: int,
    end: int,
    *,
    container: ContainerContext | None = None,
) -> tuple[Candidate, ...]:
    """Propose and arbitrate every built-in inline recognizer in one scope."""
    candidates = (
        *scan_composite_math(source, start, end),
        *scan_backtick_runs(source, start, end),
        *scan_paren_math(source, start, end),
        *scan_inline_environments(source, start, end),
        *scan_dollar_runs(source, start, end),
    )
    selected = arbitrate_candidates(candidates, start=start, end=end)
    if container is None:
        return selected
    return tuple(replace(candidate, container=container) for candidate in selected)


def _line_scalar_ranges(text: str) -> tuple[ScalarRun, ...]:
    ranges: list[ScalarRun] = []
    start = 0
    for line in text.splitlines(keepends=True):
        end = start + len(line)
        ranges.append((start, end))
        start = end
    return tuple(ranges)


def _advance_column(column: int, scalar: str) -> int:
    return column + 1 if scalar == " " else column + (4 - column % 4)


def _consume_indent(
    text: str,
    index: int,
    end: int,
    column: int,
    *,
    maximum: int,
) -> tuple[int, int]:
    origin = column
    while index < end and text[index] in " \t":
        next_column = _advance_column(column, text[index])
        if next_column - origin > maximum:
            break
        index += 1
        column = next_column
    return index, column


def _consume_to_column(
    text: str, index: int, end: int, column: int, target: int
) -> tuple[int, int] | None:
    while index < end and text[index] in " \t" and column < target:
        column = _advance_column(column, text[index])
        index += 1
    return (index, column) if column >= target else None


def _consume_quote_marker(text: str, index: int, end: int, column: int) -> tuple[int, int] | None:
    marker_index, marker_column = _consume_indent(
        text,
        index,
        end,
        column,
        maximum=3,
    )
    if marker_index >= end or text[marker_index] != ">":
        return None
    marker_index += 1
    marker_column += 1
    if marker_index < end and text[marker_index] in " \t":
        marker_column = _advance_column(marker_column, text[marker_index])
        marker_index += 1
    return marker_index, marker_column


def _list_marker_end(text: str, index: int, end: int) -> int | None:
    if index >= end:
        return None
    if text[index] in "-*+":
        marker_end = index + 1
    elif text[index].isdigit():
        marker_end = index
        while marker_end < end and marker_end - index < 9 and text[marker_end].isdigit():
            marker_end += 1
        if marker_end >= end or text[marker_end] not in ".)":
            return None
        marker_end += 1
    else:
        return None
    if marker_end < end and text[marker_end] not in " \t":
        return None
    return marker_end


def _consume_list_marker(
    text: str,
    index: int,
    end: int,
    column: int,
) -> tuple[int, int, int, int] | None:
    marker_index, marker_column = _consume_indent(
        text,
        index,
        end,
        column,
        maximum=3,
    )
    marker_end = _list_marker_end(text, marker_index, end)
    if marker_end is None:
        return None

    after_marker_column = marker_column + (marker_end - marker_index)
    if marker_end == end:
        return marker_end, after_marker_column, after_marker_column + 1, marker_index

    padding_end = marker_end
    padding_column = after_marker_column
    while padding_end < end and text[padding_end] in " \t":
        padding_column = _advance_column(padding_column, text[padding_end])
        padding_end += 1

    padding_width = padding_column - after_marker_column
    if padding_end < end and padding_width <= 4:
        content_start = padding_end
        content_column = padding_column
    else:
        content_start = marker_end + 1
        content_column = _advance_column(after_marker_column, text[marker_end])
    return content_start, content_column, content_column, marker_index


def _match_frame(
    text: str,
    index: int,
    end: int,
    column: int,
    frame: _ContainerFrame,
) -> tuple[int, int] | None:
    if frame.kind is _ContainerKind.quote:
        return _consume_quote_marker(text, index, end, column)
    return _consume_to_column(text, index, end, column, frame.content_column)


def _parse_new_frames(
    text: str,
    index: int,
    end: int,
    column: int,
    frames: list[_ContainerFrame],
) -> tuple[int, int]:
    while index < end:
        quote = _consume_quote_marker(text, index, end, column)
        if quote is not None:
            marker_index, _ = _consume_indent(
                text,
                index,
                end,
                column,
                maximum=3,
            )
            frames.append(_ContainerFrame(_ContainerKind.quote, marker_index))
            index, column = quote
            continue

        list_marker = _consume_list_marker(text, index, end, column)
        if list_marker is None:
            break
        index, column, content_column, marker_index = list_marker
        frames.append(
            _ContainerFrame(
                _ContainerKind.list_item,
                marker_index,
                content_column,
            )
        )
    return index, column


def _container_context(frames: tuple[_ContainerFrame, ...]) -> ContainerContext:
    list_frames = tuple(frame for frame in frames if frame.kind is _ContainerKind.list_item)
    return ContainerContext(
        blockquote_depth=sum(frame.kind is _ContainerKind.quote for frame in frames),
        list_depth=len(list_frames),
        content_column=list_frames[-1].content_column if list_frames else 0,
    )


def _container_key(frames: tuple[_ContainerFrame, ...]) -> tuple[tuple[str, int, int], ...]:
    return tuple((frame.kind.name, frame.identity, frame.content_column) for frame in frames)


def _payload_start(text: str, start: int, end: int) -> int:
    return _consume_indent(text, start, end, 0, maximum=3)[0]


def _starts_block_structure(text: str, start: int, end: int) -> bool:
    content_start = _payload_start(text, start, end)
    content = text[content_start:end]
    if not content:
        return False
    return bool(
        _ATX_HEADING.match(text[start:end])
        or _consume_quote_marker(text, start, end, 0)
        or _consume_list_marker(text, start, end, 0)
        or re.match(r"(`{3,}|~{3,})", content)
        or _THEMATIC_BREAK.fullmatch(content)
        or content in {"$$", "\\[", "\\]"}
        or content.startswith(("\\begin{", "\\end{"))
    )


def build_container_view(source: NormalizedSource) -> tuple[ContainerLine, ...]:
    """Derive raw line ranges and container identities without parsing Markdown."""
    text = source.text
    active_frames: tuple[_ContainerFrame, ...] = ()
    previous_allows_lazy = False
    views: list[ContainerLine] = []

    for line_number, (line_start, line_end) in enumerate(_line_scalar_ranges(text)):
        content_end = line_end - 1 if text[line_end - 1 : line_end] == "\n" else line_end
        index = line_start
        column = 0
        matched_count = 0
        for frame in active_frames:
            matched = _match_frame(text, index, content_end, column, frame)
            if matched is None:
                break
            index, column = matched
            matched_count += 1

        remaining_blank = text[index:content_end].strip(" \t") == ""
        lazy = False
        if (
            matched_count < len(active_frames)
            and previous_allows_lazy
            and not remaining_blank
            and not _starts_block_structure(text, index, content_end)
        ):
            frames = list(active_frames)
            lazy = True
        else:
            frames = list(active_frames[:matched_count])
            index, column = _parse_new_frames(
                text,
                index,
                content_end,
                column,
                frames,
            )

        frame_tuple = tuple(frames)
        view = ContainerLine(
            index=line_number,
            start=source.byte_offset(line_start),
            end=source.byte_offset(line_end),
            content_start=source.byte_offset(index),
            content_end=source.byte_offset(content_end),
            logical_column=column,
            context=_container_context(frame_tuple),
            container_key=_container_key(frame_tuple),
            frames=frame_tuple,
            lazy=lazy,
        )
        views.append(view)

        if remaining_blank:
            retained: list[_ContainerFrame] = list(active_frames[:matched_count])
            for frame in active_frames[matched_count:]:
                if frame.kind is _ContainerKind.quote:
                    break
                retained.append(frame)
            active_frames = tuple(frames) if len(frames) > matched_count else tuple(retained)
            previous_allows_lazy = False
        else:
            active_frames = frame_tuple
            previous_allows_lazy = not _starts_block_structure(text, index, content_end)

    return tuple(views)


def _scalar_line_bounds(source: NormalizedSource, line: ContainerLine) -> tuple[int, int]:
    start = source.scalar_index(line.start)
    end = source.scalar_index(line.content_end)
    return start, end


def _content_under_frames(
    source: NormalizedSource,
    line: ContainerLine,
    frames: tuple[_ContainerFrame, ...],
) -> tuple[int, int, int] | None:
    start, end = _scalar_line_bounds(source, line)
    index = start
    column = 0
    for frame_index, frame in enumerate(frames):
        matched = _match_frame(source.text, index, end, column, frame)
        if matched is None:
            remaining_frames = frames[frame_index:]
            if source.text[index:end].strip(" \t") == "" and all(
                remaining.kind is _ContainerKind.list_item for remaining in remaining_frames
            ):
                return end, end, column
            return None
        index, column = matched
    return index, end, column


def _line_payload_bounds(
    source: NormalizedSource,
    line: ContainerLine,
    *,
    frames: tuple[_ContainerFrame, ...] | None = None,
) -> tuple[int, int]:
    if frames is None:
        start = source.scalar_index(line.content_start)
        end = source.scalar_index(line.content_end)
        column = line.logical_column
    else:
        content = _content_under_frames(source, line, frames)
        if content is None:
            raise InvalidRegionError("line is outside the requested container")
        start, end, column = content
    start, _ = _consume_indent(source.text, start, end, column, maximum=3)
    return start, end


def _line_payload(
    source: NormalizedSource,
    line: ContainerLine,
    *,
    frames: tuple[_ContainerFrame, ...] | None = None,
) -> str:
    start, end = _line_payload_bounds(source, line, frames=frames)
    return source.text[start:end].rstrip(" \t")


def _scaffold_prefix(source: NormalizedSource, line: ContainerLine) -> str:
    """Return the exact opening-line prefix needed to retain parser placement."""
    delimiter_start, _ = _line_payload_bounds(source, line)
    line_start = source.scalar_index(line.start)
    return source.text[line_start:delimiter_start]


def _raw_line_content(source: NormalizedSource, line: ContainerLine) -> str:
    start, end = _scalar_line_bounds(source, line)
    return source.text[start:end]


def compatible_container(opener: ContainerLine, closer: ContainerLine) -> bool:
    """Return whether two structural delimiters occupy the same container item."""
    return (
        not opener.lazy
        and not closer.lazy
        and opener.container_key == closer.container_key
        and opener.context == closer.context
    )


def _fence_opener(payload: str) -> tuple[str, int] | None:
    match = re.fullmatch(r"(`{3,}|~{3,})(.*)", payload)
    if match is None or (match.group(1)[0] == "`" and "`" in match.group(2)):
        return None
    return match.group(1)[0], len(match.group(1))


def _fence_closes(payload: str, character: str, length: int) -> bool:
    stripped = payload.rstrip(" \t")
    return len(stripped) >= length and set(stripped) == {character}


def _line_indent_width(source: NormalizedSource, line: ContainerLine) -> int:
    start = source.scalar_index(line.content_start)
    end = source.scalar_index(line.content_end)
    index = start
    column = line.logical_column
    while index < end and source.text[index] in " \t":
        column = _advance_column(column, source.text[index])
        index += 1
    return column - line.logical_column


def _opaque_line_flags(
    lines: tuple[ContainerLine, ...], blocks: tuple[OpaqueBlock, ...]
) -> tuple[bool, ...]:
    flags = [False] * len(lines)
    block_index = 0
    for line in lines:
        while block_index < len(blocks) and blocks[block_index].end <= line.start:
            block_index += 1
        if (
            block_index < len(blocks)
            and blocks[block_index].start < line.end
            and line.start < blocks[block_index].end
        ):
            flags[line.index] = True
    return tuple(flags)


def scan_existing_opaque_blocks(
    source: NormalizedSource,
    lines: tuple[ContainerLine, ...] | None = None,
) -> tuple[OpaqueBlock, ...]:
    """Find leading YAML frontmatter plus fenced and indented code blocks."""
    views = build_container_view(source) if lines is None else lines
    blocks: list[OpaqueBlock] = []
    covered = [False] * len(views)

    if views and not views[0].container_key and _raw_line_content(source, views[0]) == "---":
        for closer_index in range(1, len(views)):
            closer = views[closer_index]
            if _raw_line_content(source, closer) in {"---", "..."}:
                blocks.append(
                    OpaqueBlock(
                        BlockRuleKind.yaml_frontmatter,
                        views[0].start,
                        closer.end,
                    )
                )
                for index in range(closer_index + 1):
                    covered[index] = True
                break

    line_index = 0
    while line_index < len(views):
        if covered[line_index]:
            line_index += 1
            continue
        opener = views[line_index]
        fence = None if opener.lazy else _fence_opener(_line_payload(source, opener))
        if fence is None:
            line_index += 1
            continue
        character, length = fence
        final_index = line_index
        closer_index: int | None = None
        for candidate_index in range(line_index + 1, len(views)):
            candidate = views[candidate_index]
            content = _content_under_frames(source, candidate, opener.frames)
            if content is None:
                break
            final_index = candidate_index
            payload = _line_payload(source, candidate, frames=opener.frames)
            if _fence_closes(payload, character, length):
                closer_index = candidate_index
                break
        if closer_index is not None:
            final_index = closer_index
        block = OpaqueBlock(
            BlockRuleKind.fenced_code,
            opener.start,
            views[final_index].end,
        )
        blocks.append(block)
        for index in range(line_index, final_index + 1):
            covered[index] = True
        line_index = final_index + 1

    line_index = 0
    while line_index < len(views):
        if covered[line_index] or _line_indent_width(source, views[line_index]) < 4:
            line_index += 1
            continue
        if line_index > 0 and not covered[line_index - 1]:
            previous = _line_payload(source, views[line_index - 1])
            if previous:
                line_index += 1
                continue
        start_index = line_index
        final_index = line_index
        line_index += 1
        while line_index < len(views) and not covered[line_index]:
            line = views[line_index]
            if _line_payload(source, line) == "":
                line_index += 1
                continue
            if (
                line.container_key == views[start_index].container_key
                and _line_indent_width(source, line) >= 4
            ):
                final_index = line_index
                line_index += 1
                continue
            break
        block = OpaqueBlock(
            BlockRuleKind.indented_code,
            views[start_index].start,
            views[final_index].end,
        )
        blocks.append(block)
        for index in range(start_index, final_index + 1):
            covered[index] = True

    block_by_start = {block.start: block for block in blocks}
    return tuple(block_by_start[line.start] for line in views if line.start in block_by_start)


_DOLLAR_CLOSER = re.compile(r"\$\$(?:[ \t]+(?:\([^()\n]*\)|\{[^{}\n]*\}))?\Z")
_ENVIRONMENT_LINE = re.compile(r"\\(begin|end)\{([^{}\n]+)\}\Z")


def scan_display_math(
    source: NormalizedSource,
    lines: tuple[ContainerLine, ...] | None = None,
    opaque_blocks: tuple[OpaqueBlock, ...] = (),
) -> tuple[Candidate, ...]:
    """Pair compatible standalone dollar and bracket display delimiters."""
    views = build_container_view(source) if lines is None else lines
    opaque = _opaque_line_flags(views, opaque_blocks)
    pending_dollars: dict[tuple[tuple[str, int, int], ...], ContainerLine] = {}
    pending_brackets: dict[tuple[tuple[str, int, int], ...], ContainerLine] = {}
    candidates: list[Candidate] = []

    for line in views:
        if opaque[line.index] or line.lazy:
            continue
        payload = _line_payload(source, line)
        key = line.container_key
        if payload == "$$":
            opener = pending_dollars.pop(key, None)
            if opener is None:
                pending_dollars[key] = line
            elif compatible_container(opener, line):
                candidates.append(
                    Candidate(
                        RegionKind.math_dollar_block,
                        RegionForm.block,
                        opener.start,
                        line.end,
                        opener.context,
                        _scaffold_prefix(source, opener),
                    )
                )
            continue
        if _DOLLAR_CLOSER.fullmatch(payload):
            opener = pending_dollars.pop(key, None)
            if opener is not None and compatible_container(opener, line):
                candidates.append(
                    Candidate(
                        RegionKind.math_dollar_block,
                        RegionForm.block,
                        opener.start,
                        line.end,
                        opener.context,
                        _scaffold_prefix(source, opener),
                    )
                )
            continue
        if payload == "\\[":
            pending_brackets.setdefault(key, line)
            continue
        if payload == "\\]":
            opener = pending_brackets.pop(key, None)
            if opener is not None and compatible_container(opener, line):
                candidates.append(
                    Candidate(
                        RegionKind.math_bracket_block,
                        RegionForm.block,
                        opener.start,
                        line.end,
                        opener.context,
                        _scaffold_prefix(source, opener),
                    )
                )
    return tuple(candidates)


def scan_environment_blocks(
    source: NormalizedSource,
    lines: tuple[ContainerLine, ...] | None = None,
    opaque_blocks: tuple[OpaqueBlock, ...] = (),
) -> tuple[Candidate, ...]:
    """Match standalone nested environments independently in each container item."""
    views = build_container_view(source) if lines is None else lines
    opaque = _opaque_line_flags(views, opaque_blocks)
    stacks: dict[
        tuple[tuple[str, int, int], ...],
        list[tuple[str, ContainerLine]],
    ] = {}
    candidates: list[Candidate] = []

    for line in views:
        if opaque[line.index] or line.lazy:
            continue
        match = _ENVIRONMENT_LINE.fullmatch(_line_payload(source, line))
        if match is None:
            continue
        command, name = match.groups()
        stack = stacks.setdefault(line.container_key, [])
        if command == "begin":
            stack.append((name, line))
        elif stack and stack[-1][0] == name:
            _, opener = stack.pop()
            if compatible_container(opener, line):
                candidates.append(
                    Candidate(
                        RegionKind.math_environment_block,
                        RegionForm.block,
                        opener.start,
                        line.end,
                        opener.context,
                        _scaffold_prefix(source, opener),
                    )
                )
    return tuple(candidates)


def _multiline_table_rule(payload: str) -> tuple[str, ...] | None:
    """Return a Pandoc dash-rule signature, or None for ordinary prose."""
    if _MULTILINE_TABLE_RULE.fullmatch(payload) is None:
        return None
    return tuple(re.findall(r"-{3,}", payload))


def _caption_extent_after(
    source: NormalizedSource,
    lines: tuple[ContainerLine, ...],
    closer_index: int,
    opener: ContainerLine,
) -> int:
    """Include one compatible following Pandoc caption paragraph when present."""
    index = closer_index + 1
    if index < len(lines):
        content = _content_under_frames(source, lines[index], opener.frames)
        if content is None:
            return closer_index
        if _line_payload(source, lines[index], frames=opener.frames) == "":
            index += 1
    if index >= len(lines):
        return closer_index
    line = lines[index]
    content = _content_under_frames(source, line, opener.frames)
    if (
        content is None
        or _TABLE_CAPTION.match(_line_payload(source, line, frames=opener.frames)) is None
    ):
        return closer_index
    final_index = index
    index += 1
    while index < len(lines):
        line = lines[index]
        if _content_under_frames(source, line, opener.frames) is None:
            break
        if _line_payload(source, line, frames=opener.frames) == "":
            break
        final_index = index
        index += 1
    return final_index


def scan_pandoc_multiline_tables(
    source: NormalizedSource,
    lines: tuple[ContainerLine, ...] | None = None,
    opaque_blocks: tuple[OpaqueBlock, ...] = (),
) -> tuple[Candidate, ...]:
    """Recognize complete Pandoc multiline tables without parsing their cells."""
    views = build_container_view(source) if lines is None else lines
    opaque = _opaque_line_flags(views, opaque_blocks)
    candidates: list[Candidate] = []
    opener_index = 0
    while opener_index < len(views):
        opener = views[opener_index]
        opener_payload = _line_payload(source, opener)
        opener_rule = (
            None if opaque[opener_index] or opener.lazy else _multiline_table_rule(opener_payload)
        )
        if opener_rule is None:
            opener_index += 1
            continue

        headered = len(opener_rule) == 1
        header_separator_seen = False
        body_content_seen = False
        body_blank_seen = False
        closer_index: int | None = None
        scan_index = opener_index + 1
        while scan_index < len(views):
            line = views[scan_index]
            if opaque[scan_index] or _content_under_frames(source, line, opener.frames) is None:
                break
            payload = _line_payload(source, line, frames=opener.frames)
            rule = _multiline_table_rule(payload)
            if payload == opener_payload and body_content_seen:
                if (headered and header_separator_seen) or (not headered and body_blank_seen):
                    closer_index = scan_index
                break
            if headered and not header_separator_seen and rule is not None and len(rule) >= 2:
                header_separator_seen = True
            elif payload == "":
                if body_content_seen:
                    body_blank_seen = True
            elif not headered or header_separator_seen:
                body_content_seen = True
            scan_index += 1

        if closer_index is None:
            opener_index += 1
            continue
        final_index = _caption_extent_after(source, views, closer_index, opener)
        candidates.append(
            Candidate(
                RegionKind.pandoc_multiline_table,
                RegionForm.block,
                opener.start,
                views[final_index].end,
                opener.context,
                _scaffold_prefix(source, opener),
            )
        )
        opener_index = final_index + 1
    return tuple(candidates)


def _line_within_frames(line: ContainerLine, frames: tuple[_ContainerFrame, ...]) -> bool:
    return len(line.frames) >= len(frames) and line.frames[: len(frames)] == frames


def scan_obsidian_callouts(
    source: NormalizedSource,
    lines: tuple[ContainerLine, ...] | None = None,
    opaque_blocks: tuple[OpaqueBlock, ...] = (),
) -> tuple[Candidate, ...]:
    """Preserve a complete quote block whose first logical line is a callout marker."""
    views = build_container_view(source) if lines is None else lines
    opaque = _opaque_line_flags(views, opaque_blocks)
    candidates: list[Candidate] = []
    for opener_index, opener in enumerate(views):
        if opaque[opener_index] or opener.lazy or not opener.frames:
            continue
        if opener.frames[-1].kind is not _ContainerKind.quote:
            continue
        if _OBSIDIAN_CALLOUT.fullmatch(_line_payload(source, opener)) is None:
            continue
        if opener_index > 0 and views[opener_index - 1].frames == opener.frames:
            continue

        final_index = opener_index
        for candidate_index in range(opener_index + 1, len(views)):
            candidate = views[candidate_index]
            if not _line_within_frames(candidate, opener.frames):
                break
            final_index = candidate_index
        candidates.append(
            Candidate(
                RegionKind.obsidian_callout,
                RegionForm.block,
                opener.start,
                views[final_index].end,
                opener.context,
                _scaffold_prefix(source, opener),
            )
        )
    return tuple(candidates)


def scan_colon_containers(
    source: NormalizedSource,
    lines: tuple[ContainerLine, ...] | None = None,
    opaque_blocks: tuple[OpaqueBlock, ...] = (),
) -> tuple[Candidate, ...]:
    """Match nested colon fences by container, without equal-length closure."""
    views = build_container_view(source) if lines is None else lines
    opaque = _opaque_line_flags(views, opaque_blocks)
    stacks: dict[tuple[tuple[str, int, int], ...], list[ContainerLine]] = {}
    candidates: list[Candidate] = []
    for line in views:
        if opaque[line.index] or line.lazy:
            continue
        match = _COLON_FENCE.fullmatch(_line_payload(source, line))
        if match is None:
            continue
        stack = stacks.setdefault(line.container_key, [])
        if match.group(2).strip(" \t"):
            stack.append(line)
            continue
        if not stack:
            continue
        opener = stack.pop()
        if compatible_container(opener, line):
            candidates.append(
                Candidate(
                    RegionKind.colon_container,
                    RegionForm.block,
                    opener.start,
                    line.end,
                    opener.context,
                    _scaffold_prefix(source, opener),
                )
            )
    return tuple(candidates)


def resolve_candidate_tree(
    source: NormalizedSource, candidates: tuple[Candidate, ...]
) -> tuple[Candidate, ...]:
    """Resolve closed outer blocks while retaining children of unmatched openers."""
    return arbitrate_candidates(candidates, start=0, end=source.byte_length)


def _is_table_delimiter(line: str) -> bool:
    stripped = line.strip(" \t").strip("|")
    cells = [cell.strip(" \t") for cell in stripped.split("|")]
    return len(cells) >= 2 and all(_TABLE_DELIMITER_CELL.fullmatch(cell) for cell in cells)


def _plain_block_scopes(
    source: NormalizedSource, lines: tuple[ContainerLine, ...]
) -> tuple[ScalarRun, ...]:
    scopes: list[ScalarRun] = []
    paragraph_start: int | None = None
    paragraph_end = 0
    for line in lines:
        line_start = source.scalar_index(line.content_start)
        line_end = source.scalar_index(line.end)
        payload = _line_payload(source, line)
        if _ATX_HEADING.match(payload):
            if paragraph_start is not None:
                scopes.append((paragraph_start, paragraph_end))
                paragraph_start = None
            scopes.append((line_start, line_end))
        else:
            if paragraph_start is None:
                paragraph_start = line_start
            paragraph_end = line_end
            if re.fullmatch(r"(?:=+|-+)[ \t]*", payload):
                scopes.append((paragraph_start, paragraph_end))
                paragraph_start = None
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
        ),
        start=source.byte_offset(line_start),
        end=source.byte_offset(line_end),
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


def _has_structural_pipe(source: NormalizedSource, line: ContainerLine) -> bool:
    start = source.scalar_index(line.content_start)
    end = source.scalar_index(line.content_end)
    cells = _table_cell_ranges(source, start, end)
    return len(cells) > 1 or source.text[start:end].lstrip(" \t").startswith("|")


def _block_inline_scopes(
    source: NormalizedSource, lines: tuple[ContainerLine, ...]
) -> tuple[InlineScope, ...]:
    scalar_scopes: list[ScalarRun] = []
    plain_lines: list[ContainerLine] = []

    def flush_plain() -> None:
        if plain_lines:
            scalar_scopes.extend(_plain_block_scopes(source, tuple(plain_lines)))
            plain_lines.clear()

    index = 0
    while index < len(lines):
        is_table_start = (
            index + 1 < len(lines)
            and _has_structural_pipe(source, lines[index])
            and _is_table_delimiter(_line_payload(source, lines[index + 1]))
        )
        if not is_table_start:
            plain_lines.append(lines[index])
            index += 1
            continue

        flush_plain()
        table_end = index + 2
        while table_end < len(lines) and _has_structural_pipe(source, lines[table_end]):
            table_end += 1
        for table_line in lines[index:table_end]:
            line_start = source.scalar_index(table_line.content_start)
            line_end = source.scalar_index(table_line.content_end)
            scalar_scopes.extend(_table_cell_ranges(source, line_start, line_end))
        index = table_end

    flush_plain()
    return tuple(
        InlineScope(
            source.byte_offset(start),
            source.byte_offset(end),
            lines[0].context,
        )
        for start, end in scalar_scopes
        if start < end
    )


def _range_line_flags(
    lines: tuple[ContainerLine, ...], ranges: tuple[ByteRange, ...]
) -> tuple[bool, ...]:
    flags = [False] * len(lines)
    range_index = 0
    for line in lines:
        while range_index < len(ranges) and ranges[range_index][1] <= line.start:
            range_index += 1
        if (
            range_index < len(ranges)
            and ranges[range_index][0] < line.end
            and line.start < ranges[range_index][1]
        ):
            flags[line.index] = True
    return tuple(flags)


def _merge_ranges(
    left: tuple[ByteRange, ...], right: tuple[ByteRange, ...]
) -> tuple[ByteRange, ...]:
    merged: list[ByteRange] = []
    left_index = 0
    right_index = 0
    while left_index < len(left) or right_index < len(right):
        if right_index >= len(right) or (
            left_index < len(left) and left[left_index][0] <= right[right_index][0]
        ):
            selected = left[left_index]
            left_index += 1
        else:
            selected = right[right_index]
            right_index += 1
        if merged and selected[0] < merged[-1][1]:
            previous = merged[-1]
            if selected[1] <= previous[1]:
                continue
            if selected[0] == previous[0]:
                merged[-1] = selected
                continue
            raise InvalidRegionError("excluded block ranges overlap without containment")
        merged.append(selected)
    return tuple(merged)


def _merge_candidates(
    left: tuple[Candidate, ...], right: tuple[Candidate, ...]
) -> tuple[Candidate, ...]:
    merged: list[Candidate] = []
    left_index = 0
    right_index = 0
    while left_index < len(left) or right_index < len(right):
        if right_index >= len(right) or (
            left_index < len(left) and left[left_index].start <= right[right_index].start
        ):
            selected = left[left_index]
            left_index += 1
        else:
            selected = right[right_index]
            right_index += 1
        if merged and selected.start < merged[-1].end:
            raise InvalidRegionError("selected block and inline candidates overlap")
        merged.append(selected)
    return tuple(merged)


def _default_inline_scopes(
    source: NormalizedSource,
    lines: tuple[ContainerLine, ...],
    excluded_ranges: tuple[ByteRange, ...],
) -> tuple[InlineScope, ...]:
    excluded = _range_line_flags(lines, excluded_ranges)
    scopes: list[InlineScope] = []
    block: list[ContainerLine] = []
    block_key: tuple[tuple[str, int, int], ...] | None = None
    for line in lines:
        blank = _line_payload(source, line) == ""
        if excluded[line.index] or blank or (block and line.container_key != block_key):
            if block:
                scopes.extend(_block_inline_scopes(source, tuple(block)))
                block.clear()
                block_key = None
        if not excluded[line.index] and not blank:
            if not block:
                block_key = line.container_key
            block.append(line)
    if block:
        scopes.extend(_block_inline_scopes(source, tuple(block)))
    return tuple(scopes)


def scan_protected_regions(
    source: NormalizedSource,
    *,
    inline_scopes: tuple[ByteRange, ...] | None = None,
) -> tuple[ProtectedRegion, ...]:
    """Scan block precedence and inline scopes into source-exact math regions."""
    lines = build_container_view(source)
    opaque_blocks = scan_existing_opaque_blocks(source, lines)
    block_candidates = resolve_candidate_tree(
        source,
        (
            *scan_pandoc_multiline_tables(source, lines, opaque_blocks),
            *scan_obsidian_callouts(source, lines, opaque_blocks),
            *scan_colon_containers(source, lines, opaque_blocks),
            *scan_display_math(source, lines, opaque_blocks),
            *scan_environment_blocks(source, lines, opaque_blocks),
        ),
    )
    excluded_ranges = _merge_ranges(
        tuple((block.start, block.end) for block in opaque_blocks),
        tuple((candidate.start, candidate.end) for candidate in block_candidates),
    )
    scopes = (
        _default_inline_scopes(source, lines, excluded_ranges)
        if inline_scopes is None
        else tuple(InlineScope(start, end, ContainerContext()) for start, end in inline_scopes)
    )
    inline_candidates: list[Candidate] = []
    previous_scope_end = 0
    excluded_index = 0
    for scope in scopes:
        start = scope.start
        end = scope.end
        if start < previous_scope_end or end > source.byte_length:
            raise InvalidRegionError("inline scopes overlap or leave normalized source")
        while excluded_index < len(excluded_ranges) and excluded_ranges[excluded_index][1] <= start:
            excluded_index += 1
        if (
            excluded_index < len(excluded_ranges)
            and start < excluded_ranges[excluded_index][1]
            and excluded_ranges[excluded_index][0] < end
        ):
            raise InvalidRegionError("inline scope overlaps an opaque or protected block")
        inline_candidates.extend(scan_inline_scope(source, start, end, container=scope.context))
        previous_scope_end = end

    protected_candidates = _merge_candidates(block_candidates, tuple(inline_candidates))
    regions = tuple(
        candidate.to_region(source, index=index)
        for index, candidate in enumerate(protected_candidates)
    )
    return validate_regions(source, regions)
