#!/usr/bin/env python
"""
Generate the committed repo-root skill discovery copy at `skills/flowmark/SKILL.md`.

This is the published landing-page skill that `npx skills add jlevy/flowmark` and skill
indexers pick up. It is generated from the same authored source as the installed skill
(`flowmark.skill.discovery_skill_text`) so the two can't drift; `tests/test_skill_artifacts.py`
fails if the committed copy is stale.
"""

from __future__ import annotations

from pathlib import Path

from strif import atomic_output_file

from flowmark.skill import discovery_skill_text


def main() -> None:
    output = Path(__file__).resolve().parents[1] / "skills" / "flowmark" / "SKILL.md"
    with atomic_output_file(output, make_parents=True) as tmp:
        Path(tmp).write_text(discovery_skill_text(), encoding="utf-8")
    print(f"Generated {output}")


if __name__ == "__main__":
    main()
