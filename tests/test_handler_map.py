from pathlib import Path

import yaml

from src.static.handler_map import HandlerMap


def test_handler_map_resolution(tmp_path: Path) -> None:
    data = {
        "clickElement": "Common.suite/Scripts/common.script",
        "EnterTextBoxByImage": "Common.suite/Scripts/common.script",
        "CommonEnovia": "EnoviaCommon.suite/Scripts/CommonEnovia.script",
        "commonScreenPart": "Common.suite/Scripts/common.script",
        "configEnovia": "Common.suite/Scripts/configEnovia.script",
        "LaunchApp": "Common.suite/Scripts/LaunchApp.script",
        "FileOperations": "Common.suite/Scripts/FileOperations.script",
        "EnoviaSearch": "Search.suite/Scripts/EnoviaSearch.script",
        "MQLTestData": "Common.suite/Scripts/MQLTestData.script",
        "WINSCP": "Common.suite/Scripts/WINSCP.script",
    }
    map_path = tmp_path / "handler_map.yaml"
    map_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    handler_map = HandlerMap.from_yaml(str(map_path))

    assert handler_map.resolve("clickElement") == data["clickElement"]
    assert handler_map.resolve("CLICKELEMENT") == data["clickElement"]
    assert handler_map.resolve("CommonEnoviaSearch") == data["CommonEnovia"]
    assert handler_map.resolve("unknownHandler") is None
    assert handler_map.all_handlers() == data


def test_all_handlers_returns_a_copy() -> None:
    handler_map = HandlerMap({"known": "Known.script"})

    returned = handler_map.all_handlers()
    returned["other"] = "Other.script"

    assert handler_map.resolve("other") is None