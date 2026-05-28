"""Drift and validation tests for generated skill artifacts (the committed discovery copy
and the skill frontmatter). Regenerate with `make gen-skill` if the drift test fails."""

import re
from pathlib import Path

from flowmark import reformat_text
from flowmark.skill import compose_skill, discovery_skill_text

REPO_ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_COPY = REPO_ROOT / "skills" / "flowmark" / "SKILL.md"


def test_discovery_copy_matches_generator() -> None:
    """The committed repo-root discovery copy must match the generator output."""
    assert DISCOVERY_COPY.read_text(encoding="utf-8") == discovery_skill_text()


def test_discovery_copy_is_flowmark_stable() -> None:
    """`flowmark --auto` over the discovery copy must be a no-op (it lives under `skills/`)."""
    text = DISCOVERY_COPY.read_text(encoding="utf-8")
    assert reformat_text(text) == text


def test_discovery_copy_has_resolvable_version_pin() -> None:
    """The committed discovery copy must pin a real, PyPI-installable version.

    `npx skills add jlevy/flowmark` users have no other source of truth for the
    bootstrap invocation, so a `<version>` placeholder or `.dev`/local-suffix pin
    in the committed copy would silently break the cross-agent install promise in
    the README.
    """
    text = DISCOVERY_COPY.read_text(encoding="utf-8")
    assert "__FLOWMARK_VERSION__" not in text  # template never escaped past compose
    assert "flowmark==<version>" not in text  # not a literal placeholder
    pin = re.search(r"flowmark==([^\s`)\"']+)", text)
    assert pin is not None, "discovery copy missing a flowmark== version pin"
    pin_value = pin.group(1)
    assert ".dev" not in pin_value and "+" not in pin_value, (
        f"discovery copy pin {pin_value!r} is a dev/local version, not PyPI-installable; "
        "bump DISCOVERY_VERSION to a real release and re-run `make format`"
    )


def test_skill_frontmatter_is_valid() -> None:
    content = compose_skill("1.2.3")
    assert content.startswith("---\n")
    frontmatter = content[4 : content.index("\n---\n", 4)]
    assert re.search(r"^name: flowmark$", frontmatter, re.M)
    description = re.search(r"^description: (.+)$", frontmatter, re.M)
    assert description is not None
    assert len(description.group(1)) <= 1024  # Agent Skills cap (guideline §4.1)
    assert re.search(r"^allowed-tools: ", frontmatter, re.M)
