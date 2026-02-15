"""Tests for the file_resolver module."""

from __future__ import annotations

from pathlib import Path

from flowmark.file_resolver import (
    DEFAULT_EXCLUDES,
    FileResolver,
    FileResolverConfig,
)


def test_config_effective_include():
    config = FileResolverConfig(extend_include=["*.markdown", "*.mdx"])
    assert config.effective_include == ["*.md", "*.markdown", "*.mdx"]


def test_config_effective_include_custom_base():
    config = FileResolverConfig(include=["*.txt"], extend_include=["*.rst"])
    assert config.effective_include == ["*.txt", "*.rst"]


def test_config_effective_exclude_replaced():
    config = FileResolverConfig(exclude=["custom_dir/"])
    assert config.effective_exclude == ["custom_dir/"]


def test_config_effective_exclude_extended():
    config = FileResolverConfig(extend_exclude=["extra_dir/"])
    effective = config.effective_exclude
    assert "extra_dir/" in effective
    for pattern in DEFAULT_EXCLUDES:
        assert pattern in effective


def test_resolver_single_file(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text("# Hello")

    resolver = FileResolver(FileResolverConfig())
    result = resolver.resolve([str(readme)])
    assert result == [readme]


def test_resolver_directory_recursion(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Root")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Guide")
    (docs / "api.md").write_text("# API")
    (tmp_path / "code.py").write_text("# not markdown")

    resolver = FileResolver(FileResolverConfig())
    result = resolver.resolve([str(tmp_path)])
    names = sorted(p.name for p in result)
    assert names == ["README.md", "api.md", "guide.md"]


def test_resolver_excludes_default_dirs(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Root")
    nm = tmp_path / "node_modules" / "pkg"
    nm.mkdir(parents=True)
    (nm / "README.md").write_text("# Should be excluded")
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "README.md").write_text("# Should be excluded")

    resolver = FileResolver(FileResolverConfig())
    result = resolver.resolve([str(tmp_path)])
    assert len(result) == 1
    assert result[0].name == "README.md"


def test_resolver_respects_gitignore(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Root")
    (tmp_path / ".gitignore").write_text("build/\n")
    build = tmp_path / "build"
    build.mkdir()
    (build / "output.md").write_text("# Should be excluded by gitignore")

    resolver = FileResolver(FileResolverConfig())
    result = resolver.resolve([str(tmp_path)])
    assert len(result) == 1
    assert result[0].name == "README.md"


def test_resolver_no_respect_gitignore(tmp_path: Path):
    (tmp_path / "good.md").write_text("# Good")
    (tmp_path / ".gitignore").write_text("ignored/\n")
    ignored = tmp_path / "ignored"
    ignored.mkdir()
    (ignored / "found.md").write_text("# Found when gitignore disabled")

    resolver = FileResolver(FileResolverConfig(respect_gitignore=False))
    result = resolver.resolve([str(tmp_path)])
    names = sorted(p.name for p in result)
    assert names == ["found.md", "good.md"]


def test_resolver_force_exclude_filters_explicit_files(tmp_path: Path):
    nm = tmp_path / "node_modules"
    nm.mkdir()
    excluded_file = nm / "README.md"
    excluded_file.write_text("# Excluded")

    resolver = FileResolver(FileResolverConfig(force_exclude=True))
    result = resolver.resolve([str(excluded_file)])
    assert result == []


def test_resolver_explicit_files_bypass_exclusions_by_default(tmp_path: Path):
    nm = tmp_path / "node_modules"
    nm.mkdir()
    excluded_file = nm / "README.md"
    excluded_file.write_text("# Excluded dir but explicit file")

    resolver = FileResolver(FileResolverConfig(force_exclude=False))
    result = resolver.resolve([str(excluded_file)])
    assert result == [excluded_file]


def test_resolver_extend_include(tmp_path: Path):
    (tmp_path / "readme.md").write_text("# MD")
    (tmp_path / "page.mdx").write_text("# MDX")
    (tmp_path / "code.py").write_text("# Not included")

    resolver = FileResolver(FileResolverConfig(extend_include=["*.mdx"]))
    result = resolver.resolve([str(tmp_path)])
    names = sorted(p.name for p in result)
    assert names == ["page.mdx", "readme.md"]


def test_resolver_exclude_replaces_defaults(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Root")
    # node_modules would normally be excluded by defaults
    nm = tmp_path / "node_modules"
    nm.mkdir()
    (nm / "README.md").write_text("# In node_modules")
    # custom_dir will be the only exclusion
    custom = tmp_path / "custom_dir"
    custom.mkdir()
    (custom / "README.md").write_text("# In custom_dir")

    resolver = FileResolver(FileResolverConfig(exclude=["custom_dir/"]))
    result = resolver.resolve([str(tmp_path)])
    names = sorted(p.name for p in result)
    # node_modules should NOT be excluded (defaults replaced)
    # custom_dir should be excluded
    assert names == ["README.md", "README.md"]
    paths = sorted(str(p) for p in result)
    assert any("node_modules" in p for p in paths)
    assert not any("custom_dir" in p for p in paths)


def test_resolver_extend_exclude(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Root")
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "wip.md").write_text("# WIP")

    resolver = FileResolver(FileResolverConfig(extend_exclude=["drafts/"]))
    result = resolver.resolve([str(tmp_path)])
    assert len(result) == 1
    assert result[0].name == "README.md"


def test_resolver_files_max_size(tmp_path: Path):
    small = tmp_path / "small.md"
    small.write_text("# Small")
    large = tmp_path / "large.md"
    large.write_text("x" * 2_000_000)

    resolver = FileResolver(FileResolverConfig(files_max_size=1_048_576))
    result = resolver.resolve([str(tmp_path)])
    assert len(result) == 1
    assert result[0].name == "small.md"


def test_resolver_files_max_size_zero_disables(tmp_path: Path):
    large = tmp_path / "large.md"
    large.write_text("x" * 2_000_000)

    resolver = FileResolver(FileResolverConfig(files_max_size=0))
    result = resolver.resolve([str(tmp_path)])
    assert len(result) == 1


def test_resolver_glob_pattern(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# A")
    (docs / "b.md").write_text("# B")
    (docs / "c.txt").write_text("not md")

    resolver = FileResolver(FileResolverConfig())
    result = resolver.resolve([str(docs / "*.md")])
    names = sorted(p.name for p in result)
    assert names == ["a.md", "b.md"]


def test_resolver_mixed_inputs(tmp_path: Path):
    (tmp_path / "explicit.md").write_text("# Explicit")
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "found.md").write_text("# Found")

    resolver = FileResolver(FileResolverConfig())
    result = resolver.resolve([str(tmp_path / "explicit.md"), str(subdir)])
    names = sorted(p.name for p in result)
    assert names == ["explicit.md", "found.md"]


def test_resolver_deduplication(tmp_path: Path):
    f = tmp_path / "README.md"
    f.write_text("# Hello")

    resolver = FileResolver(FileResolverConfig())
    result = resolver.resolve([str(f), str(f), str(tmp_path)])
    assert len(result) == 1


def test_resolver_sorted_output(tmp_path: Path):
    for name in ["c.md", "a.md", "b.md"]:
        (tmp_path / name).write_text(f"# {name}")

    resolver = FileResolver(FileResolverConfig())
    result = resolver.resolve([str(tmp_path)])
    assert result == sorted(result)


def test_resolver_file_not_found():
    resolver = FileResolver(FileResolverConfig())
    try:
        resolver.resolve(["/nonexistent/path/file.md"])
        raise AssertionError("Expected FileNotFoundError")
    except FileNotFoundError:
        pass


def test_resolver_flowmarkignore(tmp_path: Path):
    (tmp_path / "keep.md").write_text("# Keep")
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "skip.md").write_text("# Skip")
    (tmp_path / ".flowmarkignore").write_text("drafts/\n")

    resolver = FileResolver(FileResolverConfig())
    result = resolver.resolve([str(tmp_path)])
    assert len(result) == 1
    assert result[0].name == "keep.md"


def test_resolver_nested_gitignore(tmp_path: Path):
    """Gitignore in subdirectory should apply to that subtree."""
    (tmp_path / "root.md").write_text("# Root")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "keep.md").write_text("# Keep")
    (sub / ".gitignore").write_text("generated/\n")
    gen = sub / "generated"
    gen.mkdir()
    (gen / "output.md").write_text("# Generated")

    resolver = FileResolver(FileResolverConfig())
    result = resolver.resolve([str(tmp_path)])
    names = sorted(p.name for p in result)
    assert names == ["keep.md", "root.md"]
