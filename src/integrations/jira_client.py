from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

import httpx
import structlog
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
    from src.config import Settings

logger = structlog.get_logger(__name__)


class JiraWriteUncertain(RuntimeError):
    def __init__(self, operation: str, ticket_key: str) -> None:
        self.operation = operation
        self.ticket_key = ticket_key
        super().__init__(
            f"Jira may have completed {operation} for {ticket_key}; "
            "check Jira before retrying"
        )


def _is_retryable(error: BaseException) -> bool:
    if isinstance(error, httpx.TimeoutException):
        return True
    return (
        isinstance(error, httpx.HTTPStatusError)
        and 500 <= error.response.status_code < 600
    )


class JiraClient:
    def __init__(
        self,
        config: Settings | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if config is None:
            from src.config import settings

            config = settings
        self._base_url = config.jira_base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {config.jira_pat.get_secret_value()}",
            "Accept": "application/json",
        }
        self._client = client or httpx.AsyncClient(timeout=30.0)
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = dict(self._headers)
        headers.update(kwargs.pop("headers", {}))
        response = await self._client.request(
            method,
            f"{self._base_url}{path}",
            headers=headers,
            **kwargs,
        )
        response.raise_for_status()
        return response

    @retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.25, min=0.25, max=2),
        reraise=True,
    )
    async def _read_request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        return await self._request(method, path, **kwargs)

    async def _write_request(
        self,
        method: str,
        path: str,
        *,
        operation: str,
        ticket_key: str,
        **kwargs: Any,
    ) -> httpx.Response:
        try:
            return await self._request(method, path, **kwargs)
        except (httpx.TimeoutException, httpx.HTTPStatusError) as error:
            if _is_retryable(error):
                raise JiraWriteUncertain(operation, ticket_key) from error
            raise

    async def get_ticket(self, key: str) -> dict[str, Any]:
        response = await self._read_request("GET", f"/rest/api/2/issue/{key}")
        return response.json()

    async def post_comment(self, key: str, body: str) -> None:
        await self._write_request(
            "POST",
            f"/rest/api/2/issue/{key}/comment",
            operation="post_comment",
            ticket_key=key,
            json={"body": body},
        )

    async def add_label(self, key: str, label: str) -> None:
        await self._write_request(
            "PUT",
            f"/rest/api/2/issue/{key}",
            operation="add_label",
            ticket_key=key,
            json={"update": {"labels": [{"add": label}]}},
        )

    async def add_attachment(
        self,
        key: str,
        filename: str,
        data: bytes,
        mime: str,
    ) -> list[dict[str, Any]]:
        response = await self._write_request(
            "POST",
            f"/rest/api/2/issue/{key}/attachments",
            operation="add_attachment",
            ticket_key=key,
            headers={"X-Atlassian-Token": "no-check"},
            files={"file": (filename, data, mime)},
        )
        payload = response.json()
        if not isinstance(payload, list):
            raise TypeError("Jira attachment response must be a list")
        return payload

    async def transitions(self, key: str) -> list[dict[str, Any]]:
        response = await self._read_request(
            "GET",
            f"/rest/api/2/issue/{key}/transitions",
        )
        payload = response.json()
        transitions = payload.get("transitions")
        if not isinstance(transitions, list):
            raise TypeError("Jira transitions response must contain transitions[]")
        return transitions

    async def transition(self, key: str, transition_name: str) -> None:
        available = await self.transitions(key)
        transition = next(
            (
                item
                for item in available
                if str(item.get("name", "")).casefold() == transition_name.casefold()
            ),
            None,
        )
        if transition is None:
            await logger.awarning(
                "jira_transition_not_found",
                key=key,
                transition=transition_name,
            )
            return
        await self._write_request(
            "POST",
            f"/rest/api/2/issue/{key}/transitions",
            operation="transition",
            ticket_key=key,
            json={"transition": {"id": str(transition["id"])}},
        )
