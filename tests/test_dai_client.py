from __future__ import annotations

import asyncio
from json import JSONDecodeError
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qs

import httpx
import pytest
from pydantic import SecretStr
from pytest_httpx import HTTPXMock

from src.integrations.dai_client import DaiClient, LogEntry

AUTH_URL = "http://production-dai.test/auth/token"
LOG_URL = "http://production-dai.test/ai/runlogs/{runid}"
SCREENSHOT_URL = "http://production-dai.test/api/v2/screenshots/{image_id}"
PNG = b"\x89PNG\r\n\x1a\nproduction-image"


def _settings(**overrides: Any) -> SimpleNamespace:
    values = {
        "dai_base_url": "http://production-dai.test",
        "dai_auth_url": AUTH_URL,
        "dai_client_id": SecretStr("production-client"),
        "dai_client_secret": SecretStr("production-secret"),
        "dai_log_by_runid_url": LOG_URL,
        "dai_screenshot_url": SCREENSHOT_URL,
        "jarvis_dai_base_url": "https://jarvis-dai.invalid:8000",
        "jarvis_dai_client_id": SecretStr("jarvis-client"),
        "jarvis_dai_client_secret": SecretStr("jarvis-secret"),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _add_auth(
    httpx_mock: HTTPXMock,
    token: str = "production-token",
    expires_in: Any = 600,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=AUTH_URL,
        json={"access_token": token, "expires_in": expires_in},
    )


@pytest.mark.asyncio
async def test_authenticate_posts_form_credentials_without_url_secrets(
    httpx_mock: HTTPXMock,
) -> None:
    _add_auth(httpx_mock)

    async with DaiClient(config=_settings()) as client:
        token = await client.authenticate()

    request = httpx_mock.get_request()
    assert token == "production-token"
    assert request.url == httpx.URL(AUTH_URL)
    assert request.url.username == ""
    assert request.url.password == ""
    assert request.headers["Content-Type"].startswith(
        "application/x-www-form-urlencoded"
    )
    assert parse_qs(request.content.decode()) == {
        "grant_type": ["client_credentials"],
        "client_id": ["production-client"],
        "client_secret": ["production-secret"],
    }


@pytest.mark.asyncio
async def test_authenticate_caches_token_before_skewed_expiry(
    httpx_mock: HTTPXMock,
) -> None:
    _add_auth(httpx_mock, expires_in=60)
    clock = 100.0

    async with DaiClient(config=_settings()) as client:
        client._clock = lambda: clock
        first = await client.authenticate()
        clock = 129.9
        second = await client.authenticate()

    assert first == second == "production-token"
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_authenticate_refreshes_at_skewed_monotonic_expiry(
    httpx_mock: HTTPXMock,
) -> None:
    _add_auth(httpx_mock, token="first", expires_in=60)
    _add_auth(httpx_mock, token="second", expires_in=60)
    clock = 100.0

    async with DaiClient(config=_settings()) as client:
        client._clock = lambda: clock
        first = await client.authenticate()
        clock = 130.0
        second = await client.authenticate()

    assert (first, second) == ("first", "second")
    assert len(httpx_mock.get_requests()) == 2


@pytest.mark.asyncio
async def test_authenticate_concurrent_calls_share_one_cache_fill(
    httpx_mock: HTTPXMock,
) -> None:
    _add_auth(httpx_mock)

    async with DaiClient(config=_settings()) as client:
        tokens = await asyncio.gather(*(client.authenticate() for _ in range(5)))

    assert tokens == ["production-token"] * 5
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"access_token": "", "expires_in": 600},
        {"access_token": "   ", "expires_in": 600},
        {"access_token": "secret"},
        {"access_token": "secret", "expires_in": "not-numeric"},
        {"access_token": "secret", "expires_in": "nan"},
        {"access_token": "secret", "expires_in": "inf"},
        {"access_token": "secret", "expires_in": 0},
        {"access_token": "secret", "expires_in": -1},
        {"access_token": "secret", "expires_in": True},
    ],
)
async def test_authenticate_rejects_malformed_lifetime_without_caching(
    httpx_mock: HTTPXMock,
    payload: dict[str, Any],
) -> None:
    httpx_mock.add_response(method="POST", url=AUTH_URL, json=payload)

    async with DaiClient(config=_settings()) as client:
        with pytest.raises((TypeError, ValueError), match="DAI auth response") as error:
            await client.authenticate()
        assert client._token is None

    assert "production-secret" not in str(error.value)
    assert "secret" not in str(error.value)


