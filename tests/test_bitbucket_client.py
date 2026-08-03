from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from pydantic import SecretStr
from pytest_httpx import HTTPXMock

from src.integrations.bitbucket_client import BitbucketClient

REPO_URL = "https://bitbucket.test/rest/api/1.0/projects/EGGAUTO/repos/enovia"
BRANCH = "Testing_Mar10"


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        bitbucket_base_url="https://bitbucket.test/",
        bitbucket_pat=SecretStr("bitbucket-token"),
        track=SimpleNamespace(
            repo=SimpleNamespace(project="EGGAUTO", slug="enovia"),
        ),
    )


@pytest.mark.asyncio
async def test_read_file_sends_auth_revision_and_returns_exact_text(
    httpx_mock: HTTPXMock,
) -> None:
    content = "  to example\n  put \"caf\u00e9\"\nend example\n\n"
    url = f"{REPO_URL}/raw/Common.suite/Scripts/common.script?at={BRANCH}"
    httpx_mock.add_response(url=url, text=content)

    async with BitbucketClient(config=_settings()) as client:
        result = await client.read_file(
            "Common.suite/Scripts/common.script",
            BRANCH,
        )

    request = httpx_mock.get_request()
    assert result == content
    assert request.headers["Authorization"] == "Bearer bitbucket-token"
    assert request.headers["Accept"] == "application/json"
    assert request.url.params["at"] == BRANCH


@pytest.mark.asyncio
async def test_read_file_percent_encodes_path_and_preserves_separators(
    httpx_mock: HTTPXMock,
) -> None:
    url = f"{REPO_URL}/raw/Folder%20A/name%23100%25.script?at={BRANCH}"
    httpx_mock.add_response(url=url, text="content")

    async with BitbucketClient(config=_settings()) as client:
        result = await client.read_file("/Folder A/name#100%.script/", BRANCH)

    assert result == "content"
    assert httpx_mock.get_request().url.raw_path.startswith(
        b"/rest/api/1.0/projects/EGGAUTO/repos/enovia/raw/Folder%20A/"
    )


@pytest.mark.asyncio
async def test_read_file_rejects_empty_path_without_request(
    httpx_mock: HTTPXMock,
) -> None:
    async with BitbucketClient(config=_settings()) as client:
        with pytest.raises(ValueError, match="file path must not be empty"):
            await client.read_file("///", BRANCH)

    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_list_files_returns_ordered_single_page(httpx_mock: HTTPXMock) -> None:
    url = f"{REPO_URL}/files/Enovia/Scripts?at={BRANCH}&start=0"
    values = ["Enovia/Scripts/a.script", "Enovia/Scripts/nested/b.script"]
    httpx_mock.add_response(
        url=url,
        json={"values": values, "isLastPage": True},
    )

    async with BitbucketClient(config=_settings()) as client:
        result = await client.list_files("Enovia/Scripts", BRANCH)

    assert result == values


@pytest.mark.asyncio
async def test_list_files_root_uses_endpoint_without_trailing_slash(
    httpx_mock: HTTPXMock,
) -> None:
    url = f"{REPO_URL}/files?at={BRANCH}&start=0"
    httpx_mock.add_response(
        url=url,
        json={"values": ["README.md"], "isLastPage": True},
    )

    async with BitbucketClient(config=_settings()) as client:
        result = await client.list_files("", BRANCH)

    assert result == ["README.md"]
    assert httpx_mock.get_request().url.path.endswith("/files")


