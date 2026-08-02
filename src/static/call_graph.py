from __future__ import annotations

from pathlib import Path

from src.static.handler_map import HandlerMap
from src.static.sensetalk_parser import handler_calls, handler_defs

_TEST_ROOT = "__test__"


def build_call_chain(
    test_src: str,
    handler_map: HandlerMap,
    repo_root: str,
    depth: int = 3,
) -> dict[str, list[str]]:
    if depth < 0:
        raise ValueError("depth must be non-negative")

    definitions = handler_defs(test_src)
    root_name = definitions[0].name if definitions else _TEST_ROOT
    chain: dict[str, list[str]] = {}
    expanded: set[str] = set()
    root = Path(repo_root)

    def visit(name: str, source: str, remaining_depth: int) -> None:
        normalized = name.casefold()
        if normalized in expanded:
            return
        expanded.add(normalized)

        if remaining_depth == 0:
            chain[name] = []
            return

        callees = [
            call for call in handler_calls(source) if handler_map.resolve(call) is not None
        ]
        chain[name] = callees
        for callee in callees:
            relative_path = handler_map.resolve(callee)
            if relative_path is None:
                continue
            script_path = root / relative_path
            try:
                callee_source = script_path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            except FileNotFoundError as error:
                raise FileNotFoundError(
                    f"handler {callee!r} resolved to missing script {script_path}"
                ) from error
            visit(callee, callee_source, remaining_depth - 1)

    visit(root_name, test_src, depth)
    return chain


def flatten_paths(
    chain: dict[str, list[str]],
    handler_map: HandlerMap,
) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    handler_names = list(chain)
    for callees in chain.values():
        handler_names.extend(callees)

    for handler_name in handler_names:
        path = handler_map.resolve(handler_name)
        if path is not None and path not in seen:
            seen.add(path)
            paths.append(path)
    return paths
