#!/usr/bin/env python3
"""Import the pinned CommonMark corpus and create a reviewed-candidate registry once."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, cast

import marko

if sys.version_info >= (3, 11):
    import tomllib  # pyright: ignore[reportUnreachable]
else:
    import tomli as tomllib  # type: ignore[no-redef]  # pyright: ignore[reportUnreachable]

VERSION = "0.31.2"
SPEC_URL = f"https://spec.commonmark.org/{VERSION}/spec.json"
LICENSE_URL = f"https://raw.githubusercontent.com/commonmark/commonmark-spec/{VERSION}/LICENSE"
SPEC_SHA256 = "d431b29d97b6f73e69d547109cf5081578fac931e72afe95639ebe766c1b2a20"
LICENSE_SHA256 = "3e4806ba6f20073e8ce40da5a0c4b59f7f44287965f538e195a4d734d833557b"
EXAMPLE_COUNT = 652
ALTERNATE_EXAMPLES = (
    4,
    15,
    26,
    43,
    62,
    80,
    108,
    120,
    192,
    219,
    227,
    234,
    255,
    301,
    350,
    482,
    572,
    607,
    618,
    633,
    650,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _download(url: str, expected_sha256: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
        data = response.read()
    actual = _sha256(data)
    if actual != expected_sha256:
        raise RuntimeError(f"checksum mismatch for {url}: expected {expected_sha256}, got {actual}")
    return data


def _examples(spec_bytes: bytes) -> list[dict[str, Any]]:
    value = cast(object, json.loads(spec_bytes))
    if not isinstance(value, list):
        raise RuntimeError(f"expected {EXAMPLE_COUNT} CommonMark examples")
    items = cast(list[object], value)
    if len(items) != EXAMPLE_COUNT or any(not isinstance(item, dict) for item in items):
        raise RuntimeError(f"expected {EXAMPLE_COUNT} CommonMark examples")
    examples = cast(list[dict[str, Any]], items)
    if [example.get("example") for example in examples] != list(range(1, EXAMPLE_COUNT + 1)):
        raise RuntimeError("CommonMark examples are not numbered consecutively")
    return examples


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown"


def _deferral(markdown: str, section: str) -> tuple[str, str, str] | None:
    if "`" in markdown or section == "Code spans":
        return "fm-ocpw", "FM-CODE-SPAN-001", "contains code-span or backtick syntax"
    if section == "HTML blocks" or re.search(r"<[/!A-Za-z][^>]*>", markdown):
        return "fm-w1tn", "FM-EXT-RAW-HTML-001", "contains raw or inline HTML syntax"
    if (markdown.count("$") >= 2) or any(token in markdown for token in (r"\(", r"\[", r"\begin{")):
        return "fm-ucy8", "FM-MATH-INLINE-001", "contains math-shaped delimiter syntax"
    return None


def _run(
    executable: Path, arguments: tuple[str, ...], stdin: bytes
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(  # noqa: S603
        (str(executable), *arguments),
        input=stdin,
        capture_output=True,
        check=False,
        timeout=30,
        env={"PATH": str(executable.parent), "NO_COLOR": "1", "LC_ALL": "C", "TZ": "UTC"},
    )


def _case_toml(
    *,
    number: int,
    section: str,
    input_path: str,
    output_path: str,
    change_id: str,
    deferred_owner: str | None,
) -> str:
    tags = ["commonmark", "default", f"section-{_slug(section)}"]
    if deferred_owner is not None:
        tags.extend(("deferred", f"owner-{deferred_owner}"))
    tag_text = ", ".join(_toml_string(tag) for tag in tags)
    return "\n".join(
        (
            "[[case]]",
            f'id = "commonmark.default.{number:04}"',
            f'change_id = "{change_id}"',
            f"description = {_toml_string(f'CommonMark {VERSION} example {number}: {section}.')}",
            'kind = "stdin"',
            f"tags = [{tag_text}]",
            'args = ["-"]',
            f'stdin = "{input_path}"',
            f'expected_stdout = "{output_path}"',
            'expected_stderr = "tests/parity_corpus/spec/commonmark-0.31.2/empty.stderr"',
            "expected_exit = 0",
            "idempotent = true",
            "",
        )
    )


def _alternate_case_toml(*, number: int, section: str, input_path: str, output_path: str) -> str:
    tags = ["alternate-mode", "commonmark", f"section-{_slug(section)}", "typography"]
    tag_text = ", ".join(_toml_string(tag) for tag in tags)
    return "\n".join(
        (
            "[[case]]",
            f'id = "commonmark.auto.{number:04}"',
            'change_id = "FM-COMMONMARK-001"',
            f"description = {_toml_string(f'CommonMark {VERSION} example {number} in the reviewed typography subset: {section}.')}",
            'kind = "stdin"',
            f"tags = [{tag_text}]",
            'args = ["--semantic", "--cleanups", "--smartquotes", "--ellipses", "-"]',
            f'stdin = "{input_path}"',
            f'expected_stdout = "{output_path}"',
            'expected_stderr = "tests/parity_corpus/spec/commonmark-0.31.2/empty.stderr"',
            "expected_exit = 0",
            "idempotent = true",
            "",
        )
    )


def import_corpus(repo_root: Path, executable: Path, *, reclassify: bool = False) -> None:
    corpus_root = repo_root / "tests/parity_corpus/spec" / f"commonmark-{VERSION}"
    registry_path = corpus_root / "manifest.toml"
    if registry_path.exists() and not reclassify:
        raise RuntimeError(f"refusing to replace existing corpus: {registry_path}")
    if not executable.is_file():
        raise RuntimeError(f"installed Flowmark executable not found: {executable}")

    if reclassify:
        spec_bytes = (corpus_root / "spec.json").read_bytes()
        license_bytes = (repo_root / "tests/parity_corpus/LICENSE-COMMONMARK").read_bytes()
        if _sha256(spec_bytes) != SPEC_SHA256 or _sha256(license_bytes) != LICENSE_SHA256:
            raise RuntimeError("cannot reclassify corpus with changed pinned sources")
    else:
        spec_bytes = _download(SPEC_URL, SPEC_SHA256)
        license_bytes = _download(LICENSE_URL, LICENSE_SHA256)
    examples = _examples(spec_bytes)
    corpus_root.mkdir(parents=True, exist_ok=True)
    (corpus_root / "spec.json").write_bytes(spec_bytes)
    (repo_root / "tests/parity_corpus/LICENSE-COMMONMARK").write_bytes(license_bytes)
    (corpus_root / "empty.stderr").write_bytes(b"")

    registry_parts = [
        "# Generated by scripts/import-commonmark-spec.py; expectations require review.",
        "schema_version = 1",
        'corpus = "flowmark-language-neutral-conformance"',
        "",
    ]
    report: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    for example in examples:
        number = cast(int, example["example"])
        section = cast(str, example["section"])
        markdown = cast(str, example["markdown"])
        source = markdown.encode("utf-8")
        case_dir = corpus_root / "examples" / f"{number:04}"
        case_dir.mkdir(parents=True, exist_ok=True)
        input_file = case_dir / "input.md"
        output_file = case_dir / "expected.default.md"
        input_file.write_bytes(source)

        deferral = _deferral(markdown, section)
        first = _run(executable, ("-",), source)
        second = _run(executable, ("-",), first.stdout) if first.returncode == 0 else first
        try:
            semantic_equal = marko.convert(markdown) == marko.convert(first.stdout.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            semantic_equal = False
        if deferral is None and (
            first.returncode != 0
            or first.stderr
            or second.returncode != 0
            or second.stderr
            or second.stdout != first.stdout
        ):
            deferral = (
                "fm-w467",
                "FM-COMMONMARK-001",
                "baseline fails, writes stderr, or is not idempotent",
            )
        if deferral is None and not semantic_equal:
            deferral = (
                "fm-w467",
                "FM-COMMONMARK-001",
                "baseline changes the parser-visible HTML structure",
            )

        if deferral is None:
            owner = None
            change_id = "FM-COMMONMARK-001"
            reason = "reviewed current behavior candidate"
            expected = first.stdout
            counts["active"] += 1
        else:
            owner, change_id, reason = deferral
            expected = source
            counts[f"deferred:{owner}"] += 1
        output_file.write_bytes(expected)

        input_path = input_file.relative_to(repo_root).as_posix()
        output_path = output_file.relative_to(repo_root).as_posix()
        registry_parts.append(
            _case_toml(
                number=number,
                section=section,
                input_path=input_path,
                output_path=output_path,
                change_id=change_id,
                deferred_owner=owner,
            )
        )
        alternate: dict[str, object] | None = None
        if number in ALTERNATE_EXAMPLES:
            if owner is not None:
                raise RuntimeError(f"alternate example {number} is no longer active by default")
            arguments = ("--semantic", "--cleanups", "--smartquotes", "--ellipses", "-")
            alternate_first = _run(executable, arguments, source)
            alternate_second = (
                _run(executable, arguments, alternate_first.stdout)
                if alternate_first.returncode == 0
                else alternate_first
            )
            if (
                alternate_first.returncode != 0
                or alternate_first.stderr
                or alternate_second.returncode != 0
                or alternate_second.stderr
                or alternate_second.stdout != alternate_first.stdout
            ):
                raise RuntimeError(f"alternate example {number} is not silent and idempotent")
            alternate_file = case_dir / "expected.auto.md"
            alternate_file.write_bytes(alternate_first.stdout)
            alternate_path = alternate_file.relative_to(repo_root).as_posix()
            registry_parts.append(
                _alternate_case_toml(
                    number=number,
                    section=section,
                    input_path=input_path,
                    output_path=alternate_path,
                )
            )
            counts["alternate-active"] += 1
            alternate = {
                "id": f"commonmark.auto.{number:04}",
                "expected_sha256": _sha256(alternate_first.stdout),
            }
        report.append(
            {
                "id": f"commonmark.default.{number:04}",
                "section": section,
                "status": "active" if owner is None else "deferred",
                "owner": owner,
                "reason": reason,
                "input_sha256": _sha256(source),
                "expected_sha256": _sha256(expected),
                "candidate_exit": first.returncode,
                "candidate_stderr_bytes": len(first.stderr),
                "candidate_idempotent": second.stdout == first.stdout,
                "candidate_semantic_equal": semantic_equal,
                "alternate": alternate,
            }
        )

    registry_path.write_text("\n".join(registry_parts), encoding="utf-8")
    (corpus_root / "review-report.json").write_text(
        json.dumps({"counts": counts, "cases": report}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Imported {EXAMPLE_COUNT} examples: {dict(sorted(counts.items()))}")


def check_corpus(repo_root: Path) -> None:
    corpus_root = repo_root / "tests/parity_corpus/spec" / f"commonmark-{VERSION}"
    spec_bytes = (corpus_root / "spec.json").read_bytes()
    license_bytes = (repo_root / "tests/parity_corpus/LICENSE-COMMONMARK").read_bytes()
    if _sha256(spec_bytes) != SPEC_SHA256 or _sha256(license_bytes) != LICENSE_SHA256:
        raise RuntimeError("pinned CommonMark source or license checksum changed")
    examples = _examples(spec_bytes)
    expected_files: set[Path] = set()
    for example in examples:
        number = cast(int, example["example"])
        source = cast(str, example["markdown"]).encode("utf-8")
        case_dir = corpus_root / "examples" / f"{number:04}"
        input_file = case_dir / "input.md"
        default_file = case_dir / "expected.default.md"
        expected_files.update((input_file, default_file))
        if input_file.read_bytes() != source:
            raise RuntimeError(f"CommonMark input drift for example {number}")
        if not default_file.is_file():
            raise RuntimeError(f"missing CommonMark expectation for example {number}")
        if number in ALTERNATE_EXAMPLES:
            alternate_file = case_dir / "expected.auto.md"
            expected_files.add(alternate_file)
            if not alternate_file.is_file():
                raise RuntimeError(f"missing alternate expectation for example {number}")

    actual_files = {path for path in (corpus_root / "examples").rglob("*") if path.is_file()}
    if actual_files != expected_files:
        extra = sorted(actual_files - expected_files)
        missing = sorted(expected_files - actual_files)
        raise RuntimeError(
            f"CommonMark extracted-file drift: extra={extra[:1]}, missing={missing[:1]}"
        )

    registry = tomllib.loads((corpus_root / "manifest.toml").read_text(encoding="utf-8"))
    raw_cases_value = cast(object, registry.get("case"))
    if not isinstance(raw_cases_value, list):
        raise RuntimeError("CommonMark registry does not contain a case array")
    raw_cases = cast(list[object], raw_cases_value)
    expected_ids = {
        *(f"commonmark.default.{number:04}" for number in range(1, EXAMPLE_COUNT + 1)),
        *(f"commonmark.auto.{number:04}" for number in ALTERNATE_EXAMPLES),
    }
    actual_ids: set[str] = set()
    cases_by_id: dict[str, dict[str, object]] = {}
    for raw_case in raw_cases:
        if not isinstance(raw_case, dict):
            raise RuntimeError("CommonMark registry contains a non-table case")
        case = cast(dict[str, object], raw_case)
        case_id = case.get("id")
        if not isinstance(case_id, str):
            raise RuntimeError("CommonMark registry contains a case without a string ID")
        actual_ids.add(case_id)
        cases_by_id[case_id] = case
    if len(raw_cases) != len(expected_ids) or actual_ids != expected_ids:
        raise RuntimeError("CommonMark registry does not cover the exact generated case set")

    for number in range(1, EXAMPLE_COUNT + 1):
        prefix = f"tests/parity_corpus/spec/commonmark-{VERSION}/examples/{number:04}"
        default_case = cases_by_id[f"commonmark.default.{number:04}"]
        if (
            default_case.get("stdin") != f"{prefix}/input.md"
            or default_case.get("expected_stdout") != f"{prefix}/expected.default.md"
        ):
            raise RuntimeError(f"CommonMark registry path drift for example {number}")
        if number in ALTERNATE_EXAMPLES:
            alternate_case = cases_by_id[f"commonmark.auto.{number:04}"]
            if (
                alternate_case.get("stdin") != f"{prefix}/input.md"
                or alternate_case.get("expected_stdout") != f"{prefix}/expected.auto.md"
            ):
                raise RuntimeError(f"CommonMark alternate path drift for example {number}")

    print(
        f"Verified CommonMark {VERSION}: {EXAMPLE_COUNT} examples, "
        f"{len(ALTERNATE_EXAMPLES)} alternate cases, and pinned checksums"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("import", "reclassify", "check"))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--flowmark-bin", type=Path)
    args = parser.parse_args()
    try:
        if args.mode in {"import", "reclassify"}:
            if args.flowmark_bin is None:
                raise RuntimeError("--flowmark-bin is required for import classification")
            import_corpus(
                args.repo_root.resolve(),
                args.flowmark_bin.resolve(),
                reclassify=args.mode == "reclassify",
            )
        else:
            check_corpus(args.repo_root.resolve())
    except (OSError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
