"""Tests for the skill installation module."""

from pathlib import Path

import pytest

from flowmark import reformat_text
from flowmark.cli import main as cli_main
from flowmark.skill import (
    AGENTS_BEGIN_PREFIX,
    AGENTS_END_MARKER,
    DISCOVERY_VERSION,
    SURFACE_CLAUDE,
    SURFACE_PORTABLE,
    agents_md_block,
    compose_skill,
    flowmark_version,
    get_docs_content,
    get_skill_content,
    install_skill,
    is_pypi_release,
    update_agents_md,
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
        rendered = compose_skill(DISCOVERY_VERSION)
        assert f"flowmark=={DISCOVERY_VERSION}" in rendered
        assert rendered == compose_skill(DISCOVERY_VERSION)  # deterministic

    def test_compose_preserves_frontmatter(self) -> None:
        rendered = compose_skill("1.2.3")
        assert rendered.startswith("---\nname: flowmark\n")

    def test_skill_content_has_vscode_cursor_setup(self) -> None:
        """SKILL.md includes VS Code/Cursor run-on-save guidance."""
        content = get_skill_content()
        assert "VS Code/Cursor" in content
        assert "emeraldwalk.runonsave" in content


class TestVersionPin:
    """The `uvx --from flowmark==<pin>` bootstrap pin must be PyPI-installable."""

    @pytest.mark.parametrize(
        "version_str",
        ["0.7.0", "1.2.3", "0.7", "10.20.30", "0.7.0.post1"],
    )
    def test_real_releases_are_accepted(self, version_str: str) -> None:
        assert is_pypi_release(version_str)

    @pytest.mark.parametrize(
        "version_str",
        [
            "0.7.1.dev29+c40ee1b",  # editable/dev checkout (the bug we hit)
            "0.6.6.dev7+6de6e10",  # stale editable build
            "0.7.0.dev1",  # dev release, no local segment
            "1.0.0+local",  # local version
            "1.0.0a1",  # alpha pre-release
            "1.0.0b2",  # beta pre-release
            "1.0.0rc1",  # release candidate
            "",  # empty / unparsable
            "garbage",
        ],
    )
    def test_non_releases_are_rejected(self, version_str: str) -> None:
        assert not is_pypi_release(version_str)

    def test_dev_version_falls_back_to_discovery_pin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """On a dev/editable checkout, flowmark_version() yields a real PyPI pin."""
        import importlib.metadata

        def fake_version(_name: str) -> str:
            return "0.7.1.dev29+c40ee1b"

        monkeypatch.setattr(importlib.metadata, "version", fake_version)
        assert flowmark_version() == DISCOVERY_VERSION
        # And the rendered skill therefore pins something PyPI-installable.
        assert is_pypi_release(flowmark_version())
        assert f"flowmark=={DISCOVERY_VERSION}" in compose_skill()
        assert f"flowmark=={DISCOVERY_VERSION}" in agents_md_block()

    def test_real_release_is_passed_through(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import importlib.metadata

        def fake_version(_name: str) -> str:
            return "0.9.4"

        monkeypatch.setattr(importlib.metadata, "version", fake_version)
        assert flowmark_version() == "0.9.4"


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
        # README.md has these distinctive sections. The install heading text comes from
        # docs/templates/python-readme-wrapper.md (the source of truth); match loosely so
        # a heading reword there doesn't break this test.
        assert "# flowmark" in content.lower()
        assert "## Installing Flowmark" in content
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
        """The `surfaces` set selects which surfaces are written."""
        install_skill(project_root=tmp_path, surfaces=frozenset({SURFACE_PORTABLE}))
        assert (tmp_path / ".agents" / "skills" / "flowmark" / "SKILL.md").exists()
        assert not (tmp_path / ".claude").exists()
        assert not (tmp_path / "AGENTS.md").exists()

    def test_installed_file_has_do_not_edit_and_format_stamp(self, tmp_path: Path) -> None:
        install_skill(project_root=tmp_path)
        content = (tmp_path / ".claude" / "skills" / "flowmark" / "SKILL.md").read_text()
        assert "DO NOT EDIT" in content
        assert "format=f02 surface=skill-md" in content
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
        target.write_text("<!-- format=f99 surface=skill-md -->\nnewer", encoding="utf-8")

        results = install_skill(project_root=tmp_path, surfaces=frozenset({SURFACE_CLAUDE}))

        assert [r.action for r in results] == ["blocked-newer"]
        assert target.read_text() == "<!-- format=f99 surface=skill-md -->\nnewer"


class TestAgentsMdBlock:
    """Tests for the AGENTS.md integration block."""

    def test_block_is_marker_bounded_with_format(self) -> None:
        block = agents_md_block("1.2.3")
        assert block.startswith(AGENTS_BEGIN_PREFIX)
        assert "format=f02" in block
        assert block.rstrip().endswith(AGENTS_END_MARKER)
        assert "flowmark==1.2.3" in block

    def test_block_is_flowmark_auto_stable(self) -> None:
        """A flowmark format pass over a host AGENTS.md must leave the block unchanged."""
        block = agents_md_block("0.7.0")
        doc = f"# Project\n\nUser-authored notes.\n\n{block}\n"
        assert block in reformat_text(doc)

    def test_update_creates_and_preserves_user_content(self, tmp_path: Path) -> None:
        path = tmp_path / "AGENTS.md"
        path.write_text("# My Project\n\nHand-written guidance.\n", encoding="utf-8")

        update_agents_md(path, version="0.7.0")

        content = path.read_text()
        assert "Hand-written guidance." in content  # user content preserved
        assert AGENTS_BEGIN_PREFIX in content

    def test_update_replaces_only_the_marked_region(self, tmp_path: Path) -> None:
        path = tmp_path / "AGENTS.md"
        update_agents_md(path, version="0.7.0")
        # Add user content after the block, then re-run with a different version.
        path.write_text(path.read_text() + "\n## User Section\n\nKeep me.\n", encoding="utf-8")

        update_agents_md(path, version="9.9.9")

        content = path.read_text()
        assert "Keep me." in content
        assert "flowmark==9.9.9" in content
        assert "flowmark==0.7.0" not in content
        assert content.count(AGENTS_BEGIN_PREFIX) == 1  # no duplicate block

    def test_update_is_idempotent(self, tmp_path: Path) -> None:
        path = tmp_path / "AGENTS.md"
        assert update_agents_md(path, version="0.7.0").action == "installed"
        assert update_agents_md(path, version="0.7.0").action == "unchanged"

    def test_update_collapses_duplicate_stale_blocks(self, tmp_path: Path) -> None:
        """Multiple stale flowmark blocks collapse to one current block on re-run."""
        path = tmp_path / "AGENTS.md"
        stale = agents_md_block("1.0.0")
        path.write_text(
            f"# Project\n\nUser-authored notes.\n\n{stale}\n\n## User Section\n\nKeep me.\n\n{stale}\n",
            encoding="utf-8",
        )

        update_agents_md(path, version="2.0.0")

        content = path.read_text()
        assert content.count(AGENTS_BEGIN_PREFIX) == 1  # collapsed to one block
        assert "flowmark==1.0.0" not in content  # stale pins removed
        assert "flowmark==2.0.0" in content  # current pin written
        assert "Keep me." in content  # user content preserved

    def test_update_guard_blocks_newer_format(self, tmp_path: Path) -> None:
        path = tmp_path / "AGENTS.md"
        path.write_text(
            f"{AGENTS_BEGIN_PREFIX} format=f99 surface=agents-md -->\nnewer\n{AGENTS_END_MARKER}\n",
            encoding="utf-8",
        )
        result = update_agents_md(path, version="0.7.0")
        assert result.action == "blocked-newer"
        assert "format=f99" in path.read_text()

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


class TestInstallSkillCli:
    """CLI-level tests for `flowmark --install-skill --surfaces` parsing."""

    def test_default_writes_all_three_surfaces(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert cli_main(["--install-skill"]) == 0
        assert (tmp_path / ".agents" / "skills" / "flowmark" / "SKILL.md").exists()
        assert (tmp_path / ".claude" / "skills" / "flowmark" / "SKILL.md").exists()
        assert (tmp_path / "AGENTS.md").exists()

    def test_surfaces_subset(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert cli_main(["--install-skill", "--surfaces=portable,agents-md"]) == 0
        assert (tmp_path / ".agents" / "skills" / "flowmark" / "SKILL.md").exists()
        assert (tmp_path / "AGENTS.md").exists()
        assert not (tmp_path / ".claude").exists()

    def test_surfaces_all_alias(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert cli_main(["--install-skill", "--surfaces=all"]) == 0
        assert (tmp_path / ".agents" / "skills" / "flowmark" / "SKILL.md").exists()
        assert (tmp_path / ".claude" / "skills" / "flowmark" / "SKILL.md").exists()
        assert (tmp_path / "AGENTS.md").exists()

    def test_unknown_surface_errors_out(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        rc = cli_main(["--install-skill", "--surfaces=cursor"])
        assert rc == 2
        err = capsys.readouterr().err
        assert "unknown surface 'cursor'" in err
        assert not (tmp_path / ".claude").exists()
        assert not (tmp_path / ".agents").exists()

    def test_empty_surfaces_value_errors_out(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        rc = cli_main(["--install-skill", "--surfaces="])
        assert rc == 2
        err = capsys.readouterr().err
        assert "empty value" in err

    def test_surfaces_with_agent_base_errors_out(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = cli_main(
            [
                "--install-skill",
                "--agent-base",
                str(tmp_path / "base"),
                "--surfaces=portable",
            ]
        )
        assert rc == 2
        err = capsys.readouterr().err
        assert "incompatible with --agent-base" in err
