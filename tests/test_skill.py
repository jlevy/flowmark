"""Tests for the skill installation module."""

from pathlib import Path

import pytest

from flowmark.skill import get_docs_content, get_skill_content, install_skill


class TestGetSkillContent:
    """Tests for get_skill_content function."""

    def test_skill_content_loads(self) -> None:
        """SKILL.md can be loaded from package data."""
        content = get_skill_content()
        assert content is not None
        assert len(content) > 0

    def test_skill_content_has_metadata(self) -> None:
        """SKILL.md contains required metadata fields."""
        content = get_skill_content()
        assert "name: flowmark" in content
        assert "description:" in content
        assert "allowed-tools:" in content

    def test_skill_content_has_usage(self) -> None:
        """SKILL.md contains usage instructions."""
        content = get_skill_content()
        assert "# Flowmark" in content
        assert "uvx flowmark" in content

    def test_skill_content_has_vscode_cursor_setup(self) -> None:
        """SKILL.md includes VS Code/Cursor run-on-save guidance."""
        content = get_skill_content()
        assert "VS Code/Cursor" in content
        assert "emeraldwalk.runonsave" in content


class TestGetDocsContent:
    """Tests for get_docs_content function."""

    def test_docs_content_loads(self) -> None:
        """README.md content can be loaded."""
        content = get_docs_content()
        assert content is not None
        assert len(content) > 0

    def test_docs_content_is_readme(self) -> None:
        """get_docs_content returns README.md content."""
        content = get_docs_content()
        # README.md has these distinctive sections
        assert "# flowmark" in content.lower()
        assert "## Installation" in content
        assert "## Semantic Line Breaks" in content

    def test_docs_content_has_vscode_cursor_setup(self) -> None:
        """README/docs content includes VS Code/Cursor run-on-save setup."""
        content = get_docs_content()
        assert "Use in VSCode/Cursor" in content or "Use in VS Code/Cursor" in content
        assert "emeraldwalk.runonsave" in content


class TestInstallSkill:
    """Tests for install_skill function."""

    def test_install_skill_default(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Skill installs to ~/.claude by default."""
        # Mock Path.home() to return tmp_path
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        install_skill()

        skill_file = tmp_path / ".claude" / "skills" / "flowmark" / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text()
        assert "name: flowmark" in content

    def test_install_skill_custom_base(self, tmp_path: Path) -> None:
        """Skill installs to custom agent base directory."""
        custom_base = tmp_path / ".claude"

        install_skill(agent_base=str(custom_base))

        skill_file = custom_base / "skills" / "flowmark" / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text()
        assert "name: flowmark" in content

    def test_install_skill_creates_directories(self, tmp_path: Path) -> None:
        """Skill installation creates necessary directories."""
        custom_base = tmp_path / "deep" / "nested" / "path"

        install_skill(agent_base=str(custom_base))

        skill_file = custom_base / "skills" / "flowmark" / "SKILL.md"
        assert skill_file.exists()

    def test_install_skill_overwrites_existing(self, tmp_path: Path) -> None:
        """Skill installation overwrites existing SKILL.md."""
        custom_base = tmp_path / ".claude"
        skill_dir = custom_base / "skills" / "flowmark"
        skill_dir.mkdir(parents=True)

        # Write dummy content
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("old content")

        install_skill(agent_base=str(custom_base))

        content = skill_file.read_text()
        assert "old content" not in content
        assert "name: flowmark" in content
