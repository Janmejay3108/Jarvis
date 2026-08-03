from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self
from urllib.parse import quote

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
	from src.config import Settings


def _is_retryable(error: BaseException) -> bool:
	if isinstance(error, httpx.TimeoutException):
		return True
	return (
		isinstance(error, httpx.HTTPStatusError)
		and 500 <= error.response.status_code < 600
	)


def _encoded_path(path: str) -> str:
	return quote(path.strip("/"), safe="/")


class BitbucketClient:
	def __init__(
		self,
		config: Settings | None = None,
		client: httpx.AsyncClient | None = None,
	) -> None:
		if config is None:
			from src.config import settings

			config = settings
		repo = config.track.repo
		self._repo_url = (
			f"{config.bitbucket_base_url.rstrip('/')}"
			f"/rest/api/1.0/projects/{repo.project}/repos/{repo.slug}"
		)
		self._headers = {
			"Authorization": f"Bearer {config.bitbucket_pat.get_secret_value()}",
			"Accept": "application/json",
		}
		self._client = client or httpx.AsyncClient(timeout=60.0)
		self._owns_client = client is None

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
	async def _read_request(
		self,
		path: str,
		*,
		params: dict[str, str | int],
	) -> httpx.Response:
		response = await self._client.get(
			f"{self._repo_url}{path}",
			params=params,
			headers=self._headers,
		)
		response.raise_for_status()
		return response

	async def read_file(self, path: str, at: str) -> str:
		encoded_path = _encoded_path(path)
		if not encoded_path:
			raise ValueError("Bitbucket file path must not be empty")
		response = await self._read_request(
			f"/raw/{encoded_path}",
			params={"at": at},
		)
		return response.text

	async def list_files(self, path: str, at: str) -> list[str]:
		encoded_path = _encoded_path(path)
		endpoint = f"/files/{encoded_path}" if encoded_path else "/files"
		files: list[str] = []
		start = 0

		while True:
			response = await self._read_request(
				endpoint,
				params={"at": at, "start": start},
			)
			payload: Any = response.json()
			if not isinstance(payload, dict):
				raise TypeError("Bitbucket files response must be an object")

			values = payload.get("values")
			if not isinstance(values, list):
				raise TypeError("Bitbucket files response must contain values[]")
			if not all(isinstance(value, str) for value in values):
				raise TypeError("Bitbucket files response values[] must contain strings")

			is_last_page = payload.get("isLastPage")
			if not isinstance(is_last_page, bool):
				raise TypeError("Bitbucket files response isLastPage must be a boolean")
			files.extend(values)
			if is_last_page:
				return files

			next_start = payload.get("nextPageStart")
			if type(next_start) is not int or next_start <= start:
				raise TypeError(
					"Bitbucket files response nextPageStart must be an advancing integer"
				)
			start = next_start
