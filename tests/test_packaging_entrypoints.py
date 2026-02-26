"""Packaging entrypoint tests."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


def test_flowmark_py_alias_entrypoint() -> None:
    """Both flowmark and flowmark-py should point to the same CLI entrypoint."""
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    scripts = data["project"]["scripts"]

    assert scripts["flowmark"] == "flowmark.cli:main"
    assert scripts["flowmark-py"] == "flowmark.cli:main"
