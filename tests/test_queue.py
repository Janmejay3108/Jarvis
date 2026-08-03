from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from src.models.run import AgentRun, RunStatus
from src.orchestrator.events import EventBus
from src.orchestrator.queue import TrackQueue
from src.orchestrator.state_store import StateStore


class ControlledPipeline:
    def __init__(self, store: StateStore, event_bus: EventBus) -> None:
        self.store = store
        self.event_bus = event_bus
        self.gates: dict[str, asyncio.Event] = {}
        self.started_events: dict[str, asyncio.Event] = {}
        self.failures: dict[str, Exception] = {}
        self.started: list[str] = []
        self.completed: list[str] = []
        self.runs: list[AgentRun] = []
        self.active = 0
        self.maximum_active = 0

    def gate(self, ticket: str) -> asyncio.Event:
        gate = asyncio.Event()
        self.gates[ticket] = gate
        return gate

    def started_event(self, ticket: str) -> asyncio.Event:
        return self.started_events.setdefault(ticket, asyncio.Event())

    @staticmethod
    def _payload(run: AgentRun) -> dict[str, Any]:
        return {
            "summary": {
                "ticket_key": run.ticket_key,
                "status": "completed",
                "reason": "diagnosed",
            },
            "totals": {"tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0},
        }

    async def execute(
        self,
        run: AgentRun,
        *,
        runid_override: str | None = None,
    ) -> AgentRun:
        assert runid_override is None
        self.runs.append(run)
        self.started.append(run.ticket_key)
        self.active += 1
        self.maximum_active = max(self.maximum_active, self.active)
        self.started_event(run.ticket_key).set()
        try:
            gate = self.gates.get(run.ticket_key)
            if gate is not None:
                await gate.wait()
            failure = self.failures.get(run.ticket_key)
            if failure is not None:
                raise failure
            run.status = RunStatus.completed
            run.completed_at = datetime.now(UTC)
            payload = self._payload(run)
            await self.store.update_run(
                run.run_id,
                status=run.status.value,
                completed_at=run.completed_at.isoformat(),
                summary_json=payload["summary"],
            )
            await self.event_bus.publish(run.run_id, "run.completed", payload)
            self.completed.append(run.ticket_key)
            return run
        finally:
            self.active -= 1


async def _harness(tmp_path: Path) -> tuple[StateStore, EventBus, ControlledPipeline]:
    store = StateStore(str(tmp_path / "agent.db"))
    await store.initialize()
    event_bus = EventBus(store)
    return store, event_bus, ControlledPipeline(store, event_bus)


async def _all_runs(store: StateStore) -> list[dict[str, Any]]:
    import aiosqlite

    async with aiosqlite.connect(store.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM runs ORDER BY rowid")
        return [dict(row) for row in await cursor.fetchall()]


@pytest.mark.asyncio
async def test_enqueue_creates_queued_run_and_master_event(tmp_path: Path) -> None:
    store, event_bus, pipeline = await _harness(tmp_path)
    gate = pipeline.gate("TESTAUTOMA-1001")
    queue = TrackQueue(
        track_id="enovia",
        state_store=store,
        event_bus=event_bus,
        pipeline=pipeline,  # type: ignore[arg-type]
    )
    try:
        run_id = await queue.enqueue(" testautoma-1001 ", "diagnose", "conversation-1")
        row = await store.get_run(run_id)
        assert row is not None
        assert {
            "ticket_key": row["ticket_key"],
            "track_id": row["track_id"],
            "mode": row["mode"],
            "conversation_id": row["conversation_id"],
            "status": row["status"],
        } == {
            "ticket_key": "TESTAUTOMA-1001",
            "track_id": "enovia",
            "mode": "diagnose",
            "conversation_id": "conversation-1",
            "status": "queued",
        }
        events = await store.list_events(run_id)
        assert len(events) == 1
        assert events[0]["type"] == "run.queued"
        assert events[0]["payload"] == {
            "ticket_key": "TESTAUTOMA-1001",
            "track_id": "enovia",
            "mode": "diagnose",
            "conversation_id": "conversation-1",
        }
        assert events[0]["cost_usd_so_far"] == 0.0
        await pipeline.started_event("TESTAUTOMA-1001").wait()
        assert pipeline.runs[0].run_id == run_id
        assert pipeline.runs[0]._state_store is store
        assert pipeline.runs[0]._event_bus is event_bus
        gate.set()
        await queue.join()
    finally:
        gate.set()
        await queue.shutdown()


@pytest.mark.asyncio
async def test_single_worker_executes_fifo(tmp_path: Path) -> None:
    store, event_bus, pipeline = await _harness(tmp_path)
    tickets = ["TESTAUTOMA-1001", "TESTAUTOMA-1002", "TESTAUTOMA-1003"]
    gates = {ticket: pipeline.gate(ticket) for ticket in tickets}
    queue = TrackQueue(
        track_id="enovia",
        state_store=store,
        event_bus=event_bus,
        pipeline=pipeline,  # type: ignore[arg-type]
    )
    try:
        for ticket in tickets:
            await queue.enqueue(ticket, "diagnose", None)
        for index, ticket in enumerate(tickets):
            await pipeline.started_event(ticket).wait()
            assert pipeline.started == tickets[: index + 1]
            gates[ticket].set()
        await queue.join()
        assert pipeline.completed == tickets
        assert pipeline.maximum_active == 1
    finally:
        for gate in gates.values():
            gate.set()
        await queue.shutdown()


@pytest.mark.asyncio
async def test_concurrent_active_ticket_deduplication_is_atomic(tmp_path: Path) -> None:
    store, event_bus, pipeline = await _harness(tmp_path)
    gate = pipeline.gate("TESTAUTOMA-1001")
    queue = TrackQueue(
        track_id="enovia",
        state_store=store,
        event_bus=event_bus,
        pipeline=pipeline,  # type: ignore[arg-type]
    )
    try:
        requests = [
            ("TESTAUTOMA-1001", "diagnose", "first"),
            (" testautoma-1001", "autofix", "second"),
            ("TESTAUTOMA-1001 ", "diagnose", "third"),
            ("testautoma-1001", "autofix", None),
        ]
        tasks = [
            asyncio.create_task(queue.enqueue(ticket, mode, conversation))
            for ticket, mode, conversation in requests
        ]
        run_ids = await asyncio.gather(*tasks)
        assert len(set(run_ids)) == 1
        rows = await _all_runs(store)
        assert len(rows) == 1
        assert rows[0]["mode"] == "diagnose"
        assert rows[0]["conversation_id"] == "first"
        events = await store.list_events(run_ids[0])
        assert [event["type"] for event in events].count("run.queued") == 1
        duplicate_messages = [
            event
            for event in events
            if event["type"] == "agent.message"
            and event["payload"] == {"text": "TESTAUTOMA-1001 is already running."}
        ]
        assert len(duplicate_messages) == 3
        await pipeline.started_event("TESTAUTOMA-1001").wait()
        assert pipeline.started == ["TESTAUTOMA-1001"]
        gate.set()
        await queue.join()
    finally:
        gate.set()
        await queue.shutdown()


@pytest.mark.asyncio
async def test_worker_failure_is_isolated_and_error_is_safe(tmp_path: Path) -> None:
    store, event_bus, pipeline = await _harness(tmp_path)
    secret = "bearer-secret-value"
    url = "https://token@example.invalid/repo"
    pipeline.failures["TESTAUTOMA-1001"] = RuntimeError(f"{secret} {url}")
    queue = TrackQueue(
        track_id="enovia",
        state_store=store,
        event_bus=event_bus,
        pipeline=pipeline,  # type: ignore[arg-type]
    )
    try:
        failed_id = await queue.enqueue("TESTAUTOMA-1001", "diagnose", None)
        completed_id = await queue.enqueue("TESTAUTOMA-1002", "diagnose", None)
        await queue.join()
        failed = await store.get_run(failed_id)
        completed = await store.get_run(completed_id)
        assert failed is not None and failed["status"] == "failed"
        assert completed is not None and completed["status"] == "completed"
        assert pipeline.completed == ["TESTAUTOMA-1002"]
        serialized = json.dumps(
            {
                "row": failed,
                "events": await store.list_events(failed_id),
            }
        )
        assert secret not in serialized
        assert url not in serialized
        assert "queue_worker_error" in serialized
        assert (
            "The run failed unexpectedly. Earlier artifacts were preserved."
            in serialized
        )
        assert queue._worker_task is not None and not queue._worker_task.done()
    finally:
        await queue.shutdown()


@pytest.mark.asyncio
async def test_tracks_have_independent_workers(tmp_path: Path) -> None:
    store, event_bus, enovia_pipeline = await _harness(tmp_path)
    oracle_pipeline = ControlledPipeline(store, event_bus)
    enovia_gate = enovia_pipeline.gate("TESTAUTOMA-1001")
    enovia = TrackQueue(
        track_id="enovia",
        state_store=store,
        event_bus=event_bus,
        pipeline=enovia_pipeline,  # type: ignore[arg-type]
    )
    oracle = TrackQueue(
        track_id="oracle",
        state_store=store,
        event_bus=event_bus,
        pipeline=oracle_pipeline,  # type: ignore[arg-type]
    )
    try:
        await enovia.enqueue("TESTAUTOMA-1001", "diagnose", None)
        await enovia_pipeline.started_event("TESTAUTOMA-1001").wait()
        await oracle.enqueue("TESTAUTOMA-2001", "diagnose", None)
        await oracle.join()
        assert oracle_pipeline.completed == ["TESTAUTOMA-2001"]
        assert enovia_pipeline.completed == []
        enovia_gate.set()
        await enovia.join()
    finally:
        enovia_gate.set()
        await enovia.shutdown()
        await oracle.shutdown()


@pytest.mark.asyncio
async def test_cancel_queued_and_running_runs_without_killing_worker(
    tmp_path: Path,
) -> None:
    store, event_bus, pipeline = await _harness(tmp_path)
    running_gate = pipeline.gate("TESTAUTOMA-1001")
    queue = TrackQueue(
        track_id="enovia",
        state_store=store,
        event_bus=event_bus,
        pipeline=pipeline,  # type: ignore[arg-type]
    )
    try:
        running_id = await queue.enqueue("TESTAUTOMA-1001", "diagnose", None)
        queued_id = await queue.enqueue("TESTAUTOMA-1002", "diagnose", None)
        await pipeline.started_event("TESTAUTOMA-1001").wait()
        assert await queue.cancel(queued_id)
        assert await queue.cancel(queued_id)
        assert await queue.cancel(running_id)
        later_id = await queue.enqueue("TESTAUTOMA-1003", "diagnose", None)
        await queue.join()
        assert pipeline.started == ["TESTAUTOMA-1001", "TESTAUTOMA-1003"]
        for run_id in (running_id, queued_id):
            row = await store.get_run(run_id)
            assert row is not None
            assert row["status"] == "cancelled"
            assert row["completed_at"] is not None
            events = await store.list_events(run_id)
            terminal = [event for event in events if event["type"] == "run.failed"]
            assert len(terminal) == 1
            assert terminal[0]["payload"]["summary"]["status"] == "cancelled"
        later = await store.get_run(later_id)
        assert later is not None and later["status"] == "completed"
        assert queue._worker_task is not None and not queue._worker_task.done()
    finally:
        running_gate.set()
        await queue.shutdown()


@pytest.mark.asyncio
async def test_terminal_cleanup_allows_same_ticket_to_run_again(tmp_path: Path) -> None:
    store, event_bus, pipeline = await _harness(tmp_path)
    queue = TrackQueue(
        track_id="enovia",
        state_store=store,
        event_bus=event_bus,
        pipeline=pipeline,  # type: ignore[arg-type]
    )
    try:
        first_id = await queue.enqueue("TESTAUTOMA-1001", "diagnose", None)
        await queue.join()
        second_id = await queue.enqueue("TESTAUTOMA-1001", "diagnose", None)
        await queue.join()
        assert first_id != second_id
        assert pipeline.started == ["TESTAUTOMA-1001", "TESTAUTOMA-1001"]
        assert len(await _all_runs(store)) == 2
    finally:
        await queue.shutdown()


@pytest.mark.asyncio
async def test_graceful_shutdown_drains_fifo_and_is_idempotent(tmp_path: Path) -> None:
    store, event_bus, pipeline = await _harness(tmp_path)
    tickets = ["TESTAUTOMA-1001", "TESTAUTOMA-1002", "TESTAUTOMA-1003"]
    gates = {ticket: pipeline.gate(ticket) for ticket in tickets}
    queue = TrackQueue(
        track_id="enovia",
        state_store=store,
        event_bus=event_bus,
        pipeline=pipeline,  # type: ignore[arg-type]
    )
    for ticket in tickets:
        await queue.enqueue(ticket, "diagnose", None)
    await pipeline.started_event(tickets[0]).wait()
    shutdown = asyncio.create_task(queue.shutdown(drain=True))
    for ticket in tickets:
        gates[ticket].set()
        if ticket != tickets[-1]:
            await pipeline.started_event(tickets[tickets.index(ticket) + 1]).wait()
    await asyncio.wait_for(shutdown, timeout=3)
    assert pipeline.completed == tickets
    assert queue._worker_task is None
    await queue.shutdown(drain=True)
    with pytest.raises(RuntimeError, match="shut down"):
        await queue.start()
    with pytest.raises(RuntimeError, match="shut down"):
        await queue.enqueue("TESTAUTOMA-1004", "diagnose", None)


@pytest.mark.asyncio
async def test_immediate_shutdown_cancels_current_and_pending_without_leaks(
    tmp_path: Path,
) -> None:
    store, event_bus, pipeline = await _harness(tmp_path)
    gate = pipeline.gate("TESTAUTOMA-1001")
    queue = TrackQueue(
        track_id="enovia",
        state_store=store,
        event_bus=event_bus,
        pipeline=pipeline,  # type: ignore[arg-type]
    )
    run_ids = [
        await queue.enqueue(f"TESTAUTOMA-{number}", "diagnose", None)
        for number in (1001, 1002, 1003)
    ]
    await pipeline.started_event("TESTAUTOMA-1001").wait()
    await asyncio.wait_for(queue.shutdown(drain=False), timeout=3)
    for run_id in run_ids:
        row = await store.get_run(run_id)
        assert row is not None
        assert row["status"] == "cancelled"
        assert row["completed_at"] is not None
        events = await store.list_events(run_id)
        terminal = [event for event in events if event["type"] == "run.failed"]
        assert len(terminal) == 1
        assert terminal[0]["payload"]["summary"]["reason"] == "cancelled"
    assert pipeline.started == ["TESTAUTOMA-1001"]
    assert queue._worker_task is None
    assert queue._current_task is None
    assert not queue._active_by_run_id
    assert not queue._active_by_ticket
    assert queue._queue.empty()
    gate.set()
