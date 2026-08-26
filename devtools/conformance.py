from __future__ import annotations

import difflib
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from argparse import ArgumentParser
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal, cast

from strif import atomic_output_file

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
TOP_LEVEL_FIELDS = frozenset({"schema_version", "corpus", "defaults", "case_registry", "case"})
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
        encoded = message.encode("utf-8")
        if len(encoded) > MAX_DIAGNOSTIC_BYTES:
            message = (
                encoded[:MAX_DIAGNOSTIC_BYTES].decode("utf-8", errors="replace")
                + "\n... <diagnostic truncated>"
            )
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
class AcceptanceChange:
    """One exact golden-file addition, replacement, or deletion."""

    case_id: str
    path: PurePosixPath
    before: bytes | None
    after: bytes | None


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


def _validate_manifest(
    data: object, repo_root: Path, *, allow_case_registries: bool
) -> ConformanceManifest:
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

    raw_cases_value = root.get("case", [])
    if not isinstance(raw_cases_value, list):
        raise ConformanceError("invalid-type", "manifest.case must be an array")
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

    raw_registries_value = root.get("case_registry", [])
    if not isinstance(raw_registries_value, list):
        raise ConformanceError("invalid-type", "manifest.case_registry must be an array of strings")
    raw_registry_items = cast(list[object], raw_registries_value)
    if any(not isinstance(value, str) for value in raw_registry_items):
        raise ConformanceError("invalid-type", "manifest.case_registry must be an array of strings")
    raw_registries = cast(list[str], raw_registry_items)
    if raw_registries and not allow_case_registries:
        raise ConformanceError("nested-case-registry", "case registries cannot include registries")

    included_cases: list[ConformanceCase] = []
    seen_registries: set[PurePosixPath] = set()
    for index, raw_path in enumerate(raw_registries):
        location = f"manifest.case_registry[{index}]"
        path = _lexical_path(raw_path, location)
        _validate_existing_path(path, location, repo_root, "file")
        if path in seen_registries:
            raise ConformanceError("duplicate-case-registry", f"duplicate registry path {path}")
        seen_registries.add(path)
        registry_path = repo_root.joinpath(*path.parts)
        try:
            registry_data = tomllib.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
            raise ConformanceError(
                "invalid-case-registry", f"cannot load {registry_path}: {error}"
            ) from error
        registry = _validate_manifest(registry_data, repo_root, allow_case_registries=False)
        if registry.default_env:
            raise ConformanceError(
                "invalid-case-registry", f"included registry {path} cannot define defaults"
            )
        included_cases.extend(registry.cases)

    all_cases = (*cases, *included_cases)
    if not all_cases:
        raise ConformanceError("invalid-type", "manifest must define one or more cases")
    seen.clear()
    for case in all_cases:
        if case.id in seen:
            raise ConformanceError("duplicate-case-id", f"duplicate case ID {case.id!r}")
        seen.add(case.id)
    return ConformanceManifest(
        corpus=corpus, default_env=tuple(default_env), cases=tuple(all_cases)
    )


