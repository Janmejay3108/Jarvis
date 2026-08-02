from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from src.static.sensetalk_parser import handler_defs
from src.static.vocabulary import HandlerEntry


def _script_files(repo_root: Path) -> list[Path]:
    scripts: list[Path] = []
    for script_path in repo_root.rglob("*.script"):
        relative_parts = script_path.relative_to(repo_root).parts
        for index, part in enumerate(relative_parts[:-1]):
            if part.casefold().endswith(".suite") and (
                index + 1 < len(relative_parts)
                and relative_parts[index + 1].casefold() == "scripts"
            ):
                scripts.append(script_path)
                break
    return sorted(scripts)


def build_vocabulary(repo_root: str, output: str) -> list[HandlerEntry]:
    root = Path(repo_root).resolve()
    entries: list[HandlerEntry] = []
    for script_path in _script_files(root):
        source = script_path.read_text(encoding="utf-8", errors="replace")
        source_lines = source.splitlines()
        relative_path = script_path.relative_to(root).as_posix()
        for definition in handler_defs(source):
            entries.append(
                HandlerEntry(
                    name=definition.name,
                    file=relative_path,
                    line=definition.line,
                    signature=source_lines[definition.line - 1].strip(),
                    params=definition.params,
                    purpose="",
                )
            )

    entries.sort(key=lambda entry: (entry.name.casefold(), entry.file, entry.line))
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([asdict(entry) for entry in entries], indent=2) + "\n",
        encoding="utf-8",
    )
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the SenseTalk vocabulary.")
    parser.add_argument("repo_root")
    parser.add_argument(
        "--output",
        default="tracks/enovia/handler_vocabulary.json",
    )
    parser.add_argument("--annotate", action="store_true")
    args = parser.parse_args()

    if args.annotate:
        print("not yet implemented")
        return 0

    entries = build_vocabulary(args.repo_root, args.output)
    print(f"Wrote {len(entries)} handlers to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
