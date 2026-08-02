from __future__ import annotations

import argparse
import asyncio
import re
import subprocess
import sys
import tempfile
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self
from urllib.parse import quote, urlsplit, urlunsplit

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(override=True)

from src.config import settings
from src.integrations.dai_client import DaiClient
from src.integrations.jira_client import JiraClient
from src.orchestrator.state_store import StateStore
from src.static.handler_map import HandlerMap
from src.static.lint import lint
from src.static.sensetalk_parser import handler_defs
from src.static.vocabulary import HandlerEntry, Vocabulary

DEFAULT_TICKET = "TESTAUTOMA-8055"
PROVEN_RUN_ID = "30832"
PROVEN_ERROR_INDEX = 384
VALIDATION_SUITE = "EngineeringCentral"
TERMINAL_STATUSES = {
	"CANCELLED",
	"COMPLETED",
	"ERROR",
	"FAILED",
	"PASSED",
	"PASS",
	"SUCCESS",
}
SUCCESS_STATUSES = {"COMPLETED", "PASSED", "PASS", "SUCCESS"}


@dataclass(frozen=True)
class CheckResult:
	number: int
	name: str
	passed: bool
	skipped: bool = False


def _require(condition: object, message: str) -> None:
	if not condition:
		raise AssertionError(message)


def _run_check(
	number: int,
	name: str,
	check: Callable[[], None],
) -> CheckResult:
	print(f"\n--- {number}. {name} ---")
	try:
		check()
	except Exception as error:  # noqa: BLE001 - each smoke check must remain isolated
		print(f"FAILED: {type(error).__name__}: {error}")
		return CheckResult(number, name, passed=False)
	print("PASSED")
	return CheckResult(number, name, passed=True)


def _run_async_check(
	number: int,
	name: str,
	check: Callable[[], Awaitable[None]],
) -> CheckResult:
	return _run_check(number, name, lambda: asyncio.run(check()))


def check_repo_and_deps() -> None:
	print(f"Python: {sys.version.split()[0]}")
	print(f"Model: {settings.model}")
	print(f"Validation mechanism: {settings.validation_mechanism}")


async def check_jira_read(ticket_key: str) -> None:
	async with JiraClient() as client:
		ticket = await client.get_ticket(ticket_key)
	_require(ticket.get("key"), "Jira response has no key field")
	fields = ticket.get("fields")
	summary = fields.get("summary") if isinstance(fields, dict) else None
	print(f"Ticket: {ticket['key']} — {summary or '(no summary)'}")


async def check_bitbucket_read() -> None:
	repo = settings.track.repo
	path = (
		f"/rest/api/1.0/projects/{repo.project}/repos/{repo.slug}"
		"/raw/Enovia/Common.suite/Scripts/common.script"
	)
	url = f"{settings.bitbucket_base_url.rstrip('/')}{path}"
	headers = {
		"Authorization": f"Bearer {settings.bitbucket_pat.get_secret_value()}"
	}
	async with httpx.AsyncClient(timeout=60.0) as client:
		response = await client.get(url, params={"at": repo.branch}, headers=headers)
	response.raise_for_status()
	_require(response.content, "Bitbucket returned an empty file")
	print(f"Read {len(response.content)} bytes from {repo.slug}@{repo.branch}")


async def check_production_dai_evidence() -> None:
	async with DaiClient() as client:
		await client.authenticate()
		logs = await client.log_by_runid(PROVEN_RUN_ID)
		_require(len(logs) >= 100, f"Expected at least 100 logs, got {len(logs)}")
		screenshot = client.walk_back_to_screenshot(logs, PROVEN_ERROR_INDEX)
	_require(screenshot is not None, "No screenshot entry found before the error")
	_require(screenshot.image_id, "Screenshot entry has no image_id")
	print(f"Logs: {len(logs)}; prior image_id: {screenshot.image_id}")


