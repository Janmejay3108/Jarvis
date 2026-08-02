from pathlib import Path

from src.static.call_graph import build_call_chain, flatten_paths
from src.static.handler_map import HandlerMap


def _write_script(root: Path, name: str, source: str) -> str:
    relative_path = f"Synthetic.suite/Scripts/{name}.script"
    script_path = root / relative_path
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(source, encoding="utf-8")
    return relative_path


def test_call_chain_and_flattened_paths(tmp_path: Path) -> None:
    paths = {
        "A": _write_script(tmp_path, "A", "to A\nB\nend A\n"),
        "B": _write_script(tmp_path, "B", "to B\nC\nend B\n"),
        "C": _write_script(tmp_path, "C", "to C\nlog \"done\"\nend C\n"),
    }
    handler_map = HandlerMap(paths)
    test_source = (tmp_path / paths["A"]).read_text(encoding="utf-8")

    chain = build_call_chain(test_source, handler_map, str(tmp_path), depth=2)

    assert chain == {"A": ["B"], "B": ["C"], "C": []}
    assert flatten_paths(chain, handler_map) == [paths["A"], paths["B"], paths["C"]]


def test_depth_one_stops_before_transitive_callees(tmp_path: Path) -> None:
    paths = {
        "A": _write_script(tmp_path, "A", "to A\nB\nend A\n"),
        "B": _write_script(tmp_path, "B", "to B\nC\nend B\n"),
        "C": _write_script(tmp_path, "C", "to C\nend C\n"),
    }
    handler_map = HandlerMap(paths)
    test_source = (tmp_path / paths["A"]).read_text(encoding="utf-8")

    chain = build_call_chain(test_source, handler_map, str(tmp_path), depth=1)

    assert chain == {"A": ["B"], "B": []}
    assert paths["C"] not in flatten_paths(chain, handler_map)