@pytest.mark.asyncio
async def test_log_by_runid_parses_envelope_all_fields_and_numeric_ids(
    httpx_mock: HTTPXMock,
) -> None:
    _add_auth(httpx_mock)
    first = {
        "id": 1,
        "eventtime": "2026-08-04T12:00:00Z",
        "testrunid": 30832,
        "message": "captured",
        "severity": "INFORMATIONAL",
        "step_id": "step-1",
        "stage": "execution",
        "message_type": "imagefound",
        "image_name": "screen.png",
        "image_id": "image-1",
        "unknown": "ignored",
    }
    second = {"id": "2", "message": "failed"}
    httpx_mock.add_response(
        method="GET",
        url="http://production-dai.test/ai/runlogs/30832",
        json={"items": [first, second], "total_count": 2, "date_as_of": "now"},
    )

    async with DaiClient(config=_settings()) as client:
        logs = await client.log_by_runid("30832")

    assert logs == [
        LogEntry(
            id="1",
            eventtime="2026-08-04T12:00:00Z",
            testrunid="30832",
            message="captured",
            severity="INFORMATIONAL",
            step_id="step-1",
            stage="execution",
            message_type="imagefound",
            image_name="screen.png",
            image_id="image-1",
        ),
        LogEntry(id="2", message="failed"),
    ]
    assert [entry.id for entry in logs] == ["1", "2"]


@pytest.mark.asyncio
async def test_log_by_runid_accepts_proven_bare_list(
    httpx_mock: HTTPXMock,
) -> None:
    _add_auth(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url="http://production-dai.test/ai/runlogs/30832",
        json=[{"id": 1, "testrunid": 30832, "message": "started"}],
    )

    async with DaiClient(config=_settings()) as client:
        logs = await client.log_by_runid("30832")

    assert logs == [LogEntry(id="1", testrunid="30832", message="started")]


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [{}, {"items": {}}, "wrong", ["wrong"]])
async def test_log_by_runid_rejects_malformed_shapes(
    httpx_mock: HTTPXMock,
    payload: Any,
) -> None:
    _add_auth(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url="http://production-dai.test/ai/runlogs/30832",
        json=payload,
    )

    async with DaiClient(config=_settings()) as client:
        with pytest.raises(TypeError, match="DAI run-log"):
            await client.log_by_runid("30832")


@pytest.mark.asyncio
@pytest.mark.parametrize("runid", ["", "   "])
async def test_log_by_runid_rejects_empty_id_before_request(
    httpx_mock: HTTPXMock,
    runid: str,
) -> None:
    async with DaiClient(config=_settings()) as client:
        with pytest.raises(ValueError, match="runid must not be empty"):
            await client.log_by_runid(runid)

    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_log_by_runid_requires_template_before_request(
    httpx_mock: HTTPXMock,
) -> None:
    settings = _settings(dai_log_by_runid_url="http://production-dai.test/logs")

    async with DaiClient(config=settings) as client:
        with pytest.raises(ValueError, match=r"must contain \{runid\}"):
            await client.log_by_runid("30832")

    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_log_by_runid_encodes_id_as_one_path_component(
    httpx_mock: HTTPXMock,
) -> None:
    _add_auth(httpx_mock)
    expected = "http://production-dai.test/ai/runlogs/run%2Fid%3Fx%3D1"
    httpx_mock.add_response(method="GET", url=expected, json=[])

    async with DaiClient(config=_settings()) as client:
        assert await client.log_by_runid("run/id?x=1") == []

    request = httpx_mock.get_requests()[-1]
    assert request.url.raw_path == b"/ai/runlogs/run%2Fid%3Fx%3D1"


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [httpx.ReadTimeout("timeout"), 503])
async def test_log_request_retries_timeout_or_5xx_to_third_attempt(
    httpx_mock: HTTPXMock,
    failure: httpx.ReadTimeout | int,
) -> None:
    _add_auth(httpx_mock)
    url = "http://production-dai.test/ai/runlogs/30832"
    for _ in range(2):
        if isinstance(failure, int):
            httpx_mock.add_response(method="GET", url=url, status_code=failure)
        else:
            httpx_mock.add_exception(failure, method="GET", url=url)
    httpx_mock.add_response(method="GET", url=url, json=[])

    async with DaiClient(config=_settings()) as client:
        assert await client.log_by_runid("30832") == []

    assert len([request for request in httpx_mock.get_requests() if request.method == "GET"]) == 3


