from __future__ import annotations

import difflib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal, cast

if sys.version_info >= (3, 11):
    import tomllib  # pyright: ignore[reportUnreachable]
else:
    import tomli as tomllib  # type: ignore[no-redef]  # pyright: ignore[reportUnreachable]


SCHEMA_VERSION = 1
CORPUS_NAME = "flowmark-language-neutral-conformance"
ID_PATTERN = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)*\Z")
CHANGE_ID_PATTERN = re.compile(r"FM-[A-Z0-9]+(?:-[A-Z0-9]+)*\Z")
ENV_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
ALLOWED_PATH_ROOTS = (
    "tests/parity_corpus/",
    "tests/tryscript/fixtures/",
    "tests/testdocs/",
)
TOP_LEVEL_FIELDS = frozenset({"schema_version", "corpus", "defaults", "case"})
DEFAULTS_FIELDS = frozenset({"env"})
COMMON_CASE_FIELDS = frozenset(
    {
        "id",
        "change_id",
        "description",
        "kind",
        "tags",
        "args",
        "expected_stdout",
        "expected_stderr",
        "expected_exit",
        "idempotent",
    }
)
KIND_CASE_FIELDS = frozenset({"stdin", "before_tree", "after_tree"})
ENV_ALLOWLIST = ("PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "TMPDIR", "TEMP", "TMP")
MAX_DIAGNOSTIC_BYTES = 8_192

CaseKind = Literal["stdin", "files"]


class ConformanceError(ValueError):
    """A stable conformance schema or execution failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code: str = code


@dataclass(frozen=True)
class ConformanceCase:
    """One validated language-neutral CLI behavior case."""

    id: str
    change_id: str
    description: str
    kind: CaseKind
    tags: tuple[str, ...]
    args: tuple[str, ...]
    expected_stdout: PurePosixPath
    expected_stderr: PurePosixPath
    expected_exit: int
    idempotent: bool
    stdin: PurePosixPath | None = None
    before_tree: PurePosixPath | None = None
    after_tree: PurePosixPath | None = None


@dataclass(frozen=True)
class ConformanceManifest:
    """Validated corpus manifest in source order."""

    corpus: str
    default_env: tuple[tuple[str, str], ...]
    cases: tuple[ConformanceCase, ...]


@dataclass(frozen=True)
class FileSnapshot:
    """One regular file in an exact sandbox tree snapshot."""

    path: PurePosixPath
    content: bytes


@dataclass(frozen=True)
class ProcessResult:
    """Raw, byte-oriented result from one conformance process."""

    command: tuple[str, ...]
    stdout: bytes
    stderr: bytes
    exit_code: int
    tree: tuple[FileSnapshot, ...]


@dataclass(frozen=True)
class _CaseFields:
    """Validated non-path fields plus unresolved repository-relative paths."""

    id: str
    change_id: str
    description: str
    kind: CaseKind
    tags: tuple[str, ...]
    args: tuple[str, ...]
    expected_stdout: str
    expected_stderr: str
    expected_exit: int
    idempotent: bool
    stdin: str | None = None
    before_tree: str | None = None
    after_tree: str | None = None


def _mapping(value: object, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConformanceError("invalid-type", f"{location} must be a table")
    return cast(dict[str, Any], value)


def _unknown_fields(data: dict[str, Any], allowed: frozenset[str], location: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ConformanceError("unknown-field", f"{location} has unknown field {unknown[0]!r}")


def _required(data: dict[str, Any], field: str, location: str) -> Any:
    if field not in data:
        raise ConformanceError("missing-field", f"{location} is missing {field!r}")
    return data[field]


def _string(data: dict[str, Any], field: str, location: str) -> str:
    value = _required(data, field, location)
    if not isinstance(value, str) or not value:
        raise ConformanceError("invalid-type", f"{location}.{field} must be a nonempty string")
    return value


def _string_list(data: dict[str, Any], field: str, location: str) -> tuple[str, ...]:
    value = _required(data, field, location)
    if not isinstance(value, list):
        raise ConformanceError("invalid-type", f"{location}.{field} must be an array of strings")
    items = cast(list[object], value)
    if any(not isinstance(item, str) for item in items):
        raise ConformanceError("invalid-type", f"{location}.{field} must be an array of strings")
    return tuple(cast(list[str], items))


def _integer(data: dict[str, Any], field: str, location: str) -> int:
    value = _required(data, field, location)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConformanceError("invalid-type", f"{location}.{field} must be an integer")
    return value


def _boolean(data: dict[str, Any], field: str, location: str) -> bool:
    value = _required(data, field, location)
    if not isinstance(value, bool):
        raise ConformanceError("invalid-type", f"{location}.{field} must be a boolean")
    return value


def _lexical_path(raw_path: str, location: str) -> PurePosixPath:
    components = raw_path.split("/")
    if (
        raw_path.startswith("/")
        or "\\" in raw_path
        or any(component in {"", ".", ".."} for component in components)
        or not any(raw_path.startswith(root) for root in ALLOWED_PATH_ROOTS)
    ):
        raise ConformanceError("invalid-path", f"{location} is not a confined path")

    return PurePosixPath(raw_path)


def _validate_existing_path(
    relative_path: PurePosixPath,
    location: str,
    repo_root: Path,
    expected_kind: Literal["file", "directory"],
) -> None:
    raw_path = relative_path.as_posix()

    candidate = repo_root.joinpath(*relative_path.parts)
    current = repo_root
    for component in relative_path.parts:
        current /= component
        if current.is_symlink():
            raise ConformanceError("symlink-path", f"{location} traverses a symlink")

    if not candidate.exists():
        raise ConformanceError("missing-path", f"{location} does not exist: {raw_path}")
    if expected_kind == "file" and not candidate.is_file():
        raise ConformanceError("invalid-path-kind", f"{location} must name a file")
    if expected_kind == "directory" and not candidate.is_dir():
        raise ConformanceError("invalid-path-kind", f"{location} must name a directory")
    if expected_kind == "directory":
        for descendant in candidate.rglob("*"):
            if descendant.is_symlink():
                raise ConformanceError(
                    "symlink-path", f"{location} contains a symlink: {descendant.name}"
                )
            if not descendant.is_dir() and not descendant.is_file():
                raise ConformanceError(
                    "invalid-path-kind",
                    f"{location} contains a non-regular entry: {descendant.name}",
                )


def _validate_case_fields(data: dict[str, Any], index: int) -> _CaseFields:
    location = f"case[{index}]"
    _unknown_fields(data, COMMON_CASE_FIELDS | KIND_CASE_FIELDS, location)

    kind_value = _required(data, "kind", location)
    if kind_value not in {"stdin", "files"}:
        raise ConformanceError("invalid-kind", f"{location}.kind must be 'stdin' or 'files'")
    kind = cast(CaseKind, kind_value)

    if kind == "stdin":
        required_kind_fields = {"stdin"}
        forbidden_kind_fields = {"before_tree", "after_tree"}
    else:
        required_kind_fields = {"before_tree", "after_tree"}
        forbidden_kind_fields = {"stdin"}
    if not required_kind_fields.issubset(data) or forbidden_kind_fields.intersection(data):
        raise ConformanceError("invalid-kind-fields", f"{location} has fields invalid for {kind}")

    case_id = _string(data, "id", location)
    if ID_PATTERN.fullmatch(case_id) is None:
        raise ConformanceError("invalid-id", f"{location}.id is invalid: {case_id!r}")
    change_id = _string(data, "change_id", location)
    if CHANGE_ID_PATTERN.fullmatch(change_id) is None:
        raise ConformanceError(
            "invalid-change-id", f"{location}.change_id is invalid: {change_id!r}"
        )
    description = _string(data, "description", location)
    tags = _string_list(data, "tags", location)
    if not tags or any(ID_PATTERN.fullmatch(tag) is None for tag in tags):
        raise ConformanceError("invalid-tags", f"{location}.tags contains an invalid tag")
    if len(set(tags)) != len(tags):
        raise ConformanceError("duplicate-tags", f"{location}.tags contains a duplicate")

    args = _string_list(data, "args", location)
    if any(not arg for arg in args):
        raise ConformanceError("invalid-args", f"{location}.args contains an empty argument")
    if kind == "stdin" and args.count("-") != 1:
        raise ConformanceError("invalid-args", f"{location}.args must contain '-' exactly once")
    if kind == "files" and "-" in args:
        raise ConformanceError("invalid-args", f"{location}.args cannot contain '-' for files")

    expected_exit = _integer(data, "expected_exit", location)
    if not 0 <= expected_exit <= 255:
        raise ConformanceError("invalid-exit", f"{location}.expected_exit must be 0..255")
    idempotent = _boolean(data, "idempotent", location)
    if idempotent and expected_exit != 0:
        raise ConformanceError("invalid-idempotence", f"{location} cannot repeat a failing case")

    expected_stdout = _string(data, "expected_stdout", location)
    expected_stderr = _string(data, "expected_stderr", location)
    stdin = _string(data, "stdin", location) if kind == "stdin" else None
    before_tree = _string(data, "before_tree", location) if kind == "files" else None
    after_tree = _string(data, "after_tree", location) if kind == "files" else None

    return _CaseFields(
        id=case_id,
        change_id=change_id,
        description=description,
        kind=kind,
        tags=tags,
        args=args,
        expected_stdout=expected_stdout,
        expected_stderr=expected_stderr,
        expected_exit=expected_exit,
        idempotent=idempotent,
        stdin=stdin,
        before_tree=before_tree,
        after_tree=after_tree,
    )


def _resolve_case_paths(fields: _CaseFields, index: int) -> ConformanceCase:
    location = f"case[{index}]"
    return ConformanceCase(
        id=fields.id,
        change_id=fields.change_id,
        description=fields.description,
        kind=fields.kind,
        tags=fields.tags,
        args=fields.args,
        expected_stdout=_lexical_path(fields.expected_stdout, f"{location}.expected_stdout"),
        expected_stderr=_lexical_path(fields.expected_stderr, f"{location}.expected_stderr"),
        expected_exit=fields.expected_exit,
        idempotent=fields.idempotent,
        stdin=(
            _lexical_path(fields.stdin, f"{location}.stdin") if fields.stdin is not None else None
        ),
        before_tree=(
            _lexical_path(fields.before_tree, f"{location}.before_tree")
            if fields.before_tree is not None
            else None
        ),
        after_tree=(
            _lexical_path(fields.after_tree, f"{location}.after_tree")
            if fields.after_tree is not None
            else None
        ),
    )


def _validate_case_paths(case: ConformanceCase, index: int, repo_root: Path) -> None:
    location = f"case[{index}]"
    _validate_existing_path(case.expected_stdout, f"{location}.expected_stdout", repo_root, "file")
    _validate_existing_path(case.expected_stderr, f"{location}.expected_stderr", repo_root, "file")
    if case.stdin is not None:
        _validate_existing_path(case.stdin, f"{location}.stdin", repo_root, "file")
    if case.before_tree is not None:
        _validate_existing_path(case.before_tree, f"{location}.before_tree", repo_root, "directory")
    if case.after_tree is not None:
        _validate_existing_path(case.after_tree, f"{location}.after_tree", repo_root, "directory")


def validate_manifest(data: object, repo_root: Path) -> ConformanceManifest:
    """Validate parsed TOML and return the typed version 1 manifest."""
    root = _mapping(data, "manifest")
    _unknown_fields(root, TOP_LEVEL_FIELDS, "manifest")

    schema_version = _integer(root, "schema_version", "manifest")
    if schema_version != SCHEMA_VERSION:
        raise ConformanceError(
            "unsupported-schema-version",
            f"schema version {schema_version} is unsupported; expected {SCHEMA_VERSION}",
        )
    corpus = _string(root, "corpus", "manifest")
    if corpus != CORPUS_NAME:
        raise ConformanceError("invalid-corpus", f"manifest.corpus must be {CORPUS_NAME!r}")

    defaults = _mapping(root.get("defaults", {}), "manifest.defaults")
    _unknown_fields(defaults, DEFAULTS_FIELDS, "manifest.defaults")
    env = _mapping(defaults.get("env", {}), "manifest.defaults.env")
    default_env: list[tuple[str, str]] = []
    for name, value in env.items():
        if ENV_NAME_PATTERN.fullmatch(name) is None or not isinstance(value, str):
            raise ConformanceError(
                "invalid-environment", "manifest.defaults.env must map names to strings"
            )
        default_env.append((name, value))

    raw_cases_value = _required(root, "case", "manifest")
    if not isinstance(raw_cases_value, list) or not raw_cases_value:
        raise ConformanceError("invalid-type", "manifest.case must be a nonempty array")
    raw_cases = cast(list[object], raw_cases_value)
    case_fields = tuple(
        _validate_case_fields(_mapping(case, f"case[{index}]"), index)
        for index, case in enumerate(raw_cases)
    )
    seen: set[str] = set()
    for fields in case_fields:
        if fields.id in seen:
            raise ConformanceError("duplicate-case-id", f"duplicate case ID {fields.id!r}")
        seen.add(fields.id)

    cases = tuple(_resolve_case_paths(fields, index) for index, fields in enumerate(case_fields))
    for index, case in enumerate(cases):
        _validate_case_paths(case, index, repo_root)

    return ConformanceManifest(corpus=corpus, default_env=tuple(default_env), cases=cases)


def load_manifest(path: Path, repo_root: Path) -> ConformanceManifest:
    """Load and validate a UTF-8 TOML conformance manifest."""
    try:
        text = path.read_text(encoding="utf-8")
        data = tomllib.loads(text)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ConformanceError("invalid-manifest", f"cannot load {path}: {error}") from error
    return validate_manifest(data, repo_root.resolve())


def select_cases(
    manifest: ConformanceManifest,
    *,
    ids: tuple[str, ...] = (),
    change_ids: tuple[str, ...] = (),
    tags: tuple[str, ...] = (),
) -> tuple[ConformanceCase, ...]:
    """Select cases by exact values, using AND between populated filter groups."""
    known_ids = {case.id for case in manifest.cases}
    known_change_ids = {case.change_id for case in manifest.cases}
    known_tags = {tag for case in manifest.cases for tag in case.tags}
    for name, requested, known in (
        ("case ID", ids, known_ids),
        ("change ID", change_ids, known_change_ids),
        ("tag", tags, known_tags),
    ):
        unknown = sorted(set(requested) - known)
        if unknown:
            raise ConformanceError("unknown-selector", f"unknown {name} selector {unknown[0]!r}")

    selected = tuple(
        case
        for case in manifest.cases
        if (not ids or case.id in ids)
        and (not change_ids or case.change_id in change_ids)
        and (not tags or set(tags).issubset(case.tags))
    )
    if not selected:
        raise ConformanceError("empty-selection", "selectors matched no conformance cases")
    return selected


def materialize_case(
    case: ConformanceCase,
    repo_root: Path,
    sandbox: Path,
    *,
    second_pass: bool = False,
    previous_stdout: bytes | None = None,
) -> bytes | None:
    """Copy a case into an empty sandbox and return its exact stdin bytes, if any."""
    if not sandbox.is_dir() or any(sandbox.iterdir()):
        raise ConformanceError("invalid-sandbox", "case sandbox must be an empty directory")

    if case.kind == "stdin":
        if second_pass:
            if previous_stdout is None:
                raise ConformanceError(
                    "invalid-idempotence", f"case {case.id!r} has no first-pass stdout"
                )
            return previous_stdout
        if case.stdin is None:  # pragma: no cover - guarded by validation
            raise ConformanceError("invalid-kind-fields", f"case {case.id!r} has no stdin")
        return repo_root.joinpath(*case.stdin.parts).read_bytes()

    source_tree = case.after_tree if second_pass else case.before_tree
    if source_tree is None:  # pragma: no cover - guarded by validation
        raise ConformanceError("invalid-kind-fields", f"case {case.id!r} has no input tree")
    shutil.copytree(repo_root.joinpath(*source_tree.parts), sandbox, dirs_exist_ok=True)
    return None


def _snapshot_tree(root: Path) -> tuple[FileSnapshot, ...]:
    snapshots: list[FileSnapshot] = []
    for path in sorted(root.rglob("*")):
        relative = PurePosixPath(path.relative_to(root).as_posix())
        if path.is_symlink():
            raise ConformanceError("sandbox-entry", f"sandbox contains symlink {relative}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ConformanceError("sandbox-entry", f"sandbox contains non-file {relative}")
        snapshots.append(FileSnapshot(relative, path.read_bytes()))
    return tuple(snapshots)


def _expected_tree(case: ConformanceCase, repo_root: Path) -> tuple[FileSnapshot, ...]:
    if case.kind == "stdin":
        return ()
    if case.after_tree is None:  # pragma: no cover - guarded by validation
        raise ConformanceError("invalid-kind-fields", f"case {case.id!r} has no output tree")
    return _snapshot_tree(repo_root.joinpath(*case.after_tree.parts))


def _bounded_text(data: bytes) -> str:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = f"<binary {len(data)} bytes> {data[:2_048].hex()}"
    encoded = text.encode("utf-8")
    if len(encoded) <= MAX_DIAGNOSTIC_BYTES // 3:
        return text
    prefix = encoded[: MAX_DIAGNOSTIC_BYTES // 3].decode("utf-8", errors="replace")
    return f"{prefix}\n... <{len(encoded) - len(prefix.encode())} bytes omitted>"


def _bounded_diff(expected: bytes, actual: bytes) -> str:
    expected_text = _bounded_text(expected)
    actual_text = _bounded_text(actual)
    rendered = "".join(
        difflib.unified_diff(
            expected_text.splitlines(keepends=True),
            actual_text.splitlines(keepends=True),
            fromfile="expected",
            tofile="actual",
        )
    )
    if not rendered:
        rendered = f"expected {expected!r}\nactual   {actual!r}"
    encoded = rendered.encode("utf-8")
    if len(encoded) > MAX_DIAGNOSTIC_BYTES:
        rendered = (
            encoded[:MAX_DIAGNOSTIC_BYTES].decode("utf-8", errors="replace")
            + "\n... <diagnostic truncated>"
        )
    return rendered


def _failure(
    code: str,
    case: ConformanceCase,
    result: ProcessResult,
    detail: str,
) -> ConformanceError:
    command = " ".join(result.command)
    return ConformanceError(code, f"case {case.id!r}; command {command!r}\n{detail}")


def compare_result(case: ConformanceCase, result: ProcessResult, repo_root: Path) -> None:
    """Compare one raw process result with every committed expectation."""
    if result.exit_code != case.expected_exit:
        raise _failure(
            "exit-mismatch",
            case,
            result,
            f"expected exit {case.expected_exit}, got {result.exit_code}",
        )

    expected_stdout = repo_root.joinpath(*case.expected_stdout.parts).read_bytes()
    if result.stdout != expected_stdout:
        raise _failure(
            "stdout-mismatch", case, result, _bounded_diff(expected_stdout, result.stdout)
        )

    expected_stderr = repo_root.joinpath(*case.expected_stderr.parts).read_bytes()
    if result.stderr != expected_stderr:
        raise _failure(
            "stderr-mismatch", case, result, _bounded_diff(expected_stderr, result.stderr)
        )

    expected_tree = _expected_tree(case, repo_root)
    if result.tree != expected_tree:
        expected_paths = {file.path: file.content for file in expected_tree}
        actual_paths = {file.path: file.content for file in result.tree}
        missing = sorted(expected_paths.keys() - actual_paths.keys())
        extra = sorted(actual_paths.keys() - expected_paths.keys())
        changed = sorted(
            path
            for path in expected_paths.keys() & actual_paths.keys()
            if expected_paths[path] != actual_paths[path]
        )
        summary = f"missing={missing!r}; extra={extra!r}; changed={changed!r}"
        if changed:
            path = changed[0]
            summary += f"\n{path}:\n{_bounded_diff(expected_paths[path], actual_paths[path])}"
        raise _failure("file-tree-mismatch", case, result, summary)


def _environment(manifest: ConformanceManifest) -> dict[str, str]:
    environment = {name: os.environ[name] for name in ENV_ALLOWLIST if name in os.environ}
    environment.update(manifest.default_env)
    return environment


def _run_once(
    case: ConformanceCase,
    manifest: ConformanceManifest,
    executable: Path,
    repo_root: Path,
    timeout_seconds: float,
    *,
    second_pass: bool,
    previous_stdout: bytes | None,
) -> ProcessResult:
    with tempfile.TemporaryDirectory(prefix="flowmark-conformance-") as temporary:
        sandbox = Path(temporary)
        stdin = materialize_case(
            case,
            repo_root,
            sandbox,
            second_pass=second_pass,
            previous_stdout=previous_stdout,
        )
        command = (str(executable), *case.args)
        try:
            completed = subprocess.run(  # noqa: S603
                command,
                cwd=sandbox,
                env=_environment(manifest),
                input=stdin,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            raise ConformanceError(
                "timeout",
                f"case {case.id!r}; command {' '.join(command)!r} exceeded {timeout_seconds:g}s",
            ) from error
        return ProcessResult(
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
            tree=_snapshot_tree(sandbox),
        )


def run_case(
    case: ConformanceCase,
    manifest: ConformanceManifest,
    *,
    executable: Path,
    repo_root: Path,
    timeout_seconds: float = 30.0,
) -> tuple[ProcessResult, ...]:
    """Run, compare, and when requested repeat one case in fresh sandboxes."""
    executable = executable.resolve()
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ConformanceError("invalid-executable", f"not executable: {executable}")
    if timeout_seconds <= 0:
        raise ConformanceError("invalid-timeout", "timeout must be positive")

    first = _run_once(
        case,
        manifest,
        executable,
        repo_root,
        timeout_seconds,
        second_pass=False,
        previous_stdout=None,
    )
    compare_result(case, first, repo_root)
    results = [first]
    if case.idempotent:
        second = _run_once(
            case,
            manifest,
            executable,
            repo_root,
            timeout_seconds,
            second_pass=True,
            previous_stdout=first.stdout,
        )
        compare_result(case, second, repo_root)
        results.append(second)
    return tuple(results)
