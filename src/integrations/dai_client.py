from __future__ import annotations

import asyncio
import math
import os
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self
from urllib.parse import quote, urlsplit

import httpx
from pydantic import BaseModel, ConfigDict
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
    from src.config import Settings


class LogEntry(BaseModel):
    """Single DAI run log entry."""

    model_config = ConfigDict(coerce_numbers_to_str=True, extra="ignore")

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


def _validated_value(value: str, name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _format_endpoint(template: str, placeholder: str, value: str) -> str:
    marker = "{" + placeholder + "}"
    if marker not in template:
        raise ValueError(f"DAI URL template must contain {marker}")
    url = template.format(**{placeholder: quote(value, safe="")})
    parsed = urlsplit(url)
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("DAI URL must not contain credentials")
    return url


def _validated_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("DAI URL must not contain credentials")
    return url


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
        self._client = client or httpx.AsyncClient(timeout=120.0)
        self._owns_client = client is None
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._auth_lock = asyncio.Lock()
        self._clock = time.monotonic

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
        if self._token is not None and self._clock() < self._token_expires_at:
            return self._token

        async with self._auth_lock:
            if self._token is not None and self._clock() < self._token_expires_at:
                return self._token
            response = await self._request(
                "POST",
                _validated_url(self._settings.dai_auth_url),
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._settings.dai_client_id.get_secret_value(),
                    "client_secret": self._settings.dai_client_secret.get_secret_value(),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            payload = response.json()
            if not isinstance(payload, dict):
                raise TypeError("DAI auth response must be an object")
            token = payload.get("access_token")
            if not isinstance(token, str) or not token.strip():
                raise ValueError("DAI auth response did not contain access_token")
            expires_value = payload.get("expires_in")
            if isinstance(expires_value, bool):
                raise TypeError("DAI auth response contained invalid expires_in")
            try:
                expires_in = float(expires_value)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    "DAI auth response contained invalid expires_in"
                ) from error
            if not math.isfinite(expires_in) or expires_in <= 0:
                raise ValueError("DAI auth response contained invalid expires_in")
            self._token = token
            self._token_expires_at = self._clock() + max(0.0, expires_in - 30.0)
            return token

    async def log_by_runid(self, runid: str) -> list[LogEntry]:
        """Fetch and parse the ordered production DAI log for a run."""
        runid = _validated_value(runid, "runid")
        url = _format_endpoint(
            self._settings.dai_log_by_runid_url,
            "runid",
            runid,
        )
        token = await self.authenticate()
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
        if not all(isinstance(item, dict) for item in items):
            raise TypeError("DAI run-log items[] must contain objects")
        return [LogEntry.model_validate(item) for item in items]

    async def fetch_screenshot(self, image_id: str, dest: Path) -> Path:
        """Fetch a production DAI screenshot and write its PNG bytes."""
        image_id = _validated_value(image_id, "image_id")
        if not dest.name or (dest.exists() and dest.is_dir()):
            raise ValueError("screenshot destination must include a filename")
        url = _format_endpoint(
            self._settings.dai_screenshot_url,
            "image_id",
            image_id,
        )
        token = await self.authenticate()
        response = await self._request(
            "GET",
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "image/png",
            },
        )
        if not response.content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("DAI screenshot response was not a PNG")

        dest.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=dest.parent,
                prefix=f".{dest.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(response.content)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, dest)
        except BaseException:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise
        return dest

    def walk_back_to_screenshot(
        self,
        logs: list[LogEntry],
        error_index: int,
    ) -> LogEntry | None:
        """Return the last captured frame before the failing log entry."""
        if error_index < 0 or error_index >= len(logs):
            raise IndexError("error_index is outside the log")
        for index in range(error_index - 1, -1, -1):
            if logs[index].image_id:
                return logs[index]
        return None

    def result_url(self, runid: str) -> str:
        """Return the known read-only DAI URL associated with this run."""
        runid = _validated_value(runid, "runid")
        return _format_endpoint(
            self._settings.dai_log_by_runid_url,
            "runid",
            runid,
        )
