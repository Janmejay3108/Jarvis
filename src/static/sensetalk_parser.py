from __future__ import annotations

import re
from dataclasses import dataclass

_DEFINITION_RE = re.compile(
    r"^\s*(to\s+handle|to|function|on)\s+([A-Za-z_]\w*)\b(.*)$",
    re.IGNORECASE,
)
_DOTTED_CALL_RE = re.compile(r'"(?:[^"\\]|\\.)*"\s*\.\s*([A-Za-z_]\w*)')
_BARE_CALL_RE = re.compile(r"^\s*([A-Za-z_]\w*)\b")


@dataclass(frozen=True)
class HandlerDef:
    name: str
    kind: str
    params: list[str]
    line: int


def source_without_comments(text: str) -> str:
    result: list[str] = []
    index = 0
    in_block_comment = False
    in_string = False

    while index < len(text):
        pair = text[index : index + 2]
        char = text[index]

        if in_block_comment:
            if pair == "*)":
                result.extend("  ")
                index += 2
                in_block_comment = False
            else:
                result.append("\n" if char == "\n" else " ")
                index += 1
            continue

        if not in_string and pair == "(*":
            result.extend("  ")
            index += 2
            in_block_comment = True
            continue

        if not in_string and pair in {"//", "--"}:
            while index < len(text) and text[index] != "\n":
                result.append(" ")
                index += 1
            continue

        result.append(char)
        if char == '"':
            if in_string and index + 1 < len(text) and text[index + 1] == '"':
                result.append(text[index + 1])
                index += 2
                continue
            in_string = not in_string
        index += 1

    return "".join(result)


def source_without_strings(text: str) -> str:
    result: list[str] = []
    index = 0
    in_string = False
    while index < len(text):
        char = text[index]
        if char == '"':
            if in_string and index + 1 < len(text) and text[index + 1] == '"':
                result.extend("  ")
                index += 2
                continue
            in_string = not in_string
            result.append(" ")
        elif in_string:
            result.append("\n" if char == "\n" else " ")
        else:
            result.append(char)
        index += 1
    return "".join(result)


def _split_params(raw_params: str) -> list[str]:
    params: list[str] = []
    token: list[str] = []
    bracket_depth = 0
    in_string = False

    def append_token() -> None:
        raw_token = "".join(token).strip()
        token.clear()
        if not raw_token:
            return
        name = raw_token.split(":", 1)[0].strip()
        if re.fullmatch(r"[A-Za-z_]\w*", name):
            params.append(name)

    for char in raw_params.strip():
        if char == '"':
            in_string = not in_string
            token.append(char)
        elif not in_string and char in "[({":
            bracket_depth += 1
            token.append(char)
        elif not in_string and char in "]) }".replace(" ", ""):
            bracket_depth = max(0, bracket_depth - 1)
            token.append(char)
        elif not in_string and bracket_depth == 0 and (char == "," or char.isspace()):
            append_token()
        else:
            token.append(char)
    append_token()
    return params


def handler_defs(text: str) -> list[HandlerDef]:
    definitions: list[HandlerDef] = []
    for line_number, line in enumerate(source_without_comments(text).splitlines(), 1):
        match = _DEFINITION_RE.match(line)
        if match is None:
            continue
        kind = " ".join(match.group(1).lower().split())
        definitions.append(
            HandlerDef(
                name=match.group(2),
                kind=kind,
                params=_split_params(match.group(3)),
                line=line_number,
            )
        )
    return definitions


def handler_calls(text: str) -> list[str]:
    calls: list[str] = []
    seen: set[str] = set()

    def append_call(name: str) -> None:
        normalized = name.casefold()
        if normalized not in seen:
            seen.add(normalized)
            calls.append(name)

    for line in source_without_comments(text).splitlines():
        if _DEFINITION_RE.match(line):
            continue
        for match in _DOTTED_CALL_RE.finditer(line):
            append_call(match.group(1))
        bare_match = _BARE_CALL_RE.match(source_without_strings(line))
        if bare_match is not None:
            append_call(bare_match.group(1))
    return calls
