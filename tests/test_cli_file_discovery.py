"""CLI integration tests for file discovery."""

from __future__ import annotations

import os
from pathlib import Path

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


def test_list_files_directory(tmp_path: Path, capsys: object) -> None:
    _make_tree(tmp_path)
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        exit_code = main(["--list-files", "."])
    finally:
        os.chdir(old_cwd)
    assert exit_code == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    lines = sorted(line for line in out.strip().split("\n") if line)
    # Should find 3 .md files, not the ones in node_modules or .venv
    assert len(lines) == 3
    names = sorted(Path(line).name for line in lines)
    assert names == ["README.md", "api.md", "guide.md"]


def test_list_files_skips_excluded_dirs(tmp_path: Path, capsys: object) -> None:
    _make_tree(tmp_path)
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        exit_code = main(["--list-files", "."])
    finally:
        os.chdir(old_cwd)
    assert exit_code == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    assert "node_modules" not in out
    assert ".venv" not in out


def test_list_files_extend_include(tmp_path: Path, capsys: object) -> None:
    _make_tree(tmp_path)
    (tmp_path / "page.mdx").write_text("# MDX page\n")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        exit_code = main(["--list-files", "--extend-include", "*.mdx", "."])
    finally:
        os.chdir(old_cwd)
    assert exit_code == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    assert "page.mdx" in out


def test_list_files_extend_exclude(tmp_path: Path, capsys: object) -> None:
    _make_tree(tmp_path)
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "wip.md").write_text("# WIP\n")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        exit_code = main(["--list-files", "--extend-exclude", "drafts/", "."])
    finally:
        os.chdir(old_cwd)
    assert exit_code == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    assert "drafts" not in out
    assert "README.md" in out


def test_list_files_no_respect_gitignore(tmp_path: Path, capsys: object) -> None:
    (tmp_path / "keep.md").write_text("# Keep\n")
    (tmp_path / ".gitignore").write_text("ignored/\n")
    ignored = tmp_path / "ignored"
    ignored.mkdir()
    (ignored / "found.md").write_text("# Found\n")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        exit_code = main(["--list-files", "--no-respect-gitignore", "."])
    finally:
        os.chdir(old_cwd)
    assert exit_code == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    assert "found.md" in out


def test_list_files_force_exclude(tmp_path: Path, capsys: object) -> None:
    nm = tmp_path / "node_modules"
    nm.mkdir()
    (nm / "README.md").write_text("# Excluded\n")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        exit_code = main(["--list-files", "--force-exclude", str(nm / "README.md")])
    finally:
        os.chdir(old_cwd)
    assert exit_code == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    assert out.strip() == ""


def test_list_files_max_size(tmp_path: Path, capsys: object) -> None:
    (tmp_path / "small.md").write_text("# Small\n")
    (tmp_path / "large.md").write_text("x" * 2_000_000)
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        exit_code = main(["--list-files", "--files-max-size", "100", "."])
    finally:
        os.chdir(old_cwd)
    assert exit_code == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    assert "small.md" in out
    assert "large.md" not in out


def test_auto_no_args_defaults_to_cwd(tmp_path: Path) -> None:
    """flowmark --auto (no file args) should default to formatting '.'"""
    (tmp_path / "test.md").write_text("# Test\n\nSome text here.\n")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        exit_code = main(["--auto"])
    finally:
        os.chdir(old_cwd)
    assert exit_code == 0
    # File should still exist and be valid markdown
    content = (tmp_path / "test.md").read_text()
    assert "# Test" in content


def test_explicit_file_still_works(tmp_path: Path, capsys: object) -> None:
    """Backward compat: explicit file argument works exactly like before."""
    f = tmp_path / "test.md"
    f.write_text("# Hello World\n")
    exit_code = main([str(f)])
    assert exit_code == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    assert "# Hello World" in out


def test_stdin_still_works(tmp_path: Path, capsys: object, monkeypatch: object) -> None:
    """Backward compat: stdin piping still works."""
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO("# From stdin\n"))  # type: ignore[union-attr]
    exit_code = main(["-"])
    assert exit_code == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    assert "# From stdin" in out


def test_auto_with_explicit_file(tmp_path: Path) -> None:
    """flowmark --auto README.md should still work (backward compat)."""
    f = tmp_path / "README.md"
    f.write_text("# Test\n\nSome text.\n")
    exit_code = main(["--auto", str(f)])
    assert exit_code == 0
    content = f.read_text()
    assert "# Test" in content


def test_flowmarkignore(tmp_path: Path, capsys: object) -> None:
    (tmp_path / "keep.md").write_text("# Keep\n")
    skip = tmp_path / "skip"
    skip.mkdir()
    (skip / "nope.md").write_text("# Nope\n")
    (tmp_path / ".flowmarkignore").write_text("skip/\n")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        exit_code = main(["--list-files", "."])
    finally:
        os.chdir(old_cwd)
    assert exit_code == 0
    out = capsys.readouterr().out  # type: ignore[union-attr]
    assert "keep.md" in out
    assert "skip" not in out
