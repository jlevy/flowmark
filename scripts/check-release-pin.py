#!/usr/bin/env python
"""
Release guard: the skill's bootstrap pin must match the release being published.

The committed discovery copy and the README runner examples pin
`uvx --from flowmark==<DISCOVERY_VERSION>`. That pin is the single source of truth in
`src/flowmark/skill.py`. If a release is tagged without bumping DISCOVERY_VERSION (and
re-running `make format`), agents that bootstrap from the just-published skill would pin
the *previous* release. This script fails the publish when that would happen.

Usage:
    # Compare against an explicit version (publish CI passes the release tag):
    python scripts/check-release-pin.py --expected 0.7.1

    # Or derive from the exact tag at HEAD (leading `v` optional):
    python scripts/check-release-pin.py --from-git-tag

With neither flag it only checks internal consistency (every shipped artifact pins
DISCOVERY_VERSION), which also runs in the test suite.
"""

from __future__ import annotations

import re
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PY = REPO_ROOT / "src" / "flowmark" / "skill.py"
# Every artifact whose concrete `flowmark==` pin must equal DISCOVERY_VERSION. Kept in
# sync with tests/test_skill_artifacts.py::_PINNED_ARTIFACTS: the README and the
# committed discovery copy, plus this repo's dogfooded install surfaces (portable +
# Claude SKILL.md mirrors and the AGENTS.md flowmark block).
SHIPPED_ARTIFACTS = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "skills" / "flowmark" / "SKILL.md",
    REPO_ROOT / ".agents" / "skills" / "flowmark" / "SKILL.md",
    REPO_ROOT / ".claude" / "skills" / "flowmark" / "SKILL.md",
    REPO_ROOT / "AGENTS.md",
]
_CONCRETE_PIN_RE = re.compile(r"flowmark==(\d[^\s`)\"']*)")


def discovery_version() -> str:
    match = re.search(
        r'^DISCOVERY_VERSION\s*=\s*"([^"]+)"', SKILL_PY.read_text(encoding="utf-8"), re.M
    )
    if not match:
        raise SystemExit(f"could not find DISCOVERY_VERSION in {SKILL_PY}")
    return match.group(1)


def git_tag_version() -> str:
    """The exact tag at HEAD with any leading `v` stripped (e.g. v0.7.1 -> 0.7.1)."""
    try:
        tag = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"HEAD is not exactly on a tag: {exc.stderr.strip()}") from exc
    return tag[1:] if tag.startswith("v") else tag


def main() -> int:
    parser = ArgumentParser(description="Verify the skill release pin matches the release.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--expected", help="Version the release should pin (e.g. 0.7.1).")
    group.add_argument(
        "--from-git-tag",
        action="store_true",
        help="Derive the expected version from the exact git tag at HEAD.",
    )
    args = parser.parse_args()

    pin = discovery_version()
    problems: list[str] = []

    # Release tags are like `v0.7.1`; compare against the bare version.
    if args.expected and args.expected.startswith("v"):
        args.expected = args.expected[1:]

    # 1. Internal consistency: every concrete pin in every shipped artifact == DISCOVERY_VERSION.
    for artifact in SHIPPED_ARTIFACTS:
        text = artifact.read_text(encoding="utf-8")
        stale = sorted({p for p in _CONCRETE_PIN_RE.findall(text) if p != pin})
        if stale:
            problems.append(
                f"{artifact.relative_to(REPO_ROOT)} pins {stale}, expected {pin} "
                "(run `make format`)"
            )

    # 2. Release coherence: DISCOVERY_VERSION matches the version being released.
    expected = args.expected or (git_tag_version() if args.from_git_tag else None)
    if expected is not None and expected != pin:
        problems.append(
            f"DISCOVERY_VERSION is {pin!r} but the release is {expected!r}; "
            "bump DISCOVERY_VERSION in src/flowmark/skill.py and re-run `make format`"
        )

    if problems:
        print("Release pin check FAILED:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    target = f" (matches release {expected})" if expected else ""
    print(f"Release pin OK: all shipped artifacts pin flowmark=={pin}{target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