async def check_claude_ping() -> None:
	url = f"{settings.anthropic_base_url.rstrip('/')}/v1/messages"
	headers = {
		"anthropic-version": "2023-06-01",
		"content-type": "application/json",
		"x-api-key": settings.anthropic_api_key.get_secret_value(),
	}
	body = {
		"model": settings.model,
		"max_tokens": 10,
		"messages": [{"role": "user", "content": "Reply OK"}],
	}
	async with httpx.AsyncClient(timeout=60.0) as client:
		response = await client.post(url, headers=headers, json=body)
	response.raise_for_status()
	_require(response.content, "Anthropic returned an empty response")
	print(f"Model confirmed: {settings.model}")


def check_test_config_registry() -> None:
	registry = settings.test_config_registry
	for suite_name in ("PartMaster", "EngineeringCentral"):
		_require(suite_name in registry, f"Registry is missing {suite_name}")
	print(f"Suites: {len(registry)}")
	print(f"PartMaster: {registry['PartMaster'].test_config_id}")
	print(f"EngineeringCentral: {registry['EngineeringCentral'].test_config_id}")


def check_static_modules() -> None:
	definitions = handler_defs("to handle Foo bar\nend Foo\n")
	_require(len(definitions) == 1, "SenseTalk parser did not find one handler")

	handler_map = HandlerMap({"Foo": "test.script"})
	_require(handler_map.resolve("Foo") == "test.script", "HandlerMap lookup failed")

	vocabulary = Vocabulary(
		[
			HandlerEntry(
				name="Foo",
				file="test.script",
				line=1,
				signature="to handle Foo",
				params=[],
				purpose="integration smoke",
			)
		]
	)
	_require(vocabulary.exists("Foo"), "Vocabulary lookup failed")

	issues = lint("if true\nend repeat\n")
	_require(issues, "SenseTalk lint did not flag mismatched blocks")
	print(f"Parser/map/vocabulary OK; lint produced {len(issues)} issue(s)")


async def check_state_store() -> None:
	with tempfile.TemporaryDirectory(prefix="jarvis-state-smoke-") as temp_dir:
		db_path = Path(temp_dir) / "agent.db"
		store = StateStore(str(db_path))
		await store.initialize()
		conversation_id = await store.create_conversation("Integration smoke")
		await store.save_message(conversation_id, "user", "Smoke test")
		run_id = await store.create_run(
			DEFAULT_TICKET,
			"enovia",
			"diagnose",
			conversation_id,
		)
		event_id = await store.append_event(run_id, "run.queued", {"smoke": True})
		events = await store.list_events(run_id)

		_require(len(events) == 1, f"Expected one event, got {len(events)}")
		_require(events[0]["event_id"] == event_id, "Persisted event ID differs")
		_require(events[0]["payload"] == {"smoke": True}, "Event payload differs")
		print(f"Conversation {conversation_id}; run {run_id}; event {event_id}")


def check_validation_mechanism() -> None:
	_require(
		settings.validation_mechanism == "jarvis-dai",
		f"Unexpected mechanism: {settings.validation_mechanism}",
	)
	print(f"Validation mechanism: {settings.validation_mechanism}")


def _records(payload: object) -> list[dict[str, Any]]:
	if isinstance(payload, list):
		return [item for item in payload if isinstance(item, dict)]
	if not isinstance(payload, dict):
		return []
	for key in (
		"items",
		"results",
		"data",
		"test_config_results",
		"testConfigResults",
		"test_results",
		"testResults",
		"logs",
	):
		value = payload.get(key)
		if isinstance(value, list):
			return [item for item in value if isinstance(item, dict)]
		if isinstance(value, dict):
			nested = _records(value)
			return nested or [value]
	return [payload]


def _find_value(payload: object, keys: tuple[str, ...]) -> object | None:
	if isinstance(payload, dict):
		for key in keys:
			value = payload.get(key)
			if value not in (None, ""):
				return value
		for value in payload.values():
			found = _find_value(value, keys)
			if found is not None:
				return found
	elif isinstance(payload, list):
		for item in payload:
			found = _find_value(item, keys)
			if found is not None:
				return found
	return None