@pytest.mark.asyncio
async def test_log_request_does_not_retry_4xx(httpx_mock: HTTPXMock) -> None:
    _add_auth(httpx_mock)
    url = "http://production-dai.test/ai/runlogs/30832"
    httpx_mock.add_response(method="GET", url=url, status_code=404)

    async with DaiClient(config=_settings()) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.log_by_runid("30832")

    assert len([request for request in httpx_mock.get_requests() if request.method == "GET"]) == 1


@pytest.mark.asyncio
async def test_log_request_does_not_retry_malformed_json(
    httpx_mock: HTTPXMock,
) -> None:
    _add_auth(httpx_mock)
    url = "http://production-dai.test/ai/runlogs/30832"
    httpx_mock.add_response(
        method="GET",
        url=url,
        content=b"{",
        headers={"Content-Type": "application/json"},
    )

    async with DaiClient(config=_settings()) as client:
        with pytest.raises(JSONDecodeError):
            await client.log_by_runid("30832")

    assert len([request for request in httpx_mock.get_requests() if request.method == "GET"]) == 1


@pytest.mark.asyncio
async def test_fetch_screenshot_validates_png_and_writes_atomically(
    httpx_mock: HTTPXMock,
    tmp_path: Path,
) -> None:
    _add_auth(httpx_mock)
    url = "http://production-dai.test/api/v2/screenshots/image-1"
    httpx_mock.add_response(method="GET", url=url, content=PNG)
    destination = tmp_path / "nested" / "evidence.png"

    async with DaiClient(config=_settings()) as client:
        result = await client.fetch_screenshot("image-1", destination)

    request = httpx_mock.get_requests()[-1]
    assert result == destination
    assert destination.read_bytes() == PNG
    assert request.headers["Authorization"] == "Bearer production-token"
    assert request.headers["Accept"] == "image/png"
    assert list(destination.parent.glob(f".{destination.name}.*.tmp")) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [b"", b"<html>not an image</html>"])
async def test_fetch_screenshot_rejects_non_png_without_touching_destination(
    httpx_mock: HTTPXMock,
    tmp_path: Path,
    body: bytes,
) -> None:
    _add_auth(httpx_mock)
    url = "http://production-dai.test/api/v2/screenshots/image-1"
    httpx_mock.add_response(method="GET", url=url, content=body)
    destination = tmp_path / "evidence.png"
    destination.write_bytes(b"existing")

    async with DaiClient(config=_settings()) as client:
        with pytest.raises(ValueError, match="not a PNG"):
            await client.fetch_screenshot("image-1", destination)

    assert destination.read_bytes() == b"existing"
    assert list(tmp_path.glob(f".{destination.name}.*.tmp")) == []


