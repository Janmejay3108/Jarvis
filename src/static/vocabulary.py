from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class HandlerEntry:
    name: str
    file: str
    line: int
    signature: str
    params: list[str]
    purpose: str


class Vocabulary:
    def __init__(self, entries: list[HandlerEntry]):
        self._entry_list = list(entries)
        self._entries: dict[str, HandlerEntry] = {}
        for entry in entries:
            self._entries.setdefault(entry.name.casefold(), entry)

    @classmethod
    def from_json(cls, path: str) -> Vocabulary:
        with Path(path).open(encoding="utf-8") as json_file:
            raw_entries = json.load(json_file)
        if not isinstance(raw_entries, list):
            raise TypeError("vocabulary JSON must contain a list of handler entries")
        return cls([HandlerEntry(**entry) for entry in raw_entries])

    def lookup(self, name: str) -> HandlerEntry | None:
        return self._entries.get(name.casefold())

    def exists(self, name: str) -> bool:
        return self.lookup(name) is not None

    def entries(self) -> list[HandlerEntry]:
        return list(self._entry_list)

    def to_json_data(self) -> list[dict[str, object]]:
        return [asdict(entry) for entry in self._entry_list]
