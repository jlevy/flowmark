from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path, PurePosixPath

import pytest

from devtools.conformance import (
    ConformanceError,
    FileSnapshot,
    ProcessResult,
    compare_result,
    load_manifest,
    materialize_case,
    run_case,
    select_cases,
)

if sys.version_info >= (3, 11):
    import tomllib  # pyright: ignore[reportUnreachable]
else:
    import tomli as tomllib  # type: ignore[no-redef]  # pyright: ignore[reportUnreachable]


REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = REPO_ROOT / "tests/parity_corpus"


def _installed_flowmark() -> Path:
    executable = Path(sys.executable).with_name("flowmark")
    assert executable.is_file()
    return executable


def test_shared_manifest_validates() -> None:
    manifest = load_manifest(CORPUS_ROOT / "manifest.toml", REPO_ROOT)

    assert [case.id for case in manifest.cases] == [
        "cli.stdin.wrap",
        "cli.files.inplace-backup",
    ]


def test_shared_invalid_manifest_fixtures_have_stable_error_codes() -> None:
    fixture_index = tomllib.loads(
        (CORPUS_ROOT / "runner-fixtures/manifest.toml").read_text(encoding="utf-8")
    )

    fixtures = [
        fixture for fixture in fixture_index["fixture"] if fixture["outcome"] == "manifest-error"
    ]
    assert fixtures
    for fixture in fixtures:
        try:
            load_manifest(REPO_ROOT / fixture["manifest"], REPO_ROOT)
        except ConformanceError as error:
            assert error.code == fixture["code"], fixture["id"]
        else:
            raise AssertionError(f"{fixture['id']} unexpectedly validated")


def test_case_selection_uses_exact_filters_and_rejects_unknown_values() -> None:
    manifest = load_manifest(CORPUS_ROOT / "manifest.toml", REPO_ROOT)

    assert [
        case.id
        for case in select_cases(
            manifest,
            ids=("cli.stdin.wrap",),
            change_ids=("FM-CONFORMANCE-001",),
            tags=("stdin", "cli"),
        )
    ] == ["cli.stdin.wrap"]

    for filters in (
        {"ids": ("cli.stdin",)},
        {"change_ids": ("FM-CONFORMANCE",)},
        {"tags": ("std",)},
    ):
        try:
            select_cases(manifest, **filters)
        except ConformanceError as error:
            assert error.code == "unknown-selector"
        else:
            raise AssertionError(f"selector {filters!r} unexpectedly matched")


def test_seed_cases_run_against_the_installed_cli() -> None:
    manifest = load_manifest(CORPUS_ROOT / "manifest.toml", REPO_ROOT)

    pass_counts = [
        len(
            run_case(
                case,
                manifest,
                executable=_installed_flowmark(),
                repo_root=REPO_ROOT,
            )
        )
        for case in manifest.cases
    ]

    assert pass_counts == [2, 1]


def test_shared_intentional_failures_have_bounded_diagnostics() -> None:
    fixture_index = tomllib.loads(
        (CORPUS_ROOT / "runner-fixtures/manifest.toml").read_text(encoding="utf-8")
    )

    fixtures = [
        fixture for fixture in fixture_index["fixture"] if fixture["outcome"] == "case-failure"
    ]
    assert fixtures
    for fixture in fixtures:
        manifest = load_manifest(REPO_ROOT / fixture["manifest"], REPO_ROOT)
        with pytest.raises(ConformanceError) as caught:
            run_case(
                manifest.cases[0],
                manifest,
                executable=_installed_flowmark(),
                repo_root=REPO_ROOT,
            )

        assert caught.value.code == fixture["code"], fixture["id"]
        assert manifest.cases[0].id in str(caught.value)
        assert len(str(caught.value).encode()) <= 16_384


def test_materialization_and_execution_preserve_invalid_utf8_bytes(tmp_path: Path) -> None:
    manifest = load_manifest(CORPUS_ROOT / "manifest.toml", REPO_ROOT)
    relative_input = PurePosixPath("tests/parity_corpus/cases/invalid-utf8.bin")
    relative_stderr = PurePosixPath("tests/parity_corpus/cases/empty.stderr")
    input_path = tmp_path.joinpath(*relative_input.parts)
    input_path.parent.mkdir(parents=True)
    input_path.write_bytes(b"before\xffafter\r\n")
    tmp_path.joinpath(*relative_stderr.parts).write_bytes(b"")
    case = replace(
        manifest.cases[0],
        args=("-",),
        stdin=relative_input,
        expected_stdout=relative_input,
        expected_stderr=relative_stderr,
    )
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    executable = tmp_path / "byte-echo"
    executable.write_text(
        f"#!{sys.executable}\nimport sys\nsys.stdout.buffer.write(sys.stdin.buffer.read())\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)

    assert materialize_case(case, tmp_path, sandbox) == b"before\xffafter\r\n"
    assert len(run_case(case, manifest, executable=executable, repo_root=tmp_path)) == 2


def test_complete_file_tree_comparison_rejects_an_extra_file() -> None:
    manifest = load_manifest(CORPUS_ROOT / "manifest.toml", REPO_ROOT)
    case = manifest.cases[1]
    result = ProcessResult(
        command=(str(_installed_flowmark()), *case.args),
        stdout=b"",
        stderr=b"",
        exit_code=0,
        tree=(FileSnapshot(PurePosixPath("unexpected.md"), b"surprise\n"),),
    )

    with pytest.raises(ConformanceError) as caught:
        compare_result(case, result, REPO_ROOT)

    assert caught.value.code == "file-tree-mismatch"


def test_case_timeout_has_a_stable_failure_code(tmp_path: Path) -> None:
    executable = tmp_path / "slow-flowmark"
    executable.write_text(f"#!{sys.executable}\nimport time\ntime.sleep(5)\n", encoding="utf-8")
    executable.chmod(0o755)
    manifest = load_manifest(CORPUS_ROOT / "manifest.toml", REPO_ROOT)

    with pytest.raises(ConformanceError) as caught:
        run_case(
            manifest.cases[0],
            manifest,
            executable=executable,
            repo_root=REPO_ROOT,
            timeout_seconds=0.05,
        )

    assert caught.value.code == "timeout"
    assert manifest.cases[0].id in str(caught.value)
