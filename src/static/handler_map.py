from __future__ import annotations

from pathlib import Path

import yaml


class HandlerMap:
    def __init__(self, data: dict[str, str]):
        self._data = dict(data)

    @classmethod
    def from_yaml(cls, path: str) -> HandlerMap:
        with Path(path).open(encoding="utf-8") as yaml_file:
            raw_data = yaml.safe_load(yaml_file) or {}
        if not isinstance(raw_data, dict) or not all(
            isinstance(name, str) and isinstance(file_path, str)
            for name, file_path in raw_data.items()
        ):
            raise ValueError("handler map must be a string-to-string YAML mapping")
        return cls(raw_data)

    def resolve(self, name: str) -> str | None:
        if name in self._data:
            return self._data[name]

        normalized = name.casefold()
        for handler_name, file_path in self._data.items():
            if handler_name.casefold() == normalized:
                return file_path

        prefix_matches = [
            (handler_name, file_path)
            for handler_name, file_path in self._data.items()
            if normalized.startswith(handler_name.casefold())
            or handler_name.casefold().startswith(normalized)
        ]
        if not prefix_matches:
            return None
        return max(prefix_matches, key=lambda item: len(item[0]))[1]

    def all_handlers(self) -> dict[str, str]:
        return dict(self._data)