def _identifier(payload: object) -> str | None:
	value = _find_value(
		payload,
		(
			"test_config_result_id",
			"testConfigResultId",
			"test_result_id",
			"testResultId",
			"execution_id",
			"executionId",
			"run_id",
			"runId",
			"id",
		),
	)
	return str(value) if value not in (None, "") else None


def _status(record: dict[str, Any]) -> str | None:
	value = _find_value(record, ("status", "result_status", "resultStatus"))
	return str(value).upper() if value not in (None, "") else None


class _JarvisDaiSmokeClient:
	def __init__(self) -> None:
		self._client = httpx.AsyncClient(
			base_url=settings.jarvis_dai_base_url.rstrip("/"),
			verify=False,
			timeout=120.0,
		)
		self._token: str | None = None
		self._token_expires_at = 0.0

	async def __aenter__(self) -> Self:
		return self

	async def __aexit__(self, *_args: object) -> None:
		await self._client.aclose()

	async def authenticate(self) -> str:
		if self._token and time.monotonic() < self._token_expires_at:
			return self._token
		response = await self._client.post(
			"/api/v2/auth",
			json={
				"client_id": settings.jarvis_dai_client_id.get_secret_value(),
				"client_secret": settings.jarvis_dai_client_secret.get_secret_value(),
			},
		)
		response.raise_for_status()
		payload = response.json()
		token = payload.get("access_token")
		_require(isinstance(token, str) and token, "JARVIS auth returned no token")
		expires_in = float(payload.get("expires_in", 570))
		self._token = token
		self._token_expires_at = time.monotonic() + max(30.0, expires_in - 30.0)
		return token

	async def request(
		self,
		method: str,
		path: str,
		**kwargs: Any,
	) -> httpx.Response:
		token = await self.authenticate()
		headers = dict(kwargs.pop("headers", {}))
		headers["Authorization"] = f"Bearer {token}"
		response = await self._client.request(method, path, headers=headers, **kwargs)
		if response.status_code == httpx.codes.UNAUTHORIZED:
			self._token = None
			headers["Authorization"] = f"Bearer {await self.authenticate()}"
			response = await self._client.request(
				method,
				path,
				headers=headers,
				**kwargs,
			)
		response.raise_for_status()
		return response

	async def trigger(self, test_config_id: str) -> str:
		response = await self.request(
			"POST",
			f"/task_scheduler_service/api/v1/task_instances/{test_config_id}",
		)
		trigger_id = _identifier(response.json())
		_require(trigger_id, "Trigger response contained no run or execution ID")
		return trigger_id

	async def test_config_results(
		self,
		test_config_id: str,
	) -> list[dict[str, Any]]:
		response = await self.request(
			"GET",
			"/api/v2/test_config_results",
			params={"test_config_id": test_config_id},
		)
		return _records(response.json())

	async def test_results(
		self,
		test_config_result_id: str,
	) -> list[dict[str, Any]]:
		response = await self.request(
			"GET",
			"/api/v2/test_results",
			params={"test_config_result_id": test_config_result_id},
		)
		return _records(response.json())

	async def logs(self, test_result_id: str) -> list[dict[str, Any]]:
		response = await self.request(
			"GET",
			f"/api/v2/test_results/{test_result_id}/logs",
		)
		return _records(response.json())


def _authenticated_git_url() -> str:
	parsed = urlsplit(settings.jarvis_repo_url)
	_require(parsed.scheme in {"http", "https"}, "JARVIS repo URL must use HTTP(S)")
	_require(parsed.hostname, "JARVIS repo URL has no hostname")
	host = parsed.hostname
	if parsed.port is not None:
		host = f"{host}:{parsed.port}"
	token = quote(settings.jarvis_pat.get_secret_value(), safe="")
	return urlunsplit(
		(parsed.scheme, f"{token}@{host}", parsed.path, "", "")
	)


