from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Self

import pytest
from pydantic import SecretStr
from pytest_httpx import HTTPXMock

from src.evidence.packager import EvidenceBundle, fetch_evidence
from src.integrations.dai_client import DaiClient, LogEntry
from src.integrations.jira_client import JiraClient


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        dai_base_url="http://dai.test:8000",
        dai_auth_url="http://dai.test:8000/auth/token",
        dai_client_id=SecretStr("client-id"),
        dai_client_secret=SecretStr("client-secret"),
        dai_log_by_runid_url="http://dai.test:8000/ai/runlogs/{runid}",
        dai_screenshot_url="http://dai.test:8000/api/v2/screenshots/{image_id}",
        jira_base_url="https://jira.test",
        jira_pat=SecretStr("jira-token"),
    )


@pytest.mark.asyncio
async def test_dai_log_by_runid_parses_entries(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url="http://dai.test:8000/auth/token",
        json={"access_token": "token", "expires_in": 600},
    )
    httpx_mock.add_response(
        method="GET",
        url="http://dai.test:8000/ai/runlogs/30832",
        json=[
            {
                "id": 1,
                "testrunid": 30832,
                "message": "started",
                "image_id": "image-1",
            },
            {"id": "2", "message": "failed", "severity": "ERROR"},
        ],
    )

    async with DaiClient(config=_settings()) as client:
        logs = await client.log_by_runid("30832")

    assert logs == [
        LogEntry(
            id="1",
            testrunid="30832",
            message="started",
            image_id="image-1",
        ),
        LogEntry(id="2", message="failed", severity="ERROR"),
    ]


@pytest.mark.asyncio
async def test_walk_back_to_screenshot() -> None:
    logs = [
        LogEntry(message="first", image_id="image-old"),
        LogEntry(message="captured", image_id="image-nearest"),
        LogEntry(message="intermediate"),
        LogEntry(message="failure"),
    ]
    async with DaiClient(config=_settings()) as client:
        found = client.walk_back_to_screenshot(logs, error_index=3)

    assert found == logs[1]


@pytest.mark.asyncio
async def test_dai_authenticate_caches_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url="http://dai.test:8000/auth/token",
        json={"access_token": "cached-token", "expires_in": 3600},
    )

    async with DaiClient(config=_settings()) as client:
        first = await client.authenticate()
        second = await client.authenticate()

    assert first == second == "cached-token"
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_jira_get_ticket(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://jira.test/rest/api/2/issue/TESTAUTOMA-8055",
        json={"key": "TESTAUTOMA-8055", "fields": {"summary": "Failure"}},
    )

    async with JiraClient(config=_settings()) as client:
        ticket = await client.get_ticket("TESTAUTOMA-8055")

    assert ticket["key"] == "TESTAUTOMA-8055"
    assert httpx_mock.get_request().headers["Authorization"] == "Bearer jira-token"


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
