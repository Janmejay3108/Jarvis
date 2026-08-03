from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.models.run import AgentRun, RunStatus
from src.orchestrator.events import EventBus
from src.orchestrator.state_store import StateStore


async def _runtime(tmp_path: Path) -> tuple[StateStore, EventBus]:
    store = StateStore(str(tmp_path / "agent.db"))
    await store.initialize()
    return store, EventBus(store)


def test_run_status_contract_is_complete_and_ordered() -> None:
    expected = [
        "queued",
        "reading_ticket",
        "localizing",
        "fetching_logs",
        "analyzing",
        "generating_fix",
        "applying_fix",
        "linting",
        "validating_local",
        "validating_dai",
        "awaiting_approval",
        "publishing",
        "updating_jira",
        "completed",
        "failed",
        "cancelled",
        "low_confidence",
        "exhausted",
    ]

    assert [status.value for status in RunStatus] == expected
    assert RunStatus.validating_local.value == "validating_local"
    assert RunStatus.validating_dai.value == "validating_dai"


def test_agent_run_defaults_validation_and_serialization() -> None:
    first = AgentRun(ticket_key="TESTAUTOMA-8055", mode="diagnose")
    second = AgentRun(ticket_key="TESTAUTOMA-8278", mode="autofix")

    assert re.fullmatch(r"run-\d{8}-\d{6}-\d{6}", first.run_id)
    assert first.created_at.tzinfo is UTC
    assert first.track_id == "enovia"
    assert first.status is RunStatus.queued
    assert first.tokens_in == first.tokens_out == 0
    assert first.cost_usd == 0.0
    assert first.steps == []
    assert first.scripts == {}
    assert first.blast_radius == {}
    assert first.screenshots == []
    assert {first.mode, second.mode} == {"diagnose", "autofix"}

    first.scripts["test.script"] = "log success"
    first.blast_radius["searchEnovia"] = ["CommonEnovia.script:409"]
    first.screenshots.append("failure.png")
    assert second.scripts == {}
    assert second.blast_radius == {}
    assert second.screenshots == []

    with pytest.raises(ValidationError):
        AgentRun(ticket_key="TESTAUTOMA-1", mode="repair")
    with pytest.raises(ValidationError):
        AgentRun(ticket_key="TESTAUTOMA-1", mode="diagnose", tokens_in=-1)
    with pytest.raises(ValidationError):
        AgentRun(ticket_key="TESTAUTOMA-1", mode="diagnose", tokens_out=-1)
    with pytest.raises(ValidationError):
        AgentRun(ticket_key="TESTAUTOMA-1", mode="diagnose", cost_usd=-0.01)

    serialized = first.model_dump(mode="json")
    assert isinstance(serialized["created_at"], str)
    assert serialized["status"] == "queued"


@pytest.mark.asyncio
async def test_create_persists_matching_run_and_hides_runtime_collaborators(
    tmp_path: Path,
) -> None:
    store, bus = await _runtime(tmp_path)
    run = await AgentRun.create(
        store,
        bus,
        ticket_key="TESTAUTOMA-8055",
        mode="diagnose",
        conversation_id="conversation-1",
    )

    persisted = await store.get_run(run.run_id)
    assert persisted is not None
    assert persisted["run_id"] == run.run_id
    assert persisted["ticket_key"] == run.ticket_key
    assert persisted["track_id"] == run.track_id
    assert persisted["mode"] == run.mode
    assert persisted["conversation_id"] == run.conversation_id
    assert persisted["status"] == "queued"
    assert persisted["created_at"] == run.created_at.isoformat()

    serialized = run.model_dump(mode="json")
    assert not {
        "_state_store",
        "_event_bus",
        "_active_step",
        "_active_step_id",
    } & serialized.keys()


@pytest.mark.asyncio
async def test_begin_persists_step_and_publishes_master_envelope(
    tmp_path: Path,
) -> None:
    store, bus = await _runtime(tmp_path)
    run = await AgentRun.create(
        store,
        bus,
        ticket_key="TESTAUTOMA-8055",
        mode="diagnose",
    )
    run.cost_usd = 0.42

    step = await run.begin(
        "collect_evidence",
        RunStatus.fetching_logs,
        "Fetching production DAI logs",
    )

    persisted_run = await store.get_run(run.run_id)
    persisted_steps = await store.list_steps(run.run_id)
    events = await store.list_events(run.run_id)
    assert run.status is RunStatus.fetching_logs
    assert run.steps == [step]
    assert run._active_step is step
    assert persisted_run is not None
    assert persisted_run["status"] == "fetching_logs"
    assert persisted_steps[0]["name"] == step.name
    assert persisted_steps[0]["status"] == "started"
    assert persisted_steps[0]["started_at"] == step.started_at.isoformat()
    assert persisted_steps[0]["detail"] == step.detail

    event = events[0]
    assert set(event) == {
        "event_id",
        "run_id",
        "ts",
        "type",
        "payload",
        "cost_usd_so_far",
    }
    assert event["type"] == "step.started"
    assert set(event["payload"]) == {
        "name",
        "status",
        "started_at",
        "completed_at",
        "detail",
        "error",
    }
    assert event["payload"] == step.model_dump(mode="json")
    assert datetime.fromisoformat(event["payload"]["started_at"]).tzinfo is not None
    assert event["cost_usd_so_far"] == 0.42


