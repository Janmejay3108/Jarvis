from __future__ import annotations

import asyncio
from dataclasses import asdict
from pathlib import Path

import aiosqlite
import pytest

from src.orchestrator.events import EventBus
from src.orchestrator.state_store import StateStore


async def _store(tmp_path: Path) -> StateStore:
    store = StateStore(str(tmp_path / "agent.db"))
    await store.initialize()
    return store


async def _wait_for_subscribers(
    bus: EventBus,
    run_id: str,
    expected: int,
) -> None:
    for _attempt in range(1_000):
        if bus.subscriber_count(run_id) == expected:
            return
        await asyncio.sleep(0.001)
    pytest.fail(f"Expected {expected} subscribers for {run_id}")


@pytest.mark.asyncio
async def test_schema_creation(tmp_path: Path) -> None:
    store = await _store(tmp_path)

    async with aiosqlite.connect(store.db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
        tables = {row[0] for row in await cursor.fetchall()}

    assert {
        "conversations",
        "messages",
        "runs",
        "run_steps",
        "events",
        "approvals",
    } <= tables


@pytest.mark.asyncio
async def test_conversation_crud(tmp_path: Path) -> None:
    store = await _store(tmp_path)
    conversation_id = await store.create_conversation("Ticket diagnosis")
    message_id = await store.save_message(
        conversation_id,
        "user",
        "Investigate TESTAUTOMA-8055",
    )

    conversation = await store.get_conversation(conversation_id)
    conversations = await store.list_conversations()
    messages = await store.list_messages(conversation_id)

    assert conversation is not None
    assert conversation["title"] == "Ticket diagnosis"
    assert conversations == [conversation]
    assert messages[0]["id"] == message_id
    assert messages[0]["content"] == "Investigate TESTAUTOMA-8055"


@pytest.mark.asyncio
async def test_run_lifecycle(tmp_path: Path) -> None:
    store = await _store(tmp_path)
    conversation_id = await store.create_conversation()
    run_id = await store.create_run(
        "TESTAUTOMA-8055",
        "enovia",
        "diagnose",
        conversation_id,
    )
    step_id = await store.append_step(run_id, "collect_evidence")
    await store.complete_step(step_id)
    await store.update_run(
        run_id,
        status="completed",
        completed_at="2026-08-02T12:00:00+00:00",
        tokens_in=120,
        summary_json={"result": "diagnosed"},
    )

    run = await store.get_run(run_id)
    steps = await store.list_steps(run_id)

    assert run is not None
    assert run["status"] == "completed"
    assert run["tokens_in"] == 120
    assert run["summary_json"] == '{"result": "diagnosed"}'
    assert steps[0]["status"] == "completed"
    assert steps[0]["completed_at"] is not None


@pytest.mark.asyncio
async def test_event_persistence(tmp_path: Path) -> None:
    store = await _store(tmp_path)
    first_id = await store.append_event("run-1", "step.started", {"step": 1})
    second_id = await store.append_event("run-1", "step.completed", {"step": 1})

    events = await store.list_events("run-1")

    assert [event["event_id"] for event in events] == [first_id, second_id]
    assert [event["type"] for event in events] == [
        "step.started",
        "step.completed",
    ]
    assert events[0]["payload"] == {"step": 1}


@pytest.mark.asyncio
async def test_event_list_after_filter(tmp_path: Path) -> None:
    store = await _store(tmp_path)
    event_ids = [
        await store.append_event("run-1", "step.progress", {"index": index})
        for index in range(5)
    ]

    events = await store.list_events("run-1", after=event_ids[2])

    assert [event["event_id"] for event in events] == event_ids[3:]
    assert [event["payload"]["index"] for event in events] == [3, 4]


@pytest.mark.asyncio
async def test_approval_flow(tmp_path: Path) -> None:
    store = await _store(tmp_path)
    approval_id = await store.request_approval("run-1", {"diff": "candidate"})
    await store.resolve_approval(approval_id, "approve", "Looks correct")

    approval = await store.get_approval(approval_id)

    assert approval is not None
    assert approval["requested_at"] is not None
    assert approval["resolved_at"] is not None
    assert approval["decision"] == "approve"
    assert approval["comment"] == "Looks correct"
    assert approval["payload"] == {"diff": "candidate"}


@pytest.mark.asyncio
async def test_eventbus_publish_persists(tmp_path: Path) -> None:
    store = await _store(tmp_path)
    bus = EventBus(store)

    published = await bus.publish(
        "run-1",
        "agent.message",
        {"text": "Collecting evidence"},
        cost_usd_so_far=0.42,
    )
    persisted = await store.list_events("run-1")

    assert persisted == [asdict(published)]


@pytest.mark.asyncio
async def test_eventbus_subscribe_replay_then_live(tmp_path: Path) -> None:
    store = await _store(tmp_path)
    bus = EventBus(store)
    published = [
        await bus.publish("run-1", "run.queued", {"index": 0}),
        await bus.publish("run-1", "step.started", {"index": 1}),
    ]
    stream = bus.subscribe("run-1")

    received = [await anext(stream), await anext(stream)]
    published.append(await bus.publish("run-1", "step.completed", {"index": 2}))
    received.append(await anext(stream))
    await stream.aclose()

    assert received == published
    assert bus.subscriber_count("run-1") == 0


@pytest.mark.asyncio
async def test_eventbus_multiple_subscribers(tmp_path: Path) -> None:
    store = await _store(tmp_path)
    bus = EventBus(store)
    first_stream = bus.subscribe("run-1")
    second_stream = bus.subscribe("run-1")
    first_next = asyncio.ensure_future(anext(first_stream))
    second_next = asyncio.ensure_future(anext(second_stream))
    await _wait_for_subscribers(bus, "run-1", 2)

    published = await bus.publish("run-1", "run.queued", {"ticket": "T-1"})
    first, second = await asyncio.gather(first_next, second_next)
    await first_stream.aclose()
    await second_stream.aclose()

    assert first == second == published
    assert bus.subscriber_count("run-1") == 0


@pytest.mark.asyncio
async def test_full_replay_equals_live(tmp_path: Path) -> None:
    store = await _store(tmp_path)
    bus = EventBus(store)
    stream = bus.subscribe("run-1")
    first_next = asyncio.ensure_future(anext(stream))
    await _wait_for_subscribers(bus, "run-1", 1)

    published = [
        await bus.publish(
            "run-1",
            "step.progress",
            {"index": index},
            cost_usd_so_far=index / 10,
        )
        for index in range(5)
    ]
    received = [await first_next]
    received.extend([await anext(stream) for _event in published[1:]])
    await stream.aclose()
    persisted = await store.list_events("run-1")

    assert received == published
    assert [asdict(event) for event in received] == persisted