def validate_manifest(data: object, repo_root: Path) -> ConformanceManifest:
    """Validate parsed TOML and all root-relative case registries."""
    return _validate_manifest(data, repo_root.resolve(), allow_case_registries=True)


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

    explicitly_selected = bool(ids or change_ids or tags)
    selected = tuple(
        case
        for case in manifest.cases
        if (explicitly_selected or "deferred" not in case.tags)
        and (not ids or case.id in ids)
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
    previous_tree: tuple[FileSnapshot, ...] | None = None,
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

    if second_pass and previous_tree is not None:
        for snapshot in previous_tree:
            destination = sandbox.joinpath(*snapshot.path.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(snapshot.content)
        return None

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
    previous_tree: tuple[FileSnapshot, ...] | None,
) -> ProcessResult:
    with tempfile.TemporaryDirectory(prefix="flowmark-conformance-") as temporary:
        sandbox = Path(temporary)
        stdin = materialize_case(
            case,
            repo_root,
            sandbox,
            second_pass=second_pass,
            previous_stdout=previous_stdout,
            previous_tree=previous_tree,
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
        previous_tree=None,
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
            previous_tree=first.tree,
        )
        compare_result(case, second, repo_root)
        results.append(second)
    return tuple(results)


def _acceptance_changes(
    case: ConformanceCase,
    result: ProcessResult,
    repo_root: Path,
) -> tuple[AcceptanceChange, ...]:
    changes: list[AcceptanceChange] = []
    for path, after in (
        (case.expected_stdout, result.stdout),
        (case.expected_stderr, result.stderr),
    ):
        before = repo_root.joinpath(*path.parts).read_bytes()
        if before != after:
            changes.append(AcceptanceChange(case.id, path, before, after))

    if case.kind == "files":
        if case.after_tree is None:  # pragma: no cover - guarded by validation
            raise ConformanceError("invalid-kind-fields", f"case {case.id!r} has no output tree")
        expected = {snapshot.path: snapshot.content for snapshot in _expected_tree(case, repo_root)}
        actual = {snapshot.path: snapshot.content for snapshot in result.tree}
        for relative in sorted(expected.keys() | actual.keys()):
            before = expected.get(relative)
            after = actual.get(relative)
            if before != after:
                changes.append(
                    AcceptanceChange(
                        case.id,
                        case.after_tree / relative,
                        before,
                        after,
                    )
                )
    return tuple(changes)


def _complete_diff(change: AcceptanceChange) -> str:
    before = change.before or b""
    after = change.after or b""
    before_name = change.path.as_posix() if change.before is not None else "/dev/null"
    after_name = change.path.as_posix() if change.after is not None else "/dev/null"
    metadata = (
        f"before: {len(before)} bytes sha256={hashlib.sha256(before).hexdigest()}\n"
        f"after:  {len(after)} bytes sha256={hashlib.sha256(after).hexdigest()}\n"
    )
    try:
        before_text = before.decode("utf-8")
        after_text = after.decode("utf-8")
    except UnicodeDecodeError:
        return metadata + (
            f"--- {before_name}\n+++ {after_name}\n"
            f"-<binary {len(before)} bytes> {before.hex()}\n"
            f"+<binary {len(after)} bytes> {after.hex()}\n"
        )
    return metadata + "".join(
        difflib.unified_diff(
            before_text.splitlines(keepends=True),
            after_text.splitlines(keepends=True),
            fromfile=before_name,
            tofile=after_name,
        )
    )


def _write_acceptance_changes(changes: tuple[AcceptanceChange, ...], repo_root: Path) -> None:
    for change in changes:
        destination = repo_root.joinpath(*change.path.parts)
        if change.after is None:
            destination.unlink()
            continue
        with atomic_output_file(destination, make_parents=True) as temporary:
            Path(temporary).write_bytes(change.after)


def accept_cases(
    manifest: ConformanceManifest,
    *,
    case_ids: tuple[str, ...],
    executable: Path,
    repo_root: Path,
    timeout_seconds: float = 30.0,
    write: bool = False,
) -> tuple[AcceptanceChange, ...]:
    """Preview and optionally write goldens for one or more exact case IDs."""
    if not case_ids or any(not case_id for case_id in case_ids):
        raise ConformanceError(
            "exact-case-ids-required", "acceptance requires one or more exact case IDs"
        )
    if len(set(case_ids)) != len(case_ids):
        raise ConformanceError("duplicate-selector", "acceptance case IDs must be unique")
    selected = select_cases(manifest, ids=case_ids)
    if len(selected) != len(case_ids):  # pragma: no cover - exact selection guarantees this
        raise ConformanceError("unknown-selector", "an acceptance case ID was not selected")

    executable = executable.resolve()
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ConformanceError("invalid-executable", f"not executable: {executable}")
    if timeout_seconds <= 0:
        raise ConformanceError("invalid-timeout", "timeout must be positive")

    by_path: dict[PurePosixPath, AcceptanceChange] = {}
    for case in selected:
        first = _run_once(
            case,
            manifest,
            executable,
            repo_root,
            timeout_seconds,
            second_pass=False,
            previous_stdout=None,
            previous_tree=None,
        )
        if first.exit_code != case.expected_exit:
            raise _failure(
                "unacceptable-exit",
                case,
                first,
                "exit status is manifest metadata and must be reviewed manually",
            )
        if case.idempotent:
            second = _run_once(
                case,
                manifest,
                executable,
                repo_root,
                timeout_seconds,
                second_pass=True,
                previous_stdout=first.stdout,
                previous_tree=first.tree,
            )
            if (
                second.stdout,
                second.stderr,
                second.exit_code,
                second.tree,
            ) != (
                first.stdout,
                first.stderr,
                first.exit_code,
                first.tree,
            ):
                raise _failure(
                    "idempotence-mismatch",
                    case,
                    second,
                    "candidate golden output does not reach a fixed point",
                )

        for change in _acceptance_changes(case, first, repo_root):
            previous = by_path.get(change.path)
            if previous is not None and previous.after != change.after:
                raise ConformanceError(
                    "golden-conflict",
                    f"cases {previous.case_id!r} and {case.id!r} propose different bytes for "
                    f"{change.path}",
                )
            by_path[change.path] = change

    changes = tuple(by_path[path] for path in sorted(by_path))
    if not changes:
        print("No golden changes proposed.")
        return ()
    for change in changes:
        print(f"case {change.case_id}: {change.path}")
        diff = _complete_diff(change)
        sys.stdout.write(diff)
        if not diff.endswith("\n"):
            print()
    if write:
        _write_acceptance_changes(changes, repo_root)
        print(f"Wrote {len(changes)} selected golden file change(s).")
    else:
        print("Preview only; no golden files were written.")
    return changes


def _case_payload_reference_counts(
    manifest: ConformanceManifest, repo_root: Path
) -> Counter[PurePosixPath]:
    references: Counter[PurePosixPath] = Counter()
    for case in manifest.cases:
        for path in (case.expected_stdout, case.expected_stderr, case.stdin):
            if path is not None and path.as_posix().startswith("tests/parity_corpus/cases/"):
                references[path] += 1
        for tree in (case.before_tree, case.after_tree):
            if tree is None or not tree.as_posix().startswith("tests/parity_corpus/cases/"):
                continue
            root = repo_root.joinpath(*tree.parts)
            for descendant in root.rglob("*"):
                if descendant.is_file() and not descendant.is_symlink():
                    relative = PurePosixPath(descendant.relative_to(repo_root).as_posix())
                    references[relative] += 1
    return references


def _validate_case_payload_reachability(manifest: ConformanceManifest, repo_root: Path) -> None:
    cases_root = repo_root / "tests/parity_corpus/cases"
    if not cases_root.is_dir():
        raise ConformanceError("missing-path", f"missing parity case directory: {cases_root}")
    payloads: set[PurePosixPath] = set()
    for path in cases_root.rglob("*"):
        relative = PurePosixPath(path.relative_to(repo_root).as_posix())
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise ConformanceError("invalid-corpus-entry", f"invalid parity payload: {relative}")
        if path.is_file():
            payloads.add(relative)

    references = _case_payload_reference_counts(manifest, repo_root)
    multiply_referenced = sorted(path for path, count in references.items() if count != 1)
    if multiply_referenced:
        path = multiply_referenced[0]
        raise ConformanceError(
            "multiply-referenced-payload",
            f"{path} is reached {references[path]} times; expected exactly once",
        )
    unreachable = sorted(payloads - references.keys())
    if unreachable:
        raise ConformanceError(
            "unreachable-payload", f"parity payload is not in the manifest: {unreachable[0]}"
        )


def _topic_deferred_paths(repo_root: Path) -> set[PurePosixPath]:
    registry_path = repo_root / "tests/tryscript/fixtures/topic-fixtures.toml"
    try:
        data = tomllib.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ConformanceError("invalid-topic-registry", str(error)) from error
    root = _mapping(data, "topic registry")
    _unknown_fields(root, frozenset({"schema_version", "deferred"}), "topic registry")
    if _integer(root, "schema_version", "topic registry") != 1:
        raise ConformanceError("unsupported-topic-registry", "topic registry version must be 1")
    raw_entries_value = root.get("deferred", [])
    if not isinstance(raw_entries_value, list):
        raise ConformanceError("invalid-topic-registry", "deferred must be an array")

    deferred: set[PurePosixPath] = set()
    for index, value in enumerate(cast(list[object], raw_entries_value)):
        location = f"deferred[{index}]"
        entry = _mapping(value, location)
        _unknown_fields(entry, frozenset({"path", "owner", "reason"}), location)
        raw_path = _string(entry, "path", location)
        owner = _string(entry, "owner", location)
        _string(entry, "reason", location)
        expected_prefix = "tests/tryscript/fixtures/content/"
        if (
            not raw_path.startswith(expected_prefix)
            or "/" in raw_path.removeprefix(expected_prefix)
            or re.fullmatch(r"fm-[a-z0-9]+", owner) is None
        ):
            raise ConformanceError("invalid-topic-registry", f"invalid {location}")
        path = PurePosixPath(raw_path)
        if path in deferred:
            raise ConformanceError("duplicate-topic-fixture", f"duplicate deferred path {path}")
        candidate = repo_root.joinpath(*path.parts)
        if not candidate.is_file() or candidate.is_symlink():
            raise ConformanceError("missing-topic-fixture", f"deferred fixture is missing: {path}")
        deferred.add(path)
    return deferred


def _validate_topic_reachability(repo_root: Path) -> None:
    topic_root = repo_root / "tests/tryscript/fixtures/content"
    if not topic_root.is_dir():
        raise ConformanceError("missing-path", f"missing topic fixture directory: {topic_root}")
    deferred = _topic_deferred_paths(repo_root)
    reference_text = (repo_root / "tests/parity_corpus/manifest.toml").read_text(encoding="utf-8")
    for script in sorted((repo_root / "tests/tryscript").glob("*.tryscript.md")):
        reference_text += script.read_text(encoding="utf-8")

    topics: set[PurePosixPath] = set()
    for path in topic_root.iterdir():
        relative = PurePosixPath(path.relative_to(repo_root).as_posix())
        if path.is_symlink() or not path.is_file():
            raise ConformanceError("invalid-topic-fixture", f"invalid topic entry: {relative}")
        topics.add(relative)
    for topic in sorted(topics):
        short_path = topic.as_posix().removeprefix("tests/tryscript/")
        referenced = short_path in reference_text or topic.as_posix() in reference_text
        is_deferred = topic in deferred
        if referenced and is_deferred:
            raise ConformanceError(
                "stale-topic-deferral", f"referenced topic remains deferred: {topic}"
            )
        if not referenced and not is_deferred:
            raise ConformanceError("unreachable-topic", f"topic fixture is dead: {topic}")

    unknown = sorted(deferred - topics)
    if unknown:  # pragma: no cover - existence validation catches this first
        raise ConformanceError(
            "missing-topic-fixture", f"deferred fixture is missing: {unknown[0]}"
        )


def _validate_portable_test_definitions(repo_root: Path) -> None:
    implementation_path = re.compile(
        r"\.venv/bin|target/(?:debug|release)|python(?:\s+-m)?\s+flowmark|"
        r"uv\s+run\s+flowmark"
    )
    definitions = [repo_root / "tests/parity_corpus/manifest.toml"]
    definitions.extend(sorted((repo_root / "tests/tryscript").glob("*.tryscript.md")))
    for path in definitions:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if implementation_path.search(line):
                relative = path.relative_to(repo_root)
                raise ConformanceError(
                    "implementation-path",
                    f"{relative}:{line_number} embeds an implementation-specific executable",
                )


def _validate_case_deferrals(manifest: ConformanceManifest, repo_root: Path) -> None:
    """Require explicit ownership and desired source bytes for deferred shared cases."""
    for case in manifest.cases:
        owner_tags = tuple(tag for tag in case.tags if tag.startswith("owner-fm-"))
        if "deferred" not in case.tags:
            if owner_tags:
                raise ConformanceError(
                    "invalid-deferral",
                    f"active case {case.id!r} has a deferred owner tag",
                )
            continue
        if len(owner_tags) != 1:
            raise ConformanceError(
                "invalid-deferral",
                f"deferred case {case.id!r} must have exactly one owner-fm-* tag",
            )
        if "commonmark" in case.tags:
            if case.stdin is None:
                raise ConformanceError(
                    "invalid-deferral", f"deferred CommonMark case {case.id!r} must use stdin"
                )
            source = repo_root.joinpath(*case.stdin.parts).read_bytes()
            expected = repo_root.joinpath(*case.expected_stdout.parts).read_bytes()
            if source != expected:
                raise ConformanceError(
                    "invalid-deferral",
                    f"deferred CommonMark case {case.id!r} must preserve source bytes",
                )


def check_conformance_coverage(repo_root: Path, *, check_topics: bool = True) -> None:
    """Validate schema, exact case-payload reachability, and shared-test portability."""
    repo_root = repo_root.resolve()
    manifest = load_manifest(repo_root / "tests/parity_corpus/manifest.toml", repo_root)
    _validate_case_deferrals(manifest, repo_root)
    _validate_case_payload_reachability(manifest, repo_root)
    if check_topics:
        _validate_topic_reachability(repo_root)
        _validate_portable_test_definitions(repo_root)


def _add_run_arguments(parser: ArgumentParser) -> None:
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, default=Path("tests/parity_corpus/manifest.toml"))
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=30.0)