@pytest.mark.asyncio
async def test_end_success_persists_detail_and_publishes_completed(
    tmp_path: Path,
) -> None:
    store, bus = await _runtime(tmp_path)
    run = await AgentRun.create(
        store,
        bus,
        ticket_key="TESTAUTOMA-8055",
        mode="diagnose",
    )
    await run.begin("collect_evidence", RunStatus.fetching_logs, "In progress")

    step = await run.end()

    persisted_steps = await store.list_steps(run.run_id)
    events = await store.list_events(run.run_id)
    assert step.status == "completed"
    assert step.completed_at is not None
    assert step.detail == "In progress"
    assert persisted_steps[0]["completed_at"] == step.completed_at.isoformat()
    assert persisted_steps[0]["detail"] == "In progress"
    assert persisted_steps[0]["error"] == ""
    assert events[-1]["type"] == "step.completed"
    assert events[-1]["payload"] == step.model_dump(mode="json")
    assert events[-1]["payload"]["detail"] == "In progress"
    assert run._active_step is None
    assert run._active_step_id is None

    next_step = await run.begin("analyze", RunStatus.analyzing, "Analyzing")
    assert run._active_step is next_step
    cleared_step = await run.end(detail="")

    persisted_steps = await store.list_steps(run.run_id)
    events = await store.list_events(run.run_id)
    assert cleared_step.status == "completed"
    assert cleared_step.completed_at is not None
    assert cleared_step.detail == ""
    assert persisted_steps[1]["completed_at"] == cleared_step.completed_at.isoformat()
    assert persisted_steps[1]["detail"] == ""
    assert persisted_steps[1]["error"] == ""
    assert events[-1]["type"] == "step.completed"
    assert events[-1]["payload"] == cleared_step.model_dump(mode="json")
    assert events[-1]["payload"]["detail"] == ""
    assert run._active_step is None
    assert run._active_step_id is None


@pytest.mark.asyncio
async def test_end_error_fails_step_and_run_and_publishes_failed(
    tmp_path: Path,
) -> None:
    store, bus = await _runtime(tmp_path)
    run = await AgentRun.create(
        store,
        bus,
        ticket_key="TESTAUTOMA-8055",
        mode="diagnose",
    )
    run.cost_usd = 1.25
    await run.begin("collect_evidence", RunStatus.fetching_logs)

    step = await run.end(detail="DAI request failed", error="request timed out")

    persisted_run = await store.get_run(run.run_id)
    persisted_steps = await store.list_steps(run.run_id)
    events = await store.list_events(run.run_id)
    assert step.status == "failed"
    assert step.error == "request timed out"
    assert run.status is RunStatus.failed
    assert run.completed_at == step.completed_at
    assert persisted_run is not None
    assert persisted_run["status"] == "failed"
    assert persisted_run["completed_at"] == run.completed_at.isoformat()
    assert persisted_steps[0]["status"] == "failed"
    assert persisted_steps[0]["completed_at"] == step.completed_at.isoformat()
    assert persisted_steps[0]["detail"] == "DAI request failed"
    assert persisted_steps[0]["error"] == "request timed out"
    assert events[-1]["type"] == "step.failed"
    assert events[-1]["payload"] == step.model_dump(mode="json")
    assert events[-1]["cost_usd_so_far"] == 1.25


@pytest.mark.asyncio
async def test_lifecycle_helpers_reject_unbound_or_invalid_sequence(
    tmp_path: Path,
) -> None:
    unbound = AgentRun(ticket_key="TESTAUTOMA-8055", mode="diagnose")
    with pytest.raises(RuntimeError, match="AgentRun.create"):
        await unbound.begin("collect_evidence", RunStatus.fetching_logs)
    with pytest.raises(RuntimeError, match="AgentRun.create"):
        await unbound.end()

    store, bus = await _runtime(tmp_path)
    bound = await AgentRun.create(
        store,
        bus,
        ticket_key="TESTAUTOMA-8055",
        mode="diagnose",
    )
    with pytest.raises(RuntimeError, match="No active step"):
        await bound.end()
    await bound.begin("collect_evidence", RunStatus.fetching_logs)
    with pytest.raises(RuntimeError, match="already active"):
        await bound.begin("analyze", RunStatus.analyzing)
