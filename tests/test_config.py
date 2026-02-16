"""Tests for config file loading and merging."""

from __future__ import annotations

from pathlib import Path

import pytest

from flowmark.cli import Options
from flowmark.config import FlowmarkConfig, find_config_file, load_config, merge_cli_with_config
from flowmark.formats.flowmark_markdown import ListSpacing


def test_find_config_flowmark_toml(tmp_path: Path) -> None:
    config_file = tmp_path / "flowmark.toml"
    config_file.write_text("[formatting]\nwidth = 100\n")
    result = find_config_file(tmp_path)
    assert result == config_file


def test_find_config_dot_flowmark_toml_takes_precedence(tmp_path: Path) -> None:
    (tmp_path / "flowmark.toml").write_text("[formatting]\nwidth = 100\n")
    dot_config = tmp_path / ".flowmark.toml"
    dot_config.write_text("[formatting]\nwidth = 80\n")
    result = find_config_file(tmp_path)
    assert result == dot_config


def test_find_config_pyproject_toml(tmp_path: Path) -> None:
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("[tool.flowmark]\nwidth = 100\n")
    result = find_config_file(tmp_path)
    assert result == config_file


def test_find_config_pyproject_without_section_skipped(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\nline-length = 100\n")
    result = find_config_file(tmp_path)
    assert result is None


def test_find_config_walks_up(tmp_path: Path) -> None:
    config_file = tmp_path / "flowmark.toml"
    config_file.write_text("[formatting]\nwidth = 100\n")
    subdir = tmp_path / "sub" / "deep"
    subdir.mkdir(parents=True)
    result = find_config_file(subdir)
    assert result == config_file


def test_find_config_none_when_missing(tmp_path: Path) -> None:
    result = find_config_file(tmp_path)
    assert result is None


def test_load_config_flowmark_toml(tmp_path: Path) -> None:
    config_file = tmp_path / "flowmark.toml"
    config_file.write_text("[formatting]\nwidth = 100\nsemantic = true\nsmartquotes = true\n")
    config = load_config(config_file)
    assert config.width == 100
    assert config.semantic is True
    assert config.smartquotes is True
    # Unset fields should be None (not set)
    assert config.cleanups is None


def test_load_config_pyproject_toml(tmp_path: Path) -> None:
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("[tool.flowmark]\nwidth = 80\nellipses = true\n")
    config = load_config(config_file)
    assert config.width == 80
    assert config.ellipses is True


def test_load_config_kebab_case(tmp_path: Path) -> None:
    config_file = tmp_path / "flowmark.toml"
    config_file.write_text(
        "[formatting]\n"
        'list-spacing = "loose"\n'
        "\n"
        "[file-discovery]\n"
        'extend-exclude = ["drafts/"]\n'
        "files-max-size = 500000\n"
        "respect-gitignore = false\n"
        "force-exclude = true\n"
    )
    config = load_config(config_file)
    assert config.list_spacing == "loose"
    assert config.extend_exclude == ["drafts/"]
    assert config.files_max_size == 500000
    assert config.respect_gitignore is False
    assert config.force_exclude is True


def test_load_config_file_discovery_section(tmp_path: Path) -> None:
    config_file = tmp_path / "flowmark.toml"
    config_file.write_text(
        '[file-discovery]\nextend-include = ["*.mdx", "*.markdown"]\nexclude = ["my_custom/"]\n'
    )
    config = load_config(config_file)
    assert config.extend_include == ["*.mdx", "*.markdown"]
    assert config.exclude == ["my_custom/"]


def test_load_config_partial(tmp_path: Path) -> None:
    config_file = tmp_path / "flowmark.toml"
    config_file.write_text("[formatting]\nwidth = 120\n")
    config = load_config(config_file)
    assert config.width == 120
    # Everything else should be None (not set)
    assert config.semantic is None
    assert config.extend_exclude is None


def _make_options(  # pyright: ignore[reportUnusedParameter]
    files: list[str] | None = None,
    output: str = "-",
    width: int = 88,
    plaintext: bool = False,
    semantic: bool = False,
    cleanups: bool = False,
    smartquotes: bool = False,
    ellipses: bool = False,
    inplace: bool = False,
    nobackup: bool = False,
    version: bool = False,
    list_spacing: ListSpacing = ListSpacing.preserve,
    extend_include: list[str] | None = None,
    exclude: list[str] | None = None,
    extend_exclude: list[str] | None = None,
    respect_gitignore: bool = True,
    force_exclude: bool = False,
    list_files: bool = False,
    files_max_size: int = 1_048_576,
    skill_instructions: bool = False,
    install_skill: bool = False,
    agent_base: str | None = None,
    docs: bool = False,
) -> Options:
    """Create an Options with defaults for all required fields."""
    return Options(
        files=files if files is not None else ["."],
        output=output,
        width=width,
        plaintext=plaintext,
        semantic=semantic,
        cleanups=cleanups,
        smartquotes=smartquotes,
        ellipses=ellipses,
        inplace=inplace,
        nobackup=nobackup,
        version=version,
        list_spacing=list_spacing,
        extend_include=extend_include if extend_include is not None else [],
        exclude=exclude,
        extend_exclude=extend_exclude if extend_exclude is not None else [],
        respect_gitignore=respect_gitignore,
        force_exclude=force_exclude,
        list_files=list_files,
        files_max_size=files_max_size,
        skill_instructions=skill_instructions,
        install_skill=install_skill,
        agent_base=agent_base,
        docs=docs,
    )


def test_merge_no_config() -> None:
    opts = _make_options(width=88, semantic=False)
    result = merge_cli_with_config(opts, config=None, is_auto=False, explicit_flags=set())
    assert result.width == 88
    assert result.semantic is False


def test_merge_config_overrides_defaults() -> None:
    opts = _make_options()
    config = FlowmarkConfig(width=100, semantic=True)
    result = merge_cli_with_config(opts, config=config, is_auto=False, explicit_flags=set())
    assert result.width == 100
    assert result.semantic is True


def test_merge_explicit_cli_overrides_config() -> None:
    opts = _make_options(width=120)
    config = FlowmarkConfig(width=100)
    result = merge_cli_with_config(opts, config=config, is_auto=False, explicit_flags={"width"})
    assert result.width == 120


def test_merge_auto_mode_overrides_formatting() -> None:
    config = FlowmarkConfig(semantic=False, smartquotes=False)
    opts = _make_options(
        semantic=True,
        cleanups=True,
        smartquotes=True,
        ellipses=True,
        inplace=True,
        nobackup=True,
    )
    result = merge_cli_with_config(opts, config=config, is_auto=True, explicit_flags=set())
    # --auto forces formatting settings on
    assert result.semantic is True
    assert result.smartquotes is True
    assert result.cleanups is True
    assert result.ellipses is True


def test_merge_auto_mode_width_from_config() -> None:
    config = FlowmarkConfig(width=100)
    opts = _make_options(
        width=88,
        semantic=True,
        cleanups=True,
        smartquotes=True,
        ellipses=True,
        inplace=True,
        nobackup=True,
    )
    result = merge_cli_with_config(opts, config=config, is_auto=True, explicit_flags=set())
    # Width should come from config even in auto mode
    assert result.width == 100


def test_merge_file_discovery_from_config() -> None:
    config = FlowmarkConfig(extend_exclude=["vendor/"], files_max_size=500000)
    opts = _make_options()
    result = merge_cli_with_config(opts, config=config, is_auto=False, explicit_flags=set())
    assert result.extend_exclude == ["vendor/"]
    assert result.files_max_size == 500000


def test_merge_extend_include_from_config() -> None:
    """Config extend_include should be applied when not explicitly set (fm-p6x5)."""
    config = FlowmarkConfig(extend_include=["*.mdx", "*.markdown"])
    opts = _make_options()
    result = merge_cli_with_config(opts, config=config, is_auto=False, explicit_flags=set())
    assert result.extend_include == ["*.mdx", "*.markdown"]


def test_load_config_malformed_toml(tmp_path: Path, capsys: object) -> None:
    """Malformed TOML should return empty config, not crash (fm-lbku)."""
    config_file = tmp_path / "flowmark.toml"
    config_file.write_text("this is not valid toml [[[")
    config = load_config(config_file)
    # Should return default empty config
    assert config.width is None
    assert config.semantic is None


def test_parse_config_warns_unknown_keys(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Unknown keys in config should produce a warning (fm-y9cx)."""
    config_file = tmp_path / "flowmark.toml"
    config_file.write_text("unknown_key = true\nwidth = 100\n")
    config = load_config(config_file)
    assert config.width == 100
    captured = capsys.readouterr()
    assert "unrecognized config key" in captured.err
