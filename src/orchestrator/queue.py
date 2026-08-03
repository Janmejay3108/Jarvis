from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from src.models.run import AgentRun, RunMode, RunStatus
from src.orchestrator.events import EventBus
from src.orchestrator.pipeline import DiagnosisPipeline
from src.orchestrator.state_store import StateStore

_TERMINAL_STATUSES = {
    RunStatus.completed,
    RunStatus.failed,
    RunStatus.cancelled,
    RunStatus.low_confidence,
    RunStatus.exhausted,
}


class TrackQueue:
    def __init__(
        self,
        *,
        track_id: str,
        state_store: StateStore,
        event_bus: EventBus,
        pipeline: DiagnosisPipeline,
    ) -> None:
        canonical_track = track_id.strip().lower()
        if not canonical_track:
            raise ValueError("track_id must not be empty")
        self.track_id = canonical_track
        self._state_store = state_store
        self._event_bus = event_bus
        self._pipeline = pipeline
        self._queue: asyncio.Queue[AgentRun] = asyncio.Queue()
        self._admission_lock = asyncio.Lock()
        self._shutdown_lock = asyncio.Lock()
        self._active_by_ticket: dict[str, AgentRun] = {}
        self._active_by_run_id: dict[str, AgentRun] = {}
        self._cancellation_requested: set[str] = set()
        self._worker_task: asyncio.Task[None] | None = None
        self._current_run: AgentRun | None = None
        self._current_task: asyncio.Task[AgentRun] | None = None
        self._closed = False

    def _ensure_worker(self) -> None:
        if self._closed:
            raise RuntimeError("Queue has been shut down")
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(
                self._worker(),
                name=f"jarvis-queue-{self.track_id}",
            )

    async def start(self) -> None:
        async with self._admission_lock:
            self._ensure_worker()

    @staticmethod
    def _canonical_ticket(ticket: str) -> str:
        canonical = ticket.strip().upper()
        if not canonical:
            raise ValueError("ticket must not be empty")
        return canonical

    @staticmethod
    def _terminal_payload(run: AgentRun, reason: str) -> dict[str, Any]:
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

    async def _fail_admission(self, run: AgentRun) -> None:
        run.status = RunStatus.failed
        run.completed_at = datetime.now(UTC)
        await self._persist_terminal(run, "queue_admission_error")

    def _remove_active(self, run: AgentRun) -> None:
        if self._active_by_ticket.get(run.ticket_key) is run:
            del self._active_by_ticket[run.ticket_key]
        if self._active_by_run_id.get(run.run_id) is run:
            del self._active_by_run_id[run.run_id]
        self._cancellation_requested.discard(run.run_id)

    async def enqueue(
        self,
        ticket: str,
        mode: RunMode,
        conversation_id: str | None,
    ) -> str:
        canonical_ticket = self._canonical_ticket(ticket)
        async with self._admission_lock:
            self._ensure_worker()
            existing = self._active_by_ticket.get(canonical_ticket)
            if existing is not None:
                await self._event_bus.publish(
                    existing.run_id,
                    "agent.message",
                    {"text": f"{canonical_ticket} is already running."},
                    cost_usd_so_far=existing.cost_usd,
                )
                return existing.run_id

            run = await AgentRun.create(
                self._state_store,
                self._event_bus,
                ticket_key=canonical_ticket,
                mode=mode,
                track_id=self.track_id,
                conversation_id=conversation_id,
            )
            self._active_by_ticket[canonical_ticket] = run
            self._active_by_run_id[run.run_id] = run
            try:
                await self._event_bus.publish(
                    run.run_id,
                    "run.queued",
                    {
                        "ticket_key": run.ticket_key,
                        "track_id": run.track_id,
                        "mode": run.mode,
                        "conversation_id": run.conversation_id,
                    },
                    cost_usd_so_far=run.cost_usd,
                )
            except asyncio.CancelledError:
                try:
                    await self._fail_admission(run)
                finally:
                    self._remove_active(run)
                raise
            except Exception:
                try:
                    await self._fail_admission(run)
                finally:
                    self._remove_active(run)
                raise
            self._queue.put_nowait(run)
            return run.run_id

    async def _terminalize_cancelled(self, run: AgentRun) -> None:
        run.status = RunStatus.cancelled
        run.completed_at = datetime.now(UTC)
        payload = await self._persist_terminal(run, "cancelled")
        await self._event_bus.publish(
            run.run_id,
            "agent.message",
            {"text": "Run cancelled."},
            cost_usd_so_far=run.cost_usd,
        )
        await self._event_bus.publish(
            run.run_id,
            "run.failed",
            payload,
            cost_usd_so_far=run.cost_usd,
        )

    async def _terminalize_failure(self, run: AgentRun) -> None:
        run.status = RunStatus.failed
        run.completed_at = datetime.now(UTC)
        payload = await self._persist_terminal(run, "queue_worker_error")
        await self._event_bus.publish(
            run.run_id,
            "agent.message",
            {"text": "The run failed unexpectedly. Earlier artifacts were preserved."},
            cost_usd_so_far=run.cost_usd,
        )
        await self._event_bus.publish(
            run.run_id,
            "run.failed",
            payload,
            cost_usd_so_far=run.cost_usd,
        )

    async def _process(self, run: AgentRun) -> None:
        if run.run_id in self._cancellation_requested:
            await self._terminalize_cancelled(run)
            return

        self._current_run = run
        pipeline_task = asyncio.create_task(
            self._pipeline.execute(run),
            name=f"jarvis-run-{run.run_id}",
        )
        self._current_task = pipeline_task
        try:
            await pipeline_task
        except asyncio.CancelledError:
            requested = run.run_id in self._cancellation_requested
            await self._terminalize_cancelled(run)
            if not requested:
                raise
        except Exception:  # noqa: BLE001
            await self._terminalize_failure(run)
        finally:
            self._current_run = None
            self._current_task = None

    async def _worker(self) -> None:
        while True:
            run = await self._queue.get()
            try:
                await self._process(run)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                self._cancellation_requested.discard(run.run_id)
            finally:
                self._remove_active(run)
                self._queue.task_done()

    async def cancel(self, run_id: str) -> bool:
        async with self._admission_lock:
            run = self._active_by_run_id.get(run_id)
            if run is None or run.status in _TERMINAL_STATUSES:
                return False
            self._cancellation_requested.add(run_id)
            if self._current_run is run and self._current_task is not None:
                self._current_task.cancel()
            return True

    async def join(self) -> None:
        await self._queue.join()

    async def shutdown(self, *, drain: bool = True) -> None:
        async with self._shutdown_lock:
            async with self._admission_lock:
                if self._closed and self._worker_task is None:
                    return
                self._closed = True
                active_run_ids = list(self._active_by_run_id)

            if not drain:
                for run_id in active_run_ids:
                    await self.cancel(run_id)

            await self.join()
            worker_task = self._worker_task
            if worker_task is not None:
                worker_task.cancel()
                try:
                    await worker_task
                except asyncio.CancelledError:
                    pass
            self._worker_task = None
            self._current_run = None
            self._current_task = None
