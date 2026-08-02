import shutil
from pathlib import Path

import pytest

from src.static.ripgrep_search import find_callers


def test_find_callers_with_ripgrep(tmp_path: Path) -> None:
    if shutil.which("rg") is None:
        pytest.skip("ripgrep is not installed")

    matching = tmp_path / "Matching.script"
    other = tmp_path / "Other.script"
    ignored = tmp_path / "Ignored.txt"
    matching.write_text("targetHandler value\nlog \"targetHandler\"\n", encoding="utf-8")
    other.write_text("differentHandler\n", encoding="utf-8")
    ignored.write_text("targetHandler\n", encoding="utf-8")

    matches = find_callers("targetHandler", str(tmp_path))

    assert [(match.file, match.line) for match in matches] == [
        ("Matching.script", 1),
        ("Matching.script", 2),
    ]
    assert matches[0].text == "targetHandler value"


def test_find_callers_returns_empty_for_unknown_handler(tmp_path: Path) -> None:
    if shutil.which("rg") is None:
        pytest.skip("ripgrep is not installed")
    (tmp_path / "Only.script").write_text("knownHandler\n", encoding="utf-8")

    assert find_callers("unknownHandler", str(tmp_path)) == []