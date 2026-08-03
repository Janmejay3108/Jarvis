from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from pydantic import SecretStr
from pytest_httpx import HTTPXMock
from structlog.testing import capture_logs

from src.integrations.jira_client import JiraClient, JiraWriteUncertain

TICKET_KEY = "TESTAUTOMA-8055"
ISSUE_URL = f"https://jira.test/rest/api/2/issue/{TICKET_KEY}"


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        jira_base_url="https://jira.test/",
        jira_pat=SecretStr("jira-token"),
    )


async def _invoke_write(
    client: JiraClient,
    operation: str,
) -> Any:
    if operation == "post_comment":
        return await client.post_comment(TICKET_KEY, "Diagnosis body")
    if operation == "add_label":
        return await client.add_label(TICKET_KEY, "ai-diagnosed")
    if operation == "add_attachment":
        return await client.add_attachment(
            TICKET_KEY,
            "evidence.txt",
            b"evidence-bytes",
            "text/plain",
        )
    if operation == "transition":
        return await client.transition(TICKET_KEY, "Done")
    raise AssertionError(f"Unsupported test operation: {operation}")


def _write_url(operation: str) -> str:
    suffix = {
        "post_comment": "/comment",
        "add_label": "",
        "add_attachment": "/attachments",
        "transition": "/transitions",
    }[operation]
    return f"{ISSUE_URL}{suffix}"


def _write_method(operation: str) -> str:
    return {
        "post_comment": "POST",
        "add_label": "PUT",
        "add_attachment": "POST",
        "transition": "POST",
    }[operation]


def _prepare_transition(httpx_mock: HTTPXMock, operation: str) -> None:
    if operation == "transition":
        httpx_mock.add_response(
            method="GET",
            url=f"{ISSUE_URL}/transitions",
            json={"transitions": [{"id": 31, "name": "Done"}]},
        )


def _write_requests(httpx_mock: HTTPXMock, operation: str) -> list[httpx.Request]:
    return [
        request
        for request in httpx_mock.get_requests()
        if request.method == _write_method(operation)
        and str(request.url) == _write_url(operation)
    ]


@pytest.mark.asyncio
async def test_get_ticket_sends_auth_and_returns_complete_payload(
    httpx_mock: HTTPXMock,
) -> None:
    payload = {
        "key": TICKET_KEY,
        "fields": {
            "summary": "Failure",
            "customfield_12345": {"runid": "30832"},
            "comment": {"comments": [{"body": "RUN ID: 30832"}]},
            "attachment": [{"filename": "runid-30832.txt"}],
        },
    }
    httpx_mock.add_response(method="GET", url=ISSUE_URL, json=payload)

    async with JiraClient(config=_settings()) as client:
        ticket = await client.get_ticket(TICKET_KEY)

    request = httpx_mock.get_request()
    assert ticket == payload
    assert request.headers["Authorization"] == "Bearer jira-token"
    assert request.headers["Accept"] == "application/json"


@pytest.mark.asyncio
async def test_post_comment_sends_body_and_returns_comment(
    httpx_mock: HTTPXMock,
) -> None:
    comment = {"id": "101", "body": "*Diagnosis* body"}
    httpx_mock.add_response(
        method="POST",
        url=f"{ISSUE_URL}/comment",
        status_code=201,
        json=comment,
    )

    async with JiraClient(config=_settings()) as client:
        result = await client.post_comment(TICKET_KEY, "*Diagnosis* body")

    assert result == comment
    assert httpx_mock.get_request().read() == b'{"body":"*Diagnosis* body"}'


