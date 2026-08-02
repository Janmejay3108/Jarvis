from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GrepMatch:
    file: str
    line: int
    text: str


def find_callers(handler: str, repo_path: str) -> list[GrepMatch]:
    if shutil.which("rg") is None:
        raise RuntimeError("ripgrep (rg) was not found on PATH")

    root = Path(repo_path).resolve()
    pattern = rf"\b{re.escape(handler)}\b"
    result = subprocess.run(
        ["rg", "-n", "--color", "never", "--glob", "*.script", pattern, "."],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode == 1:
        return []
    if result.returncode != 0:
        message = result.stderr.strip() or "unknown ripgrep error"
        raise RuntimeError(f"ripgrep failed: {message}")

    matches: list[GrepMatch] = []
    for output_line in result.stdout.splitlines():
        match = re.match(r"^(.+?):(\d+):(.*)$", output_line)
        if match is None:
            continue
        relative_path = match.group(1).replace("\\", "/").removeprefix("./")
        matches.append(
            GrepMatch(
                file=relative_path,
                line=int(match.group(2)),
                text=match.group(3),
            )
        )
    return matches
