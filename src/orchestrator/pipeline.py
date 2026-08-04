from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import httpx
from pydantic import BaseModel, ConfigDict, Field

from src.integrations.dai_client import LogEntry
from src.integrations.jira_client import JiraWriteUncertain
from src.models.run import AgentRun, RunStatus
from src.orchestrator.events import EventBus
from src.orchestrator.jira_actions import (
	JiraActionState,
	append_jira_action_footer,
	jira_action_event_payload,
)
from src.orchestrator.state_store import StateStore
from src.utils.budget import BudgetExceeded
from src.utils.textguard import frame_evidence_text


class TicketMetadata(BaseModel):
	model_config = ConfigDict(extra="forbid")

	runid: str | None = None
	title: str = ""
	description: str = ""
	test_script_name: str = ""


class ErrorMatch(BaseModel):
	model_config = ConfigDict(extra="forbid")

	index: int = Field(ge=0)
	reasoning: str


class LocalizationResult(BaseModel):
	model_config = ConfigDict(extra="forbid")

	scripts: dict[str, str] = Field(default_factory=dict)
	call_chain: list[str] = Field(default_factory=list)
	blast_radius: dict[str, list[str]] = Field(default_factory=dict)


class DiagnosisOutcome(BaseModel):
	model_config = ConfigDict(extra="forbid")

	diagnosis: dict[str, Any]
	tokens_in: int = Field(default=0, ge=0)
	tokens_out: int = Field(default=0, ge=0)
	cost_usd: float = Field(default=0.0, ge=0)


@runtime_checkable
class JiraGateway(Protocol):
	async def get_ticket(self, key: str) -> dict[str, Any]: ...

	async def post_comment(self, key: str, body: str) -> dict[str, Any]: ...

	async def add_label(self, key: str, label: str) -> None: ...


@runtime_checkable
class EvidenceGateway(Protocol):
	async def log_by_runid(self, runid: str) -> list[LogEntry]: ...

	async def fetch_screenshot(self, image_id: str, dest: Path) -> Path: ...

	def walk_back_to_screenshot(
		self,
		logs: list[LogEntry],
		error_index: int,
	) -> LogEntry | None: ...


@runtime_checkable
class TicketExtractor(Protocol):
	async def extract(self, framed_ticket: str) -> TicketMetadata: ...


@runtime_checkable
class ErrorMatcher(Protocol):
	async def match(
		self,
		framed_logs: str,
		title: str,
		description: str,
	) -> ErrorMatch: ...


@runtime_checkable
class Localizer(Protocol):
	async def localize(
		self,
		run: AgentRun,
		metadata: TicketMetadata,
		matched_log: LogEntry,
	) -> LocalizationResult: ...


@runtime_checkable
class Diagnoser(Protocol):
	async def diagnose(self, run: AgentRun) -> DiagnosisOutcome: ...


DiagnosisFormatter = Callable[[dict[str, Any], str], str]


class MissingRunId(RuntimeError):
	pass


@dataclass
class _StageCompletion:
	detail: str | None = None


_TERMINAL_STATUSES = {
	RunStatus.completed,
	RunStatus.failed,
	RunStatus.cancelled,
	RunStatus.low_confidence,
	RunStatus.exhausted,
}


