"""Packaging entrypoint tests."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib  # pyright: ignore[reportUnreachable]
else:
    import tomli as tomllib  # type: ignore[no-redef]  # pyright: ignore[reportUnreachable]


def test_flowmark_py_alias_entrypoint() -> None:
    """Both flowmark and flowmark-py should point to the same CLI entrypoint."""
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    scripts = data["project"]["scripts"]

    assert scripts["flowmark"] == "flowmark.cli:main"
    assert scripts["flowmark-py"] == "flowmark.cli:main"