def _run_git(
	args: list[str],
	*,
	cwd: Path | None = None,
	secret_url: str | None = None,
) -> str:
	result = subprocess.run(
		["git", *args],
		cwd=cwd,
		capture_output=True,
		text=True,
		check=False,
	)
	if result.returncode != 0:
		detail = (result.stderr or result.stdout).strip()
		if secret_url:
			detail = detail.replace(secret_url, "<authenticated-repo-url>")
		raise RuntimeError(f"git {args[0]} failed: {detail}")
	return result.stdout.strip()


def _mark_timeline(
	timeline: list[tuple[str, float]],
	label: str,
	started_at: float,
) -> None:
	timeline.append((label, time.monotonic() - started_at))


def _print_timeline(timeline: list[tuple[str, float]]) -> None:
	print("Validation timeline:")
	previous = 0.0
	for label, elapsed in timeline:
		print(f"  {label:<12} +{elapsed - previous:7.1f}s ({elapsed:7.1f}s total)")
		previous = elapsed


async def _poll_until_complete(
	client: _JarvisDaiSmokeClient,
	test_config_id: str,
	baseline_ids: set[str],
) -> tuple[str, list[dict[str, Any]], list[str]]:
	backoff = settings.track.jarvis.poll_backoff
	_require(backoff, "JARVIS poll_backoff is empty")
	deadline = time.monotonic() + settings.track.jarvis.run_timeout
	attempt = 0

	while True:
		config_results = await client.test_config_results(test_config_id)
		selected_id = next(
			(
				result_id
				for result in config_results
				if (result_id := _identifier(result))
				and result_id not in baseline_ids
			),
			None,
		)
		if selected_id is not None:
			test_results = await client.test_results(selected_id)
			statuses = [status for result in test_results if (status := _status(result))]
			if statuses and all(status in TERMINAL_STATUSES for status in statuses):
				return selected_id, test_results, statuses

		remaining = deadline - time.monotonic()
		if remaining <= 0:
			raise TimeoutError("JARVIS validation exceeded configured run_timeout")
		delay = backoff[min(attempt, len(backoff) - 1)]
		print(f"Polling JARVIS DAI again in {delay}s")
		await asyncio.sleep(min(delay, remaining))
		attempt += 1


async def _find_executed_sha(
	client: _JarvisDaiSmokeClient,
	test_results: list[dict[str, Any]],
) -> str:
	pattern = re.compile(
		r"Using Git commit SHA:\s*['\"]?([0-9a-f]{40})",
		re.IGNORECASE,
	)
	for result in test_results:
		test_result_id = _identifier(result)
		if test_result_id is None:
			continue
		for log_entry in await client.logs(test_result_id):
			message = log_entry.get("message")
			if isinstance(message, str) and (match := pattern.search(message)):
				return match.group(1)
	raise AssertionError("Run logs contain no 'Using Git commit SHA' entry")


