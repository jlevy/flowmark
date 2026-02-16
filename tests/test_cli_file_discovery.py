"""CLI integration tests for file discovery."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from flowmark.cli import main


def _make_tree(root: Path) -> None:
    """Create a minimal project directory tree for testing."""
    (root / "README.md").write_text("# Root\n")
    docs = root / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Guide\n")
    (docs / "api.md").write_text("# API\n")
    (root / "code.py").write_text("print('hello')\n")
    nm = root / "node_modules" / "pkg"
    nm.mkdir(parents=True)
    (nm / "README.md").write_text("# Should be excluded\n")
    venv = root / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "README.md").write_text("# Should be excluded\n")


def test_list_files_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_tree(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert main(["--list-files", "."]) == 0
    out = capsys.readouterr().out
    names = sorted(Path(line).name for line in out.strip().split("\n") if line)
    assert names == ["README.md", "api.md", "guide.md"]


def test_list_files_skips_excluded_dirs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_tree(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert main(["--list-files", "."]) == 0
    out = capsys.readouterr().out
    assert "node_modules" not in out
    assert ".venv" not in out


def test_list_files_extend_include(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_tree(tmp_path)
    (tmp_path / "page.mdx").write_text("# MDX page\n")
    monkeypatch.chdir(tmp_path)
    assert main(["--list-files", "--extend-include", "*.mdx", "."]) == 0
    out = capsys.readouterr().out
    assert "page.mdx" in out


def test_list_files_extend_exclude(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_tree(tmp_path)
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "wip.md").write_text("# WIP\n")
    monkeypatch.chdir(tmp_path)
    assert main(["--list-files", "--extend-exclude", "drafts/", "."]) == 0
    out = capsys.readouterr().out
    assert "drafts" not in out
    assert "README.md" in out


def test_list_files_no_respect_gitignore(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "keep.md").write_text("# Keep\n")
    (tmp_path / ".gitignore").write_text("ignored/\n")
    ignored = tmp_path / "ignored"
    ignored.mkdir()
    (ignored / "found.md").write_text("# Found\n")
    monkeypatch.chdir(tmp_path)
    assert main(["--list-files", "--no-respect-gitignore", "."]) == 0
    out = capsys.readouterr().out
    assert "found.md" in out


def test_list_files_force_exclude(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    nm = tmp_path / "node_modules"
    nm.mkdir()
    (nm / "README.md").write_text("# Excluded\n")
    monkeypatch.chdir(tmp_path)
    assert main(["--list-files", "--force-exclude", str(nm / "README.md")]) == 0
    out = capsys.readouterr().out
    assert out.strip() == ""


def test_list_files_max_size(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "small.md").write_text("# Small\n")
    (tmp_path / "large.md").write_text("x" * 2_000_000)
    monkeypatch.chdir(tmp_path)
    assert main(["--list-files", "--files-max-size", "100", "."]) == 0
    out = capsys.readouterr().out
    assert "small.md" in out
    assert "large.md" not in out


def test_auto_no_args_defaults_to_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "test.md").write_text("# Test\n\nSome text here.\n")
    monkeypatch.chdir(tmp_path)
    assert main(["--auto"]) == 0
    content = (tmp_path / "test.md").read_text()
    assert "# Test" in content


def test_explicit_file_still_works(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    f = tmp_path / "test.md"
    f.write_text("# Hello World\n")
    assert main([str(f)]) == 0
    out = capsys.readouterr().out
    assert "# Hello World" in out


def test_stdin_still_works(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("# From stdin\n"))
    assert main(["-"]) == 0
    out = capsys.readouterr().out
    assert "# From stdin" in out


def test_auto_with_explicit_file(tmp_path: Path) -> None:
    f = tmp_path / "README.md"
    f.write_text("# Test\n\nSome text.\n")
    assert main(["--auto", str(f)]) == 0
    content = f.read_text()
    assert "# Test" in content


def test_flowmarkignore(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "keep.md").write_text("# Keep\n")
    skip = tmp_path / "skip"
    skip.mkdir()
    (skip / "nope.md").write_text("# Nope\n")
    (tmp_path / ".flowmarkignore").write_text("skip/\n")
    monkeypatch.chdir(tmp_path)
    assert main(["--list-files", "."]) == 0
    out = capsys.readouterr().out
    assert "keep.md" in out
    assert "skip" not in out


def test_list_files_stdin_does_not_crash(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """--list-files with stdin arg should not raise FileNotFoundError (fm-1xaz)."""
    (tmp_path / "README.md").write_text("# Root\n")
    monkeypatch.chdir(tmp_path)
    # Passing '-' (stdin) together with a directory should not crash
    assert main(["--list-files", "-", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "README.md" in out


def test_explicit_flag_detection_with_default_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Passing --width 88 (the default) should still be detected as explicit (fm-4z3r)."""
    from flowmark.cli import _parse_args

    _, explicit_flags, _ = _parse_args(["--width", "88", str(tmp_path)])
    assert "width" in explicit_flags
