from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from src.orchestrator.events import EventBus
from src.orchestrator.state_store import StateStore


class RunStatus(str, Enum):
	queued = "queued"
	reading_ticket = "reading_ticket"
	localizing = "localizing"
	fetching_logs = "fetching_logs"
	analyzing = "analyzing"
	generating_fix = "generating_fix"
	applying_fix = "applying_fix"
	linting = "linting"
	validating_local = "validating_local"
	validating_dai = "validating_dai"
	awaiting_approval = "awaiting_approval"
	publishing = "publishing"
	updating_jira = "updating_jira"
	completed = "completed"
	failed = "failed"
	cancelled = "cancelled"
	low_confidence = "low_confidence"
	exhausted = "exhausted"


RunMode = Literal["diagnose", "autofix"]
StepStatus = Literal["started", "completed", "failed"]


def _utc_now() -> datetime:
	return datetime.now(UTC)


def _run_id() -> str:
	return _utc_now().strftime("run-%Y%m%d-%H%M%S-%f")


class RunStep(BaseModel):
	model_config = ConfigDict(extra="forbid")

	name: str
	status: StepStatus = "started"
	started_at: datetime
	completed_at: datetime | None = None
	detail: str = ""
	error: str = ""


class AgentRun(BaseModel):
	model_config = ConfigDict(extra="forbid")

	run_id: str = Field(default_factory=_run_id)
	ticket_key: str
	track_id: str = "enovia"
	mode: RunMode
	conversation_id: str | None = None
	status: RunStatus = RunStatus.queued
	steps: list[RunStep] = Field(default_factory=list)
	ticket_data: dict[str, Any] | None = None
	scripts: dict[str, str] = Field(default_factory=dict)
	call_chain: list[str] | None = None
	blast_radius: dict[str, list[str]] = Field(default_factory=dict)
	logs: list[dict[str, Any]] | None = None
	screenshots: list[str] = Field(default_factory=list)
	diagnosis: dict[str, Any] | None = None
	fix: dict[str, Any] | None = None
	validation: dict[str, Any] | None = None
	tokens_in: int = Field(default=0, ge=0)
	tokens_out: int = Field(default=0, ge=0)
	cost_usd: float = Field(default=0.0, ge=0)
	created_at: datetime = Field(default_factory=_utc_now)
	completed_at: datetime | None = None

	_state_store: StateStore | None = PrivateAttr(default=None)
	_event_bus: EventBus | None = PrivateAttr(default=None)
	_active_step: RunStep | None = PrivateAttr(default=None)
	_active_step_id: str | None = PrivateAttr(default=None)

	@classmethod
	async def create(
		cls,
		state_store: StateStore,
		event_bus: EventBus,
		*,
		ticket_key: str,
		mode: RunMode,
		track_id: str = "enovia",
		conversation_id: str | None = None,
	) -> Self:
		run = cls(
			ticket_key=ticket_key,
			mode=mode,
			track_id=track_id,
			conversation_id=conversation_id,
		)
		await state_store.create_run(
			run.ticket_key,
			run.track_id,
			run.mode,
			run.conversation_id,
			run_id=run.run_id,
			status=run.status.value,
			created_at=run.created_at.isoformat(),
		)
		run._state_store = state_store
		run._event_bus = event_bus
		return run

	def _runtime(self) -> tuple[StateStore, EventBus]:
		if self._state_store is None or self._event_bus is None:
			raise RuntimeError(
				"Lifecycle helpers require an AgentRun created with AgentRun.create()"
			)
		return self._state_store, self._event_bus

	async def begin(
		self,
		name: str,
		status: RunStatus,
		detail: str = "",
	) -> RunStep:
		state_store, event_bus = self._runtime()
		if self._active_step is not None:
			raise RuntimeError(f"Step {self._active_step.name!r} is already active")

		started_at = _utc_now()
		step = RunStep(name=name, started_at=started_at, detail=detail)
		self.status = status
		self.steps.append(step)
		await state_store.update_run(self.run_id, status=status.value)
		step_id = await state_store.append_step(
			self.run_id,
			step.name,
			status=step.status,
			detail=step.detail,
			started_at=started_at.isoformat(),
		)
		self._active_step = step
		self._active_step_id = step_id
		await event_bus.publish(
			self.run_id,
			"step.started",
			step.model_dump(mode="json"),
			cost_usd_so_far=self.cost_usd,
		)
		return step

	async def end(self, detail: str | None = None, error: str = "") -> RunStep:
		state_store, event_bus = self._runtime()
		if self._active_step is None or self._active_step_id is None:
			raise RuntimeError("No active step to end")

		step = self._active_step
		completed_at = _utc_now()
		step.completed_at = completed_at
		if detail is not None:
			step.detail = detail
		step.error = error
		if error:
			step.status = "failed"
			self.status = RunStatus.failed
			self.completed_at = completed_at
			await state_store.update_run(
				self.run_id,
				status=self.status.value,
				completed_at=completed_at.isoformat(),
			)
			event_type = "step.failed"
		else:
			step.status = "completed"
			event_type = "step.completed"

		await state_store.complete_step(
			self._active_step_id,
			status=step.status,
			error=step.error,
			completed_at=completed_at.isoformat(),
			detail=detail,
		)
		await event_bus.publish(
			self.run_id,
			event_type,
			step.model_dump(mode="json"),
			cost_usd_so_far=self.cost_usd,
		)
		self._active_step = None
		self._active_step_id = None
		return step