@pytest.mark.asyncio
async def test_list_files_uses_server_next_start_and_preserves_order(
    httpx_mock: HTTPXMock,
) -> None:
    endpoint = f"{REPO_URL}/files/Enovia?at={BRANCH}"
    httpx_mock.add_response(
        url=f"{endpoint}&start=0",
        json={
            "values": ["Enovia/first.script"],
            "isLastPage": False,
            "nextPageStart": 17,
        },
    )
    httpx_mock.add_response(
        url=f"{endpoint}&start=17",
        json={"values": ["Enovia/second.script"], "isLastPage": True},
    )

    async with BitbucketClient(config=_settings()) as client:
        result = await client.list_files("Enovia", BRANCH)

    assert result == ["Enovia/first.script", "Enovia/second.script"]
    requests = httpx_mock.get_requests()
    assert [request.url.params["start"] for request in requests] == ["0", "17"]
    assert [request.url.params["at"] for request in requests] == [BRANCH, BRANCH]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, message",
    [
        ([], "must be an object"),
        ({"isLastPage": True}, r"values\[\]"),
        ({"values": {}, "isLastPage": True}, r"values\[\]"),
        (
            {"values": ["good.script", 3], "isLastPage": True},
            r"values\[\] must contain strings",
        ),
    ],
)
async def test_list_files_rejects_malformed_values(
    httpx_mock: HTTPXMock,
    payload: Any,
    message: str,
) -> None:
    httpx_mock.add_response(
        url=f"{REPO_URL}/files?at={BRANCH}&start=0",
        json=payload,
    )

    async with BitbucketClient(config=_settings()) as client:
        with pytest.raises(TypeError, match=message):
            await client.list_files("", BRANCH)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, message",
    [
        ({"values": [], "isLastPage": "false"}, "isLastPage"),
        ({"values": [], "isLastPage": False}, "nextPageStart"),
        (
            {"values": [], "isLastPage": False, "nextPageStart": True},
            "nextPageStart",
        ),
        (
            {"values": [], "isLastPage": False, "nextPageStart": 0},
            "nextPageStart",
        ),
    ],
)
async def test_list_files_rejects_malformed_page_state_without_followup_request(
    httpx_mock: HTTPXMock,
    payload: dict[str, Any],
    message: str,
) -> None:
    httpx_mock.add_response(
        url=f"{REPO_URL}/files?at={BRANCH}&start=0",
        json=payload,
    )

    async with BitbucketClient(config=_settings()) as client:
        with pytest.raises(TypeError, match=message):
            await client.list_files("", BRANCH)

    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_read_timeout_retries_and_succeeds_on_third_attempt(
    httpx_mock: HTTPXMock,
) -> None:
    url = f"{REPO_URL}/raw/file.script?at={BRANCH}"
    httpx_mock.add_exception(httpx.ReadTimeout("first"), url=url)
    httpx_mock.add_exception(httpx.ReadTimeout("second"), url=url)
    httpx_mock.add_response(url=url, text="content")

    async with BitbucketClient(config=_settings()) as client:
        result = await client.read_file("file.script", BRANCH)

    assert result == "content"
    assert len(httpx_mock.get_requests()) == 3


@pytest.mark.asyncio
async def test_later_page_5xx_retries_only_that_page_without_duplicate_values(
    httpx_mock: HTTPXMock,
) -> None:
    endpoint = f"{REPO_URL}/files?at={BRANCH}"
    httpx_mock.add_response(
        url=f"{endpoint}&start=0",
        json={"values": ["first.script"], "isLastPage": False, "nextPageStart": 7},
    )
    httpx_mock.add_response(url=f"{endpoint}&start=7", status_code=503)
    httpx_mock.add_response(
        url=f"{endpoint}&start=7",
        json={"values": ["second.script"], "isLastPage": True},
    )

    async with BitbucketClient(config=_settings()) as client:
        result = await client.list_files("", BRANCH)

    assert result == ["first.script", "second.script"]
    requests = httpx_mock.get_requests()
    assert [request.url.params["start"] for request in requests] == ["0", "7", "7"]


@pytest.mark.asyncio
async def test_client_error_is_not_retried(httpx_mock: HTTPXMock) -> None:
    url = f"{REPO_URL}/raw/missing.script?at={BRANCH}"
    httpx_mock.add_response(url=url, status_code=404)

    async with BitbucketClient(config=_settings()) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.read_file("missing.script", BRANCH)

    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_context_closes_owned_client_but_not_injected_client() -> None:
    injected = httpx.AsyncClient()
    async with BitbucketClient(config=_settings(), client=injected):
        pass
    assert not injected.is_closed
    await injected.aclose()

    client = BitbucketClient(config=_settings())
    owned = client._client
    await client.aclose()
    assert owned.is_closed
