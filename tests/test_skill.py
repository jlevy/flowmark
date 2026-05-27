"""Tests for the skill installation module."""

from pathlib import Path

from flowmark.skill import (
    DOC_VERSION_PIN,
    compose_skill,
    flowmark_version,
    get_docs_content,
    get_skill_content,
    install_skill,
)


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
        assert "flowmark --auto" in content


class TestComposeSkill:
    """Tests for compose_skill version rendering."""

    def test_compose_substitutes_explicit_version(self) -> None:
        rendered = compose_skill("1.2.3")
        assert "flowmark==1.2.3" in rendered
        assert "__FLOWMARK_VERSION__" not in rendered

    def test_compose_default_pins_installed_version(self) -> None:
        rendered = compose_skill()
        assert "__FLOWMARK_VERSION__" not in rendered
        assert f"flowmark=={flowmark_version()}" in rendered

    def test_compose_doc_pin_is_stable(self) -> None:
        # The committed/published copy uses a literal placeholder, not a real version,
        # so it never churns across releases.
        rendered = compose_skill(DOC_VERSION_PIN)
        assert f"flowmark=={DOC_VERSION_PIN}" in rendered
        assert rendered == compose_skill(DOC_VERSION_PIN)  # deterministic

    def test_compose_preserves_frontmatter(self) -> None:
        rendered = compose_skill("1.2.3")
        assert rendered.startswith("---\nname: flowmark\n")

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
        assert "## Installing Python Flowmark CLI" in content
        assert "## Semantic Line Breaks" in content

    def test_docs_content_has_vscode_cursor_setup(self) -> None:
        """README/docs content includes VS Code/Cursor run-on-save setup."""
        content = get_docs_content()
        assert "Use in VSCode/Cursor" in content or "Use in VS Code/Cursor" in content
        assert "emeraldwalk.runonsave" in content


class TestInstallSkill:
    """Tests for install_skill function."""

    def test_install_default_writes_both_project_local_surfaces(self, tmp_path: Path) -> None:
        """Default project-local install writes both portable and Claude surfaces."""
        install_skill(project_root=tmp_path)

        portable = tmp_path / ".agents" / "skills" / "flowmark" / "SKILL.md"
        claude = tmp_path / ".claude" / "skills" / "flowmark" / "SKILL.md"
        assert portable.exists()
        assert claude.exists()
        assert "name: flowmark" in claude.read_text()

    def test_install_target_selection(self, tmp_path: Path) -> None:
        """codex/claude flags select which surfaces are written."""
        install_skill(project_root=tmp_path, claude=False, codex=True)
        assert (tmp_path / ".agents" / "skills" / "flowmark" / "SKILL.md").exists()
        assert not (tmp_path / ".claude").exists()

    def test_installed_file_has_do_not_edit_and_format_stamp(self, tmp_path: Path) -> None:
        install_skill(project_root=tmp_path)
        content = (tmp_path / ".claude" / "skills" / "flowmark" / "SKILL.md").read_text()
        assert "DO NOT EDIT" in content
        assert "skill-format=f01" in content
        # Frontmatter must still come first for the skill to parse.
        assert content.startswith("---\nname: flowmark\n")

    def test_install_is_idempotent(self, tmp_path: Path) -> None:
        first = install_skill(project_root=tmp_path)
        assert {r.action for r in first} == {"installed"}
        second = install_skill(project_root=tmp_path)
        assert {r.action for r in second} == {"unchanged"}

    def test_forward_compat_guard_blocks_newer_format(self, tmp_path: Path) -> None:
        """A surface stamped with a newer format is not clobbered."""
        target = tmp_path / ".claude" / "skills" / "flowmark" / "SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_text("<!-- skill-format=f99 -->\nnewer", encoding="utf-8")

        results = install_skill(project_root=tmp_path, codex=False, claude=True)

        assert [r.action for r in results] == ["blocked-newer"]
        assert target.read_text() == "<!-- skill-format=f99 -->\nnewer"

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