@pytest.mark.asyncio
async def test_add_label_sends_update_payload_and_accepts_no_content(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(method="PUT", url=ISSUE_URL, status_code=204)

    async with JiraClient(config=_settings()) as client:
        result = await client.add_label(TICKET_KEY, "ai-diagnosed")

    assert result is None
    assert httpx_mock.get_request().read() == (
        b'{"update":{"labels":[{"add":"ai-diagnosed"}]}}'
    )


@pytest.mark.asyncio
async def test_add_attachment_sends_multipart_and_returns_list(
    httpx_mock: HTTPXMock,
) -> None:
    attachments = [{"id": "202", "filename": "evidence.txt", "size": 14}]
    httpx_mock.add_response(
        method="POST",
        url=f"{ISSUE_URL}/attachments",
        json=attachments,
    )

    async with JiraClient(config=_settings()) as client:
        result = await client.add_attachment(
            TICKET_KEY,
            "evidence.txt",
            b"evidence-bytes",
            "text/plain",
        )

    request = httpx_mock.get_request()
    body = request.read()
    assert result == attachments
    assert request.headers["Authorization"] == "Bearer jira-token"
    assert request.headers["X-Atlassian-Token"] == "no-check"
    assert request.headers["Content-Type"].startswith("multipart/form-data; boundary=")
    assert b'name="file"' in body
    assert b'filename="evidence.txt"' in body
    assert b"Content-Type: text/plain" in body
    assert b"evidence-bytes" in body


@pytest.mark.asyncio
async def test_add_attachment_rejects_non_list_response(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{ISSUE_URL}/attachments",
        json={"id": "202"},
    )

    async with JiraClient(config=_settings()) as client:
        with pytest.raises(TypeError, match="Jira attachment response must be a list"):
            await client.add_attachment(
                TICKET_KEY,
                "evidence.txt",
                b"evidence-bytes",
                "text/plain",
            )


@pytest.mark.asyncio
async def test_transitions_returns_response_list(httpx_mock: HTTPXMock) -> None:
    transitions = [{"id": "31", "name": "Done"}]
    httpx_mock.add_response(
        method="GET",
        url=f"{ISSUE_URL}/transitions",
        json={"transitions": transitions},
    )

    async with JiraClient(config=_settings()) as client:
        result = await client.transitions(TICKET_KEY)

    assert result == transitions


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [{}, {"transitions": {"id": "31"}}])
async def test_transitions_rejects_missing_or_non_list_payload(
    httpx_mock: HTTPXMock,
    payload: dict[str, Any],
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{ISSUE_URL}/transitions",
        json=payload,
    )

    async with JiraClient(config=_settings()) as client:
        with pytest.raises(
            TypeError,
            match=r"Jira transitions response must contain transitions\[\]",
        ):
            await client.transitions(TICKET_KEY)


@pytest.mark.asyncio
async def test_transition_matches_case_insensitively_and_posts_id(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{ISSUE_URL}/transitions",
        json={"transitions": [{"id": 31, "name": "Ready For Review"}]},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{ISSUE_URL}/transitions",
        status_code=204,
    )

    async with JiraClient(config=_settings()) as client:
        result = await client.transition(TICKET_KEY, "ready for review")

    requests = httpx_mock.get_requests()
    assert result is None
    assert [request.method for request in requests] == ["GET", "POST"]
    assert requests[1].read() == b'{"transition":{"id":"31"}}'


@pytest.mark.asyncio
async def test_transition_missing_name_warns_without_post(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{ISSUE_URL}/transitions",
        json={"transitions": [{"id": "31", "name": "Done"}]},
    )

    with capture_logs() as logs:
        async with JiraClient(config=_settings()) as client:
            result = await client.transition(TICKET_KEY, "Reopen")

    assert result is None
    assert len(httpx_mock.get_requests()) == 1
    assert logs == [
        {
            "event": "jira_transition_not_found",
            "key": TICKET_KEY,
            "log_level": "warning",
            "transition": "Reopen",
        }
    ]


