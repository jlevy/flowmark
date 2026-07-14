#!/usr/bin/env python
"""
Generate the committed repo-root skill bundle under `skills/flowmark/`.

This is the published landing-page skill that
`npx skills add jlevy/flowmark@flowmark` and skill indexers pick up. It is generated from
the same authored source as the installed skill (`flowmark.skill.discovery_skill_text`)
so the two can't drift; `tests/test_skill_artifacts.py` fails if the committed copy is
stale.
"""

from __future__ import annotations

from pathlib import Path

from strif import atomic_output_file

from flowmark.skill import discovery_project_setup_text, discovery_skill_text


def main() -> None:
    skill_dir = Path(__file__).resolve().parents[1] / "skills" / "flowmark"
    skill_output = skill_dir / "SKILL.md"
    reference_output = skill_dir / "references" / "project-setup.md"
    with atomic_output_file(skill_output, make_parents=True) as tmp:
        Path(tmp).write_text(discovery_skill_text(), encoding="utf-8")
    with atomic_output_file(reference_output, make_parents=True) as tmp:
        Path(tmp).write_text(discovery_project_setup_text(), encoding="utf-8")
    print(f"Generated {skill_output}")
    print(f"Generated {reference_output}")


if __name__ == "__main__":
    main()