def _resolve_from_root(path: Path, repo_root: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def main(argv: list[str] | None = None) -> int:
    """Run the read-only conformance checks or explicit selected acceptance."""
    parser = ArgumentParser(description="Run Flowmark's language-neutral conformance corpus.")
    commands = parser.add_subparsers(dest="command", required=True)

    run_parser = commands.add_parser("run", help="Run and compare selected corpus cases.")
    _add_run_arguments(run_parser)
    run_parser.add_argument("--case", action="append", default=[])
    run_parser.add_argument("--change-id", action="append", default=[])
    run_parser.add_argument("--tag", action="append", default=[])

    accept_parser = commands.add_parser(
        "accept", help="Preview or write selected case golden files."
    )
    _add_run_arguments(accept_parser)
    accept_parser.add_argument(
        "--case-ids", required=True, help="Comma-separated exact case IDs; never a pattern."
    )
    accept_parser.add_argument("--write", action="store_true")

    coverage_parser = commands.add_parser(
        "coverage", help="Validate manifest, payload, fixture, and portability coverage."
    )
    coverage_parser.add_argument("--repo-root", type=Path, default=Path.cwd())

    arguments = parser.parse_args(argv)
    repo_root = cast(Path, arguments.repo_root).resolve()
    try:
        if arguments.command == "coverage":
            check_conformance_coverage(repo_root)
            print("Conformance schema and reachability checks passed.")
            return 0

        manifest_path = _resolve_from_root(cast(Path, arguments.manifest), repo_root)
        manifest = load_manifest(manifest_path, repo_root)
        executable = cast(Path, arguments.executable)
        timeout = cast(float, arguments.timeout)
        if arguments.command == "run":
            cases = select_cases(
                manifest,
                ids=tuple(cast(list[str], arguments.case)),
                change_ids=tuple(cast(list[str], arguments.change_id)),
                tags=tuple(cast(list[str], arguments.tag)),
            )
            for case in cases:
                passes = run_case(
                    case,
                    manifest,
                    executable=executable,
                    repo_root=repo_root,
                    timeout_seconds=timeout,
                )
                print(f"PASS {case.id} ({len(passes)} pass{'es' if len(passes) != 1 else ''})")
            return 0

        raw_case_ids = cast(str, arguments.case_ids)
        case_ids = tuple(raw_case_ids.split(",")) if raw_case_ids else ()
        accept_cases(
            manifest,
            case_ids=case_ids,
            executable=executable,
            repo_root=repo_root,
            timeout_seconds=timeout,
            write=cast(bool, arguments.write),
        )
        return 0
    except ConformanceError as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