@pytest.mark.asyncio
async def test_read_timeout_retries_and_succeeds_on_third_attempt(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_exception(httpx.ReadTimeout("first"), method="GET", url=ISSUE_URL)
    httpx_mock.add_exception(httpx.ReadTimeout("second"), method="GET", url=ISSUE_URL)
    httpx_mock.add_response(method="GET", url=ISSUE_URL, json={"key": TICKET_KEY})

    async with JiraClient(config=_settings()) as client:
        result = await client.get_ticket(TICKET_KEY)

    assert result == {"key": TICKET_KEY}
    assert len(httpx_mock.get_requests()) == 3


@pytest.mark.asyncio
async def test_read_server_error_retries_and_succeeds_on_third_attempt(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(method="GET", url=ISSUE_URL, status_code=500)
    httpx_mock.add_response(method="GET", url=ISSUE_URL, status_code=503)
    httpx_mock.add_response(method="GET", url=ISSUE_URL, json={"key": TICKET_KEY})

    async with JiraClient(config=_settings()) as client:
        result = await client.get_ticket(TICKET_KEY)

    assert result == {"key": TICKET_KEY}
    assert len(httpx_mock.get_requests()) == 3


@pytest.mark.asyncio
async def test_read_client_error_is_not_retried(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(method="GET", url=ISSUE_URL, status_code=404)

    async with JiraClient(config=_settings()) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_ticket(TICKET_KEY)

    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation",
    ["post_comment", "add_label", "add_attachment", "transition"],
)
async def test_write_timeout_is_uncertain_and_not_retried(
    httpx_mock: HTTPXMock,
    operation: str,
) -> None:
    _prepare_transition(httpx_mock, operation)
    httpx_mock.add_exception(
        httpx.ReadTimeout("response lost"),
        method=_write_method(operation),
        url=_write_url(operation),
    )

    async with JiraClient(config=_settings()) as client:
        with pytest.raises(JiraWriteUncertain) as caught:
            await _invoke_write(client, operation)

    assert caught.value.operation == operation
    assert caught.value.ticket_key == TICKET_KEY
    assert len(_write_requests(httpx_mock, operation)) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation",
    ["post_comment", "add_label", "add_attachment", "transition"],
)
async def test_write_server_error_is_uncertain_and_not_retried(
    httpx_mock: HTTPXMock,
    operation: str,
) -> None:
    _prepare_transition(httpx_mock, operation)
    httpx_mock.add_response(
        method=_write_method(operation),
        url=_write_url(operation),
        status_code=503,
        text="server-secret-response",
    )

    async with JiraClient(config=_settings()) as client:
        with pytest.raises(JiraWriteUncertain) as caught:
            await _invoke_write(client, operation)

    assert caught.value.operation == operation
    assert caught.value.ticket_key == TICKET_KEY
    assert len(_write_requests(httpx_mock, operation)) == 1


@pytest.mark.asyncio
async def test_write_client_error_remains_http_status_error(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{ISSUE_URL}/comment",
        status_code=403,
    )

    async with JiraClient(config=_settings()) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.post_comment(TICKET_KEY, "Diagnosis body")

    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_uncertain_write_error_is_redacted(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{ISSUE_URL}/attachments",
        status_code=503,
        text="server-secret-response",
    )

    async with JiraClient(config=_settings()) as client:
        with pytest.raises(JiraWriteUncertain) as caught:
            await client.add_attachment(
                TICKET_KEY,
                "secret-name.txt",
                b"secret-attachment-bytes",
                "application/secret-mime",
            )

    public_text = f"{caught.value!s} {caught.value.operation} {caught.value.ticket_key}"
    assert "add_attachment" in public_text
    assert TICKET_KEY in public_text
    for secret in (
        "jira-token",
        "secret-name.txt",
        "secret-attachment-bytes",
        "application/secret-mime",
        "https://jira.test",
        "server-secret-response",
        "503",
    ):
        assert secret not in public_text


@pytest.mark.asyncio
async def test_injected_client_remains_open_after_close() -> None:
    injected = httpx.AsyncClient()
    try:
        client = JiraClient(config=_settings(), client=injected)
        await client.aclose()
        assert injected.is_closed is False
    finally:
        await injected.aclose()


@pytest.mark.asyncio
async def test_owned_client_closes_with_context_manager() -> None:
    client = JiraClient(config=_settings())

    async with client:
        assert client._client.is_closed is False

    assert client._client.is_closed is True
