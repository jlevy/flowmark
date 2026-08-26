from __future__ import annotations

from pathlib import Path

import pytest

from flowmark.linewrapping.markdown_filling import fill_markdown
from flowmark.preservation.bridge import InvalidTokenError
from flowmark.preservation.model import InvalidUtf8Error
from flowmark.reformat_api import reformat_file, reformat_text


def test_reformat_text_does_not_implicitly_dedent_markdown() -> None:
    source = "    \\[\\]\n"

    assert reformat_text(source, width=0, semantic=False) == "```\n\\[\\]\n```\n"
    assert fill_markdown(source, width=0, semantic=False, dedent_input=True) == "\\[\\]\n"


def test_file_io_is_strict_utf8_and_preserves_bom_while_normalizing_lf(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    output = tmp_path / "output.md"
    source.write_bytes(b"\xef\xbb\xbfprefix $x_1$\r\n")

    assert reformat_file(source, output, width=0)

    assert source.read_bytes() == b"\xef\xbb\xbfprefix $x_1$\r\n"
    assert output.read_bytes() == b"\xef\xbb\xbfprefix $x_1$\n"


def test_invalid_utf8_and_restoration_failure_cannot_mutate_an_inplace_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.md"
    invalid = b"before\xffafter\n"
    source.write_bytes(invalid)

    with pytest.raises(InvalidUtf8Error, match="input is not valid UTF-8"):
        reformat_file(source, None, inplace=True, nobackup=True)
    assert source.read_bytes() == invalid

    original = b"before $x$ after\n"
    source.write_bytes(original)

    def fail_restoration(*_args: object) -> str:
        raise InvalidTokenError("injected restoration failure")

    monkeypatch.setattr(
        "flowmark.linewrapping.markdown_filling.restore_source",
        fail_restoration,
    )
    with pytest.raises(InvalidTokenError, match="injected"):
        reformat_file(source, None, inplace=True, nobackup=True)
    assert source.read_bytes() == original