@pytest.mark.asyncio
async def test_fetch_screenshot_rejects_invalid_input_before_request(
    httpx_mock: HTTPXMock,
    tmp_path: Path,
) -> None:
    async with DaiClient(config=_settings()) as client:
        with pytest.raises(ValueError, match="image_id must not be empty"):
            await client.fetch_screenshot(" ", tmp_path / "evidence.png")
        with pytest.raises(ValueError, match="destination must include a filename"):
            await client.fetch_screenshot("image-1", Path("."))

    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_fetch_screenshot_requires_template_before_request(
    httpx_mock: HTTPXMock,
    tmp_path: Path,
) -> None:
    settings = _settings(
        dai_screenshot_url="http://production-dai.test/api/v2/screenshots"
    )

    async with DaiClient(config=settings) as client:
        with pytest.raises(ValueError, match=r"must contain \{image_id\}"):
            await client.fetch_screenshot("image-1", tmp_path / "evidence.png")

    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_fetch_screenshot_encodes_id_without_changing_destination(
    httpx_mock: HTTPXMock,
    tmp_path: Path,
) -> None:
    _add_auth(httpx_mock)
    expected = "http://production-dai.test/api/v2/screenshots/folder%2Fimage%3Fx"
    httpx_mock.add_response(method="GET", url=expected, content=PNG)
    destination = tmp_path / "chosen.png"

    async with DaiClient(config=_settings()) as client:
        result = await client.fetch_screenshot("folder/image?x", destination)

    assert result == destination
    assert result.name == "chosen.png"
    assert httpx_mock.get_requests()[-1].url.raw_path.endswith(
        b"/screenshots/folder%2Fimage%3Fx"
    )


def test_walk_back_to_screenshot_uses_nearest_prior_capture() -> None:
    logs = [
        LogEntry(message="old", image_id="image-old"),
        LogEntry(message="nearest", image_id="image-nearest"),
        LogEntry(message="intermediate"),
        LogEntry(message="failure", image_id="image-on-error"),
    ]
    client = DaiClient(config=_settings(), client=httpx.AsyncClient())

    assert client.walk_back_to_screenshot(logs, 3) == logs[1]
    assert client.walk_back_to_screenshot(logs, 0) is None


@pytest.mark.parametrize("error_index", [-1, 1])
def test_walk_back_to_screenshot_rejects_invalid_index(error_index: int) -> None:
    client = DaiClient(config=_settings(), client=httpx.AsyncClient())

    with pytest.raises(IndexError, match="outside the log"):
        client.walk_back_to_screenshot([LogEntry(message="only")], error_index)


def test_result_url_is_encoded_configured_read_only_url() -> None:
    client = DaiClient(config=_settings(), client=httpx.AsyncClient())

    result = client.result_url("run/id?x=1")

    assert result == "http://production-dai.test/ai/runlogs/run%2Fid%3Fx%3D1"
    assert "production-secret" not in result


@pytest.mark.parametrize(
    ("settings", "runid", "message"),
    [
        (_settings(), " ", "runid must not be empty"),
        (
            _settings(dai_log_by_runid_url="http://production-dai.test/logs"),
            "30832",
            r"must contain \{runid\}",
        ),
        (
            _settings(
                dai_log_by_runid_url=(
                    "http://user:password@production-dai.test/logs/{runid}"
                )
            ),
            "30832",
            "must not contain credentials",
        ),
    ],
)
def test_result_url_rejects_unsafe_input(
    settings: SimpleNamespace,
    runid: str,
    message: str,
) -> None:
    client = DaiClient(config=settings, client=httpx.AsyncClient())

    with pytest.raises(ValueError, match=message):
        client.result_url(runid)


@pytest.mark.asyncio
async def test_client_closes_owned_but_not_injected_client() -> None:
    injected = httpx.AsyncClient()
    async with DaiClient(config=_settings(), client=injected):
        pass
    assert not injected.is_closed
    await injected.aclose()

    client = DaiClient(config=_settings())
    owned = client._client
    await client.aclose()
    assert owned.is_closed


@pytest.mark.asyncio
async def test_production_client_never_uses_jarvis_dai_settings(
    httpx_mock: HTTPXMock,
    tmp_path: Path,
) -> None:
    _add_auth(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url="http://production-dai.test/ai/runlogs/30832",
        json=[{"message": "failure", "image_id": "image-1"}],
    )
    httpx_mock.add_response(
        method="GET",
        url="http://production-dai.test/api/v2/screenshots/image-1",
        content=PNG,
    )

    async with DaiClient(config=_settings()) as client:
        logs = await client.log_by_runid("30832")
        await client.fetch_screenshot("image-1", tmp_path / "evidence.png")

    assert logs[0].image_id == "image-1"
    assert all(
        request.url.host == "production-dai.test"
        for request in httpx_mock.get_requests()
    )