class DiagnosisPipeline:
	def __init__(
		self,
		*,
		state_store: StateStore,
		event_bus: EventBus,
		jira: JiraGateway,
		evidence: EvidenceGateway,
		ticket_extractor: TicketExtractor,
		error_matcher: ErrorMatcher,
		localizer: Localizer,
		diagnoser: Diagnoser,
		format_for_jira: DiagnosisFormatter,
		jira_writes_enabled: bool,
		artifact_root: Path = Path("data/agent_runs"),
	) -> None:
		self._state_store = state_store
		self._event_bus = event_bus
		self._jira = jira
		self._evidence = evidence
		self._ticket_extractor = ticket_extractor
		self._error_matcher = error_matcher
		self._localizer = localizer
		self._diagnoser = diagnoser
		self._format_for_jira = format_for_jira
		self._jira_writes_enabled = jira_writes_enabled
		self._artifact_root = artifact_root

	async def _message(self, run: AgentRun, text: str) -> None:
		await self._event_bus.publish(
			run.run_id,
			"agent.message",
			{"text": text},
			cost_usd_so_far=run.cost_usd,
		)

	async def _artifact(self, run: AgentRun, kind: str, data: Any) -> None:
		await self._event_bus.publish(
			run.run_id,
			"artifact",
			{"kind": kind, "data": data},
			cost_usd_so_far=run.cost_usd,
		)

	async def _jira_action_event(
		self,
		run: AgentRun,
		action: dict[str, Any],
	) -> None:
		await self._event_bus.publish(
			run.run_id,
			"jira.action.updated",
			jira_action_event_payload(action),
			cost_usd_so_far=run.cost_usd,
		)

	async def _create_jira_action(
		self,
		run: AgentRun,
		operation: str,
		intent: dict[str, Any],
	) -> dict[str, Any]:
		action = await self._state_store.create_jira_action(
			run.run_id,
			run.ticket_key,
			operation,
			intent,
		)
		await self._jira_action_event(run, action)
		return action

	async def _finish_jira_action(
		self,
		run: AgentRun,
		action_id: str,
		state: JiraActionState,
	) -> JiraActionState:
		action = await self._state_store.update_jira_action(
			action_id,
			state=state,
		)
		await self._jira_action_event(run, action)
		return state

	async def _attempt_jira_write(
		self,
		run: AgentRun,
		action_id: str,
		request: Callable[[], Awaitable[Any]],
	) -> JiraActionState:
		action = await self._state_store.begin_jira_action_attempt(action_id)
		await self._jira_action_event(run, action)
		try:
			await request()
		except asyncio.CancelledError:
			raise
		except JiraWriteUncertain:
			state: JiraActionState = "uncertain"
		except httpx.HTTPStatusError as error:
			state = (
				"failed"
				if 400 <= error.response.status_code < 500
				else "uncertain"
			)
		except httpx.RequestError:
			state = "uncertain"
		else:
			state = "succeeded"
		return await self._finish_jira_action(run, action_id, state)

	def _terminal_payload(self, run: AgentRun, reason: str) -> dict[str, Any]:
		return {
			"summary": {
				"ticket_key": run.ticket_key,
				"status": run.status.value,
				"reason": reason,
			},
			"totals": {
				"tokens_in": run.tokens_in,
				"tokens_out": run.tokens_out,
				"cost_usd": run.cost_usd,
			},
		}

	@asynccontextmanager
	async def _stage(
		self,
		run: AgentRun,
		name: str,
		status: RunStatus,
		detail: str,
	) -> AsyncIterator[_StageCompletion]:
		await run.begin(name, status, detail)
		completion = _StageCompletion()
		try:
			await self._message(run, detail)
			yield completion
		except asyncio.CancelledError:
			raise
		except Exception as error:
			if isinstance(error, MissingRunId):
				safe_code = "missing_runid"
			elif isinstance(error, BudgetExceeded):
				safe_code = "budget_exceeded"
			else:
				safe_code = type(error).__name__
			await run.end(error=safe_code)
			raise
		else:
			await run.end(detail=completion.detail)

	async def _persist_terminal(self, run: AgentRun, reason: str) -> dict[str, Any]:
		payload = self._terminal_payload(run, reason)
		await self._state_store.update_run(
			run.run_id,
			status=run.status.value,
			completed_at=(
				run.completed_at.isoformat() if run.completed_at is not None else None
			),
			tokens_in=run.tokens_in,
			tokens_out=run.tokens_out,
			cost_usd=run.cost_usd,
			summary_json=payload["summary"],
		)
		return payload

	async def _fail(self, run: AgentRun, reason: str, message: str) -> AgentRun:
		if run.status is not RunStatus.failed:
			run.status = RunStatus.failed
			run.completed_at = datetime.now(UTC)
		await self._message(run, message)
		payload = await self._persist_terminal(run, reason)
		await self._event_bus.publish(
			run.run_id,
			"run.failed",
			payload,
			cost_usd_so_far=run.cost_usd,
		)
		return run

	async def execute(
		self,
		run: AgentRun,
		*,
		runid_override: str | None = None,
	) -> AgentRun:
		if run.status in _TERMINAL_STATUSES:
			raise ValueError("A terminal run cannot be executed")

		try:
			metadata = await self._read_ticket(run, runid_override)
			matched_log = await self._fetch_logs(run, metadata)
			await self._localize(run, metadata, matched_log)
			await self._analyze(run)
			await self._post_diagnosis(run)
		except asyncio.CancelledError:
			raise
		except MissingRunId:
			return await self._fail(
				run,
				"missing_runid",
				"No DAI run ID was found. Re-run with runid=NNN.",
			)
		except BudgetExceeded:
			return await self._fail(
				run,
				"budget_exceeded",
				"Run stopped because its model budget was exhausted.",
			)
		except Exception:  # noqa: BLE001
			return await self._fail(
				run,
				"pipeline_error",
				"The diagnosis pipeline failed. Earlier artifacts were preserved.",
			)

		run.status = RunStatus.completed
		run.completed_at = datetime.now(UTC)
		payload = await self._persist_terminal(run, "diagnosed")
		await self._event_bus.publish(
			run.run_id,
			"run.completed",
			payload,
			cost_usd_so_far=run.cost_usd,
		)
		return run

	async def _read_ticket(
		self,
		run: AgentRun,
		runid_override: str | None,
	) -> TicketMetadata:
		detail = f"Reading Jira ticket {run.ticket_key}"
		async with self._stage(run, "read_ticket", RunStatus.reading_ticket, detail):
			ticket = await self._jira.get_ticket(run.ticket_key)
			run.ticket_data = ticket
			framed_ticket = frame_evidence_text(
				json.dumps(ticket, ensure_ascii=True, default=str),
				label="TICKET",
			)
			if runid_override is None:
				metadata = await self._ticket_extractor.extract(framed_ticket)
			else:
				fields = ticket.get("fields")
				fields = fields if isinstance(fields, dict) else {}
				title = fields.get("summary")
				description = fields.get("description")
				metadata = TicketMetadata(
					runid=runid_override,
					title=title if isinstance(title, str) else "",
					description=(
						description if isinstance(description, str) else ""
					),
				)

			metadata.runid = metadata.runid.strip() if metadata.runid else None
			run.ticket_data["jarvis_metadata"] = metadata.model_dump(mode="json")
			if not metadata.runid:
				raise MissingRunId
			return metadata

	async def _fetch_logs(
		self,
		run: AgentRun,
		metadata: TicketMetadata,
	) -> LogEntry:
		runid = metadata.runid
		if runid is None:
			raise MissingRunId
		detail = f"Fetching production DAI evidence for run {runid}"
		async with self._stage(run, "fetch_logs", RunStatus.fetching_logs, detail):
			logs = await self._evidence.log_by_runid(runid)
			if not logs:
				raise ValueError("Production DAI returned no log entries")
			run.logs = [entry.model_dump(mode="json") for entry in logs]
			matcher_view = [
				{
					"i": index,
					"message_type": entry.message_type,
					"severity": entry.severity,
					"message": entry.message,
				}
				for index, entry in enumerate(logs)
			]
			framed_logs = frame_evidence_text(
				json.dumps(matcher_view, ensure_ascii=True, default=str),
				label="DAI_LOG",
			)
			match = await self._error_matcher.match(
				framed_logs,
				metadata.title,
				metadata.description,
			)
			if match.index >= len(logs):
				raise IndexError("Error match index is outside the production DAI log")
			matched_log = logs[match.index]
			screenshot_log = self._evidence.walk_back_to_screenshot(logs, match.index)
			if screenshot_log is not None and screenshot_log.image_id:
				destination = self._artifact_root / run.run_id / "failure.png"
				screenshot = await self._evidence.fetch_screenshot(
					screenshot_log.image_id,
					destination,
				)
				run.screenshots.append(str(screenshot))
			return matched_log

	async def _localize(
		self,
		run: AgentRun,
		metadata: TicketMetadata,
		matched_log: LogEntry,
	) -> None:
		detail = "Localizing the failing SenseTalk path"
		async with self._stage(run, "localize", RunStatus.localizing, detail):
			localized = await self._localizer.localize(run, metadata, matched_log)
			run.scripts = localized.scripts
			run.call_chain = localized.call_chain
			run.blast_radius = localized.blast_radius

	async def _analyze(self, run: AgentRun) -> None:
		detail = "Analyzing the failure evidence"
		async with self._stage(run, "analyze", RunStatus.analyzing, detail):
			outcome = await self._diagnoser.diagnose(run)
			run.diagnosis = outcome.diagnosis
			run.tokens_in += outcome.tokens_in
			run.tokens_out += outcome.tokens_out
			run.cost_usd += outcome.cost_usd
			await self._state_store.update_run(
				run.run_id,
				tokens_in=run.tokens_in,
				tokens_out=run.tokens_out,
				cost_usd=run.cost_usd,
			)
		await self._artifact(run, "diagnosis", run.diagnosis)

	async def _post_diagnosis(self, run: AgentRun) -> None:
		detail = "Publishing the diagnosis result"
		async with self._stage(
			run,
			"post_diagnosis",
			RunStatus.updating_jira,
			detail,
		) as completion:
			if self._jira_writes_enabled:
				comment = await self._create_jira_action(
					run,
					"post_comment",
					{
						"kind": "diagnosis_comment",
						"source": "diagnosis_artifact",
					},
				)
				try:
					diagnosis = (
						run.diagnosis
						if run.diagnosis is not None
						else {}
					)
					body = self._format_for_jira(
						diagnosis,
						run.ticket_key,
					)
					body = append_jira_action_footer(
						body,
						str(comment["action_id"]),
					)
				except Exception:  # noqa: BLE001
					comment_state = await self._finish_jira_action(
						run,
						str(comment["action_id"]),
						"failed",
					)
				else:
					comment_state = await self._attempt_jira_write(
						run,
						str(comment["action_id"]),
						lambda: self._jira.post_comment(
							run.ticket_key,
							body,
						),
					)

				label = await self._create_jira_action(
					run,
					"add_label",
					{"label": "ai-diagnosed"},
				)
				label_state = await self._attempt_jira_write(
					run,
					str(label["action_id"]),
					lambda: self._jira.add_label(
						run.ticket_key,
						"ai-diagnosed",
					),
				)
				if (
					comment_state == "succeeded"
					and label_state == "succeeded"
				):
					completion.detail = (
						"Jira publication succeeded (2/2 actions)"
					)
				else:
					completion.detail = (
						"Diagnosis completed; Jira publication needs "
						"attention: "
						f"post_comment={comment_state}, "
						f"add_label={label_state}"
					)
			else:
				completion.detail = "Jira writes disabled"
