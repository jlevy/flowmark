"""Tests for CLI help text and help footer guidance."""

from __future__ import annotations

import pytest

from flowmark.cli import main


def _render_help(capsys: pytest.CaptureFixture[str]) -> str:
    """Run `flowmark --help` via CLI entrypoint and return captured stdout."""
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    return capsys.readouterr().out


def test_help_includes_tagline(capsys: pytest.CaptureFixture[str]) -> None:
    """Help output should include the canonical Flowmark tagline."""
    out = _render_help(capsys)
    assert "Flowmark: Better auto-formatting for Markdown and plaintext" in out


def test_help_includes_brief_common_usage(capsys: pytest.CaptureFixture[str]) -> None:
    """Help output should include the concise common usage examples."""
    out = _render_help(capsys)
    assert "Common usage:" in out
    assert "flowmark --auto README.md" in out
    assert "flowmark --auto docs/" in out
    assert "flowmark --auto ." in out
    assert "flowmark --list-files ." in out


def test_help_includes_agent_guidance(capsys: pytest.CaptureFixture[str]) -> None:
    """Help output should include explicit agent guidance via --skill."""
    out = _render_help(capsys)
    assert "Agent usage:" in out
    assert "flowmark --skill" in out
    assert "Agents should run `flowmark --skill` for full Flowmark usage guidance." in out
    assert "Use `flowmark --docs` for full documentation." in out


def test_help_omits_old_long_epilog(capsys: pytest.CaptureFixture[str]) -> None:
    """Help output should not include the old long-form examples section."""
    out = _render_help(capsys)
    assert "Command-line usage examples:" not in out
    assert "Flowmark provides enhanced text wrapping capabilities" not in out
