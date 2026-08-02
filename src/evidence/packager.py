from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.integrations.dai_client import DaiClient, LogEntry


@dataclass(frozen=True)
class EvidenceBundle:
    ticket_key: str
    runid: str
    logs: list[LogEntry]
    error_index: int
    error_message: str
    screenshot_path: Path | None
    screenshot_image_id: str | None
    result_url: str

    def trimmed_log_excerpt(self, head: int = 60, tail: int = 40) -> str:
        """Return the first and last log messages for context packing."""
        messages = [entry.message or "" for entry in self.logs]
        if len(messages) <= head + tail:
            selected = messages
        elif tail == 0:
            selected = messages[:head]
        else:
            selected = [*messages[:head], *messages[-tail:]]
        return "\n".join(selected)


async def fetch_evidence(
    ticket_key: str,
    runid: str,
    error_index: int,
    dest_dir: Path,
) -> EvidenceBundle:
    """Fetch the run log and the captured frame preceding a known error."""
    async with DaiClient() as client:
        logs = await client.log_by_runid(runid)
        if not 0 <= error_index < len(logs):
            raise IndexError(
                f"error_index {error_index} is outside log range 0..{len(logs) - 1}"
            )

        screenshot_entry = client.walk_back_to_screenshot(logs, error_index)
        screenshot_path: Path | None = None
        screenshot_image_id: str | None = None
        if screenshot_entry is not None and screenshot_entry.image_id is not None:
            screenshot_image_id = screenshot_entry.image_id
            screenshot_path = dest_dir / f"{screenshot_image_id}.png"
            await client.fetch_screenshot(screenshot_image_id, screenshot_path)

        return EvidenceBundle(
            ticket_key=ticket_key,
            runid=runid,
            logs=logs,
            error_index=error_index,
            error_message=logs[error_index].message or "",
            screenshot_path=screenshot_path,
            screenshot_image_id=screenshot_image_id,
            result_url=client.result_url(runid),
        )
