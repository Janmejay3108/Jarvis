from pathlib import Path

from scripts.build_vocabulary import build_vocabulary
from src.static.vocabulary import HandlerEntry, Vocabulary


def test_build_and_load_vocabulary(tmp_path: Path) -> None:
    script_path = tmp_path / "Common.suite" / "Scripts" / "common.script"
    script_path.parent.mkdir(parents=True)
    script_path.write_text(
        "to clickElement label,SR:[0,0,100,100]\n"
        "end clickElement\n"
        "function commonScreenPart Portion\n"
        "end function\n",
        encoding="utf-8",
    )
    output = tmp_path / "handler_vocabulary.json"

    entries = build_vocabulary(str(tmp_path), str(output))
    vocabulary = Vocabulary.from_json(str(output))

    assert len(entries) == 2
    assert vocabulary.exists("clickElement")
    assert vocabulary.exists("CLICKELEMENT")
    assert not vocabulary.exists("unknownHandler")
    entry = vocabulary.lookup("commonScreenPart")
    assert entry is not None
    assert entry.file == "Common.suite/Scripts/common.script"
    assert entry.line == 3
    assert entry.signature == "function commonScreenPart Portion"
    assert entry.params == ["Portion"]
    assert entry.purpose == ""


def test_duplicate_entries_are_preserved_with_deterministic_lookup() -> None:
    first = HandlerEntry("shared", "A.script", 1, "to shared", [], "")
    second = HandlerEntry("shared", "B.script", 2, "to shared", [], "")
    vocabulary = Vocabulary([first, second])

    assert vocabulary.lookup("shared") == first
    assert vocabulary.entries() == [first, second]