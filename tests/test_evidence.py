from __future__ import annotations

from pathlib import Path
from typing import Self

import pytest

from src.evidence.packager import EvidenceBundle, fetch_evidence
from src.integrations.dai_client import LogEntry


def test_trimmed_log_excerpt() -> None:
    bundle = EvidenceBundle(
        ticket_key="TESTAUTOMA-8055",
        runid="30832",
        logs=[LogEntry(message=f"message-{index}") for index in range(200)],
        error_index=150,
        error_message="message-150",
        screenshot_path=None,
        screenshot_image_id=None,
        result_url="http://dai.test/run/30832",
    )

    lines = bundle.trimmed_log_excerpt().splitlines()

    assert len(lines) == 100
    assert lines[:2] == ["message-0", "message-1"]
    assert lines[59] == "message-59"
    assert lines[60] == "message-160"
    assert lines[-1] == "message-199"


@pytest.mark.asyncio
async def test_fetch_evidence_assembles_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logs = [
        LogEntry(message="started"),
        LogEntry(message="captured", image_id="image-123"),
        LogEntry(message="reported failure"),
    ]

    class FakeDaiClient:
        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def log_by_runid(self, runid: str) -> list[LogEntry]:
            assert runid == "30832"
            return logs

        def walk_back_to_screenshot(
            self,
            entries: list[LogEntry],
            error_index: int,
        ) -> LogEntry | None:
            assert entries is logs
            assert error_index == 2
            return logs[1]

        async def fetch_screenshot(self, image_id: str, dest: Path) -> Path:
            assert image_id == "image-123"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"png-bytes")
            return dest

        def result_url(self, runid: str) -> str:
            return f"http://dai.test/ai/runlogs/{runid}"

    monkeypatch.setattr("src.evidence.packager.DaiClient", FakeDaiClient)

    bundle = await fetch_evidence(
        "TESTAUTOMA-8055",
        "30832",
        2,
        tmp_path / "evidence",
    )

    assert bundle.error_message == "reported failure"
    assert bundle.screenshot_image_id == "image-123"
    assert bundle.screenshot_path is not None
    assert bundle.screenshot_path.read_bytes() == b"png-bytes"
    assert bundle.result_url == "http://dai.test/ai/runlogs/30832"