async def check_jarvis_validation() -> None:
	timeline: list[tuple[str, float]] = []
	started_at = time.monotonic()
	registry_entry = settings.test_config_registry[VALIDATION_SUITE]
	authenticated_url = _authenticated_git_url()

	try:
		async with _JarvisDaiSmokeClient() as client:
			await client.authenticate()
			baseline_results = await client.test_config_results(
				registry_entry.test_config_id
			)
			baseline_ids = {
				result_id
				for result in baseline_results
				if (result_id := _identifier(result))
			}

			with tempfile.TemporaryDirectory(prefix="jarvis-validation-smoke-") as temp:
				clone_path = Path(temp) / "validation-repo"
				_run_git(
					[
						"clone",
						"--depth",
						"1",
						"--branch",
						settings.jarvis_branch,
						authenticated_url,
						str(clone_path),
					],
					secret_url=authenticated_url,
				)
				_run_git(
					[
						"-c",
						"user.name=JARVIS",
						"-c",
						"user.email=jarvis@localhost",
						"commit",
						"--allow-empty",
						"-m",
						"smoke: integration test",
					],
					cwd=clone_path,
				)
				pushed_sha = _run_git(["rev-parse", "HEAD"], cwd=clone_path)
				branch_ref = f"refs/heads/{settings.jarvis_branch}"
				_run_git(
					[
						"push",
						"--force",
						authenticated_url,
						f"HEAD:{branch_ref}",
					],
					cwd=clone_path,
					secret_url=authenticated_url,
				)
				_mark_timeline(timeline, "push", started_at)

				remote_line = _run_git(
					["ls-remote", authenticated_url, branch_ref],
					secret_url=authenticated_url,
				)
				remote_sha = remote_line.split(maxsplit=1)[0] if remote_line else ""
				_require(remote_sha == pushed_sha, "Remote SHA differs from pushed SHA")
				_mark_timeline(timeline, "SHA-assert", started_at)

				trigger_id = await client.trigger(registry_entry.test_config_id)
				print(f"Triggered execution: {trigger_id}")
				_mark_timeline(timeline, "trigger", started_at)

				result_id, test_results, statuses = await _poll_until_complete(
					client,
					registry_entry.test_config_id,
					baseline_ids,
				)
				print(f"Completed result {result_id}: {', '.join(statuses)}")
				_require(
					all(status in SUCCESS_STATUSES for status in statuses),
					f"Golden-path validation did not pass: {statuses}",
				)
				_mark_timeline(timeline, "complete", started_at)

				executed_sha = await _find_executed_sha(client, test_results)
				_require(
					executed_sha.lower() == pushed_sha.lower(),
					f"Executed SHA {executed_sha} differs from pushed SHA {pushed_sha}",
				)
				_mark_timeline(timeline, "SHA-verify", started_at)
				print(f"Executed commit verified: {executed_sha}")
	finally:
		_print_timeline(timeline)


def _print_summary(results: list[CheckResult]) -> None:
	print("\n============ GATE 0b-LOCAL Integration Smoke ============")
	for result in results:
		if result.skipped:
			symbol = "-"
			suffix = " (skipped)"
		else:
			symbol = "✓" if result.passed else "✗"
			suffix = ""
		print(f" {symbol} {result.number:>2}. {result.name}{suffix}")
	print("=========================================================")

	passed = sum(result.passed and not result.skipped for result in results)
	skipped = sum(result.skipped for result in results)
	if any(not result.passed and not result.skipped for result in results):
		print(
			f"Result: {passed}/10 passed — GATE 0b-LOCAL NOT SATISFIED"
		)
	elif skipped:
		print(
			f"Result: {passed}/{passed} executed passed; {skipped} skipped — "
			"GATE 0b-LOCAL NOT EVALUATED"
		)
	else:
		print("Result: 10/10 passed — GATE 0b-LOCAL SATISFIED")


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Run GATE 0b-LOCAL integration checks")
	parser.add_argument(
		"--skip-validation",
		action="store_true",
		help="skip the long-running JARVIS validation dry-run",
	)
	parser.add_argument("--ticket", default=DEFAULT_TICKET, help="Jira test ticket key")
	return parser.parse_args()


def main() -> int:
	args = parse_args()
	results = [
		_run_check(1, "Repo + deps", check_repo_and_deps),
		_run_async_check(2, "Jira read", lambda: check_jira_read(args.ticket)),
		_run_async_check(3, "Bitbucket read", check_bitbucket_read),
		_run_async_check(
			4,
			"Production DAI evidence",
			check_production_dai_evidence,
		),
		_run_async_check(5, "Claude ping", check_claude_ping),
		_run_check(6, "Test config registry", check_test_config_registry),
		_run_check(7, "Static modules", check_static_modules),
		_run_async_check(8, "SQLite state store", check_state_store),
		_run_check(9, "Validation mechanism", check_validation_mechanism),
	]

	if args.skip_validation:
		results.append(
			CheckResult(
				10,
				"JARVIS validation dry-run",
				passed=True,
				skipped=True,
			)
		)
	else:
		results.append(
			_run_async_check(
				10,
				"JARVIS validation dry-run",
				check_jarvis_validation,
			)
		)

	_print_summary(results)
	return int(any(not result.passed for result in results))


if __name__ == "__main__":
	raise SystemExit(main())
