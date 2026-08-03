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
        "jira_actions",
    } <= tables


@pytest.mark.asyncio
async def test_jira_actions_migrate_existing_plan0_database_without_data_loss(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "agent.db"
    old_schema = """
    CREATE TABLE conversations (id TEXT PRIMARY KEY, title TEXT, created_at TEXT, updated_at TEXT);
    CREATE TABLE messages (id TEXT PRIMARY KEY, conversation_id TEXT, role TEXT, content TEXT, run_id TEXT NULL, ts TEXT);
    CREATE TABLE runs (run_id TEXT PRIMARY KEY, ticket_key TEXT, track_id TEXT, mode TEXT, status TEXT, conversation_id TEXT, created_at TEXT, completed_at TEXT, tokens_in INTEGER DEFAULT 0, tokens_out INTEGER DEFAULT 0, cost_usd REAL DEFAULT 0.0, summary_json TEXT);
    CREATE TABLE run_steps (id TEXT PRIMARY KEY, run_id TEXT, name TEXT, status TEXT, started_at TEXT, completed_at TEXT, detail TEXT, error TEXT);
    CREATE TABLE events (event_id TEXT PRIMARY KEY, run_id TEXT, ts TEXT, type TEXT, payload_json TEXT);
    CREATE TABLE approvals (id TEXT PRIMARY KEY, run_id TEXT, requested_at TEXT, resolved_at TEXT, decision TEXT, comment TEXT, payload_json TEXT);
    """
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(old_schema)
        await db.execute(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?, NULL, ?, NULL, 0, 0, 0.0, ?)",
            (
                "sentinel-run",
                "TESTAUTOMA-8055",
                "enovia",
                "diagnose",
                "completed",
                "2026-08-03T12:00:00+00:00",
                "{}",
            ),
        )
        await db.commit()

    store = StateStore(str(db_path))
    await store.initialize()
    await store.initialize()

    assert (await store.get_run("sentinel-run"))["ticket_key"] == "TESTAUTOMA-8055"
    async with aiosqlite.connect(db_path) as db:
        table = await db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'jira_actions'"
        )
        index = await db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name = 'jira_actions_run_id_idx'"
        )
        assert await table.fetchone() == ("jira_actions",)
        assert await index.fetchone() == ("jira_actions_run_id_idx",)


@pytest.mark.asyncio
async def test_jira_action_crud_hydrates_intent_and_validates_states(
    tmp_path: Path,
) -> None:
    store = await _store(tmp_path)
    first = await store.create_jira_action(
        "run-1",
        "TESTAUTOMA-8055",
        "post_comment",
        {"kind": "diagnosis_comment", "source": "diagnosis_artifact"},
        action_id="action-1",
    )
    second = await store.create_jira_action(
        "run-1",
        "TESTAUTOMA-8055",
        "add_label",
        {"label": "ai-diagnosed"},
        action_id="action-2",
    )

    assert first["state"] == "pending"
    assert first["check_result"] == "unknown"
    assert first["attempts"] == 0
    assert first["intent"] == {
        "kind": "diagnosis_comment",
        "source": "diagnosis_artifact",
    }
    assert "intent_json" not in first
    assert [action["action_id"] for action in await store.list_jira_actions("run-1")] == [
        "action-1",
        "action-2",
    ]

    begun = await store.begin_jira_action_attempt("action-1")
    assert begun["attempts"] == 1
    assert begun["created_at"] == first["created_at"]
    assert begun["updated_at"] >= first["updated_at"]
    succeeded = await store.update_jira_action(
        "action-1",
        state="succeeded",
        check_result="present",
    )
    assert succeeded["state"] == "succeeded"
    assert succeeded["check_result"] == "present"
    assert succeeded["attempts"] == 1
    assert await store.get_jira_action("action-1") == succeeded
    assert second["action_id"] == "action-2"

    with pytest.raises(KeyError):
        await store.begin_jira_action_attempt("missing")
    with pytest.raises(KeyError):
        await store.update_jira_action("missing", state="failed")
    with pytest.raises(ValueError, match="state"):
        await store.update_jira_action("action-1", state="invalid")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="check result"):
        await store.update_jira_action(
            "action-1",
            state="failed",
            check_result="invalid",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="negative"):
        await store.update_jira_action("action-1", state="failed", attempts=-1)


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