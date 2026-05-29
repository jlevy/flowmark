#!/usr/bin/env -S uv run --script --python 3.14
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "jinja2>=3.1.6",
#   "strif>=3.0.1",
# ]
# ///
"""Generate Python README.md from wrapper template + shared docs body."""

from __future__ import annotations

import re
from argparse import ArgumentParser
from pathlib import Path

from jinja2 import Environment, StrictUndefined
from strif import atomic_output_file

# Runner-pin placeholder used in the shared docs body (and the authored SKILL.md):
# `uvx --from flowmark==__FLOWMARK_VERSION__ flowmark`. Substituted here with the single
# source of truth, DISCOVERY_VERSION in src/flowmark/skill.py, so every shipped example
# pins the same real release and a release bump only has to touch one constant.
VERSION_PLACEHOLDER = "__FLOWMARK_VERSION__"


def read_discovery_version(repo_root: Path) -> str:
    """Read DISCOVERY_VERSION (the canonical release pin) from src/flowmark/skill.py.

    This standalone script runs on its own interpreter without flowmark importable, so
    parse the constant out of source rather than importing it. One source of truth means
    `make format` re-stamps the README pins from the same value the skill discovery copy
    uses.
    """
    skill_py = repo_root / "src" / "flowmark" / "skill.py"
    match = re.search(
        r'^DISCOVERY_VERSION\s*=\s*"([^"]+)"', skill_py.read_text(encoding="utf-8"), re.M
    )
    if not match:
        raise ValueError(f"could not find DISCOVERY_VERSION in {skill_py}")
    return match.group(1)


def parse_args() -> tuple[Path, Path, Path, str]:
    """Parse arguments and resolve default repo-relative paths."""
    repo_root = Path(__file__).resolve().parents[1]
    parser = ArgumentParser(description="Generate README.md from Python wrapper + shared docs.")
    parser.add_argument(
        "--shared-docs",
        type=Path,
        default=repo_root / "docs/shared/flowmark-readme-shared.md",
        help="Path to shared README body content.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=repo_root / "docs/templates/python-readme-wrapper.md",
        help="Path to Python README wrapper template.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repo_root / "README.md",
        help="Output README path.",
    )
    parser.add_argument(
        "--flowmark-version",
        default=None,
        help="Version substituted for the runner-pin placeholder "
        "(default: DISCOVERY_VERSION from src/flowmark/skill.py).",
    )
    args = parser.parse_args()
    version = args.flowmark_version or read_discovery_version(repo_root)
    return args.shared_docs, args.template, args.output, version


def render_readme(template_path: Path, shared_docs_body: str) -> str:
    """Render README template with shared docs body."""
    environment = Environment(
        autoescape=False,
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    template = environment.from_string(template_path.read_text(encoding="utf-8"))
    rendered = template.render(shared_docs_body=shared_docs_body.rstrip() + "\n")
    if not rendered.endswith("\n"):
        rendered += "\n"
    return rendered


def write_atomic(output_path: Path, content: str) -> None:
    """Write output atomically."""
    with atomic_output_file(output_path, make_parents=True) as temp_path:
        Path(temp_path).write_text(content, encoding="utf-8")


def main() -> int:
    """Generate README.md from shared docs and wrapper template."""
    shared_docs_path, template_path, output_path, version = parse_args()

    if not shared_docs_path.exists():
        raise FileNotFoundError(f"missing shared docs source at {shared_docs_path}")
    if not template_path.exists():
        raise FileNotFoundError(f"missing wrapper template at {template_path}")

    shared_docs_body = shared_docs_path.read_text(encoding="utf-8")
    rendered = render_readme(template_path, shared_docs_body)
    rendered = rendered.replace(VERSION_PLACEHOLDER, version)
    if VERSION_PLACEHOLDER in rendered:
        raise ValueError(f"{VERSION_PLACEHOLDER} still present after substitution")
    write_atomic(output_path, rendered)

    print(f"Generated {output_path} from {shared_docs_path} via {template_path}")
    print(f"Pinned runner examples to flowmark=={version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
