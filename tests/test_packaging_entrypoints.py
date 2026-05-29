"""Packaging entrypoint tests."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib  # pyright: ignore[reportUnreachable]
else:
    import tomli as tomllib  # type: ignore[no-redef]  # pyright: ignore[reportUnreachable]


_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_flowmark_py_alias_entrypoint() -> None:
    """Both flowmark and flowmark-py should point to the same CLI entrypoint."""
    pyproject = _REPO_ROOT / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    scripts = data["project"]["scripts"]

    assert scripts["flowmark"] == "flowmark.cli:main"
    assert scripts["flowmark-py"] == "flowmark.cli:main"


def test_pre_commit_hooks_manifest_is_valid() -> None:
    """Guard the published .pre-commit-hooks.yaml against shipping malformed.

    Checks both hooks are declared with the required fields and that they set
    --force-exclude (so exclusions apply to the explicit paths pre-commit passes),
    and that the check hook mirrors --auto so it validates what the auto-fix hook writes.
    Uses a tolerant text scan to avoid a PyYAML test dependency.
    """
    text = (_REPO_ROOT / ".pre-commit-hooks.yaml").read_text(encoding="utf-8")

    assert "- id: flowmark\n" in text
    assert "- id: flowmark-check\n" in text
    assert text.count("entry: flowmark\n") == 2
    assert text.count("language: python\n") == 2
    assert text.count("types: [markdown]\n") == 2
    assert "args: [--auto, --force-exclude]\n" in text
    assert "args: [--auto, --check, --force-exclude]\n" in text
