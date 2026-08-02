from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

import httpx
from pydantic import BaseModel
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
    from src.config import Settings


class LogEntry(BaseModel):
    """Single DAI run log entry."""

    id: str | None = None
    eventtime: str | None = None
    testrunid: str | None = None
    message: str | None = None
    severity: str | None = None
    step_id: str | None = None
    stage: str | None = None
    message_type: str | None = None
    image_name: str | None = None
    image_id: str | None = None


def _is_retryable(error: BaseException) -> bool:
    if isinstance(error, httpx.TimeoutException):
        return True
    return (
        isinstance(error, httpx.HTTPStatusError)
        and error.response.status_code >= 500
    )


class DaiClient:
    def __init__(
        self,
        config: Settings | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if config is None:
            from src.config import settings

            config = settings
        self._settings = config
        self._client = client or httpx.AsyncClient(verify=False, timeout=120.0)
        self._owns_client = client is None
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._auth_lock = asyncio.Lock()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.aclose()

    @retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.25, min=0.25, max=2),
        reraise=True,
    )
    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        response = await self._client.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    async def authenticate(self) -> str:
        """OAuth2 client_credentials -> bearer token, cached by expiry."""
        if self._token is not None and time.monotonic() < self._token_expires_at:
            return self._token

        async with self._auth_lock:
            if self._token is not None and time.monotonic() < self._token_expires_at:
                return self._token
            response = await self._request(
                "POST",
                self._settings.dai_auth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._settings.dai_client_id.get_secret_value(),
                    "client_secret": self._settings.dai_client_secret.get_secret_value(),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            payload = response.json()
            token = payload.get("access_token")
            if not isinstance(token, str) or not token:
                raise ValueError("DAI auth response did not contain access_token")
            expires_in = float(payload.get("expires_in", 600))
            self._token = token
            self._token_expires_at = time.monotonic() + max(0.0, expires_in - 30.0)
            return token

    async def log_by_runid(self, runid: str) -> list[LogEntry]:
        """Fetch and parse the ordered production DAI log for a run."""
        token = await self.authenticate()
        url = self._settings.dai_log_by_runid_url.format(runid=runid)
        response = await self._request(
            "GET",
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )
        payload = response.json()
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict) and isinstance(payload.get("items"), list):
            items = payload["items"]
        else:
            raise TypeError("DAI run-log response must be a list or contain items[]")
        return [LogEntry.model_validate(item) for item in items]

    async def fetch_screenshot(self, image_id: str, dest: Path) -> Path:
        """Fetch a production DAI screenshot and write its PNG bytes."""
        token = await self.authenticate()
        url = self._settings.dai_screenshot_url.format(image_id=image_id)
        response = await self._request(
            "GET",
            url,
            headers={"Authorization": f"Bearer {token}"},
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(response.content)
        return dest

    def walk_back_to_screenshot(
        self,
        logs: list[LogEntry],
        error_index: int,
    ) -> LogEntry | None:
        """Return the last captured frame before the failing log entry."""
        start_index = min(error_index - 1, len(logs) - 1)
        for index in range(start_index, -1, -1):
            if logs[index].image_id:
                return logs[index]
        return None

    def result_url(self, runid: str) -> str:
        """Return the known read-only DAI URL associated with this run."""
        if "{runid}" in self._settings.dai_log_by_runid_url:
            return self._settings.dai_log_by_runid_url.format(runid=runid)
        return f"{self._settings.dai_base_url.rstrip('/')}/ai/runlogs/{runid}"
