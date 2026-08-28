"""
Corpus-wide idempotence gate.

Formatting is meant to reach a fixed point in one pass: ``format(format(x)) ==
format(x)``. Where it does not, ``flowmark --check`` reports files flowmark itself just
wrote, and repeated runs rewrite authored content.

The shared conformance corpus already verifies this per case, but each case pins one CLI
invocation, so the option space is sampled one point per document. This walks every
Markdown document the project ships across a mode matrix instead, which is what surfaces
width-dependent instability.

Known failures live in ``tests/idempotence_known_divergences.toml`` and are asserted
exactly: an unlisted failure fails the build, and a listed entry that now passes also
fails it, so the ledger shrinks and cannot rot.

This is the reference-side twin of ``tests/test_idempotence_corpus.rs`` in flowmark-rs.
The two ledgers are separate on purpose: a defect one port carries and the other does not
is exactly what the pair is meant to make visible.
"""

from __future__ import annotations

import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from flowmark import reformat_text
from flowmark.formats.flowmark_markdown import ListSpacing

if sys.version_info >= (3, 11):
    import tomllib  # pyright: ignore[reportUnreachable]
else:
    import tomli as tomllib  # type: ignore[no-redef]  # pyright: ignore[reportUnreachable]

REPO_ROOT = Path(__file__).resolve().parent.parent

# Modes covering the option space's independent axes rather than its combinations.
# Width earns two entries: instability that only appears when wrapping pushes a hazardous
# token to the start of a line is invisible at the default width.
_BASE: dict[str, Any] = {
    "plaintext": False,
    "semantic": False,
    "cleanups": False,
    "smartquotes": False,
    "ellipses": False,
    "list_spacing": ListSpacing.preserve,
}
MODES: dict[str, dict[str, Any]] = {
    "default": {**_BASE, "width": 88},
    "semantic": {**_BASE, "width": 88, "semantic": True},
    "cleanups": {**_BASE, "width": 88, "cleanups": True},
    "typography": {
        **_BASE,
        "width": 88,
        "semantic": True,
        "cleanups": True,
        "smartquotes": True,
        "ellipses": True,
    },
    "nowrap": {**_BASE, "width": 0},
    "narrow": {**_BASE, "width": 40},
}


def corpus_documents() -> list[Path]:
    """Every corpus the project ships, plus its own docs.

    The repository's docs are the only genuinely human-authored prose in the set, and a
    doc flowmark cannot format stably is itself a defect.
    """
    tests = REPO_ROOT / "tests"
    assert tests.is_dir(), f"corpus missing at {tests}"
    documents = sorted(tests.rglob("*.md"))
    documents += sorted((REPO_ROOT / "docs").rglob("*.md"))
    readme = REPO_ROOT / "README.md"
    if readme.is_file():
        documents.append(readme)
    assert len(documents) > 1000, f"expected the full corpus, found only {len(documents)}"
    return documents


def load_ledger() -> set[str]:
    """A ledger entry names one document and one mode, keyed as ``relative/path::mode``."""
    path = REPO_ROOT / "tests" / "idempotence_known_divergences.toml"
    data: dict[str, Any] = tomllib.loads(path.read_text(encoding="utf-8"))
    assert data.get("schema_version") == 1, "ledger schema_version must be 1"
    entries: list[dict[str, Any]] = data.get("divergence", [])
    ledger: set[str] = set()
    for entry in entries:
        document: str | None = entry.get("document")
        mode: str | None = entry.get("mode")
        assert document, "each divergence needs a non-empty document"
        assert mode, "each divergence needs a non-empty mode"
        assert entry.get("bead"), f"each divergence needs a non-empty bead: {document}::{mode}"
        key = f"{document}::{mode}"
        assert key not in ledger, f"duplicate ledger entry: {key}"
        ledger.add(key)
    return ledger


def _unstable_modes(path_text: str) -> list[str]:
    """Return the modes in which this document is not a fixed point."""
    path = Path(path_text)
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Deliberately invalid UTF-8 fixtures are byte-level I/O cases, not formatter
        # inputs for this gate.
        return []
    failures: list[str] = []
    for name, options in MODES.items():
        once = reformat_text(source, **options)
        if reformat_text(once, **options) != once:
            failures.append(f"{path.relative_to(REPO_ROOT).as_posix()}::{name}")
    return failures


def test_every_corpus_document_reaches_a_fixed_point() -> None:
    """Formatting must reach a fixed point in one pass for every shipped document in
    every mode, except the exact set the ledger names."""
    documents = corpus_documents()
    ledger = load_ledger()

    observed: set[str] = set()
    with ProcessPoolExecutor() as pool:
        for failures in pool.map(_unstable_modes, [str(p) for p in documents], chunksize=16):
            observed.update(failures)
    checks = len(documents) * len(MODES)

    unexpected = sorted(observed - ledger)
    stale = sorted(ledger - observed)

    assert not unexpected, (
        f"{len(unexpected)} of {checks} checks are newly not a fixed point.\n"
        "Add a ledger entry only with a tracking bead, or fix the defect:\n  "
        + "\n  ".join(unexpected)
    )
    assert not stale, (
        f"{len(stale)} ledger entries now pass and must be removed:\n  " + "\n  ".join(stale)
    )
