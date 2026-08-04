from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import httpx
import pytest

from src.integrations.dai_client import LogEntry
from src.integrations.jira_client import JiraWriteUncertain
from src.models.run import AgentRun, RunStatus
from src.orchestrator.events import EventBus
from src.orchestrator.pipeline import (
    DiagnosisOutcome,
    DiagnosisPipeline,
    ErrorMatch,
    LocalizationResult,
    TicketMetadata,
)
from src.orchestrator.state_store import StateStore
from src.utils.budget import BudgetExceeded


class RecordingJira:
    def __init__(
        self,
        calls: list[str],
        ticket: dict[str, Any],
        *,
        comment_error: BaseException | None = None,
        label_error: BaseException | None = None,
    ) -> None:
        self.calls = calls
        self.ticket = ticket
        self.comment_error = comment_error
        self.label_error = label_error

    async def get_ticket(self, key: str) -> dict[str, Any]:
        self.calls.append(f"jira.get_ticket:{key}")
        return deepcopy(self.ticket)

    async def post_comment(self, key: str, body: str) -> None:
        self.calls.append(f"jira.post_comment:{key}:{body}")
        if self.comment_error is not None:
            raise self.comment_error

    async def add_label(self, key: str, label: str) -> None:
        self.calls.append(f"jira.add_label:{key}:{label}")
        if self.label_error is not None:
            raise self.label_error


def _http_status_error(status_code: int, message: str) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://jira.example.test/rest/api/2/issue/T-1")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError(message, request=request, response=response)


class RecordingEvidence:
    def __init__(
        self,
        calls: list[str],
        logs: list[LogEntry],
        screenshot_log: LogEntry | None,
    ) -> None:
        self.calls = calls
        self.logs = logs
        self.screenshot_log = screenshot_log

    async def log_by_runid(self, runid: str) -> list[LogEntry]:
        self.calls.append(f"evidence.log_by_runid:{runid}")
        return self.logs

    async def fetch_screenshot(self, image_id: str, dest: Path) -> Path:
        self.calls.append(f"evidence.fetch_screenshot:{image_id}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"png")
        return dest

    def walk_back_to_screenshot(
        self,
        logs: list[LogEntry],
        error_index: int,
    ) -> LogEntry | None:
        assert logs is self.logs
        self.calls.append(f"evidence.walk_back:{error_index}")
        return self.screenshot_log


class RecordingExtractor:
    def __init__(
        self,
        calls: list[str],
        metadata: TicketMetadata,
        *,
        fail_if_called: bool = False,
    ) -> None:
        self.calls = calls
        self.metadata = metadata
        self.fail_if_called = fail_if_called
        self.framed_ticket = ""

    async def extract(self, framed_ticket: str) -> TicketMetadata:
        if self.fail_if_called:
            raise AssertionError("extractor must be skipped")
        self.calls.append("extractor.extract")
        self.framed_ticket = framed_ticket
        return self.metadata.model_copy(deep=True)


class RecordingMatcher:
    def __init__(self, calls: list[str], match: ErrorMatch) -> None:
        self.calls = calls
        self.match_result = match
        self.framed_logs = ""
        self.title = ""
        self.description = ""

    async def match(
        self,
        framed_logs: str,
        title: str,
        description: str,
    ) -> ErrorMatch:
        self.calls.append("matcher.match")
        self.framed_logs = framed_logs
        self.title = title
        self.description = description
        return self.match_result


class RecordingLocalizer:
    def __init__(
        self,
        calls: list[str],
        result: LocalizationResult,
        error: BaseException | None = None,
    ) -> None:
        self.calls = calls
        self.result = result
        self.error = error

    async def localize(
        self,
        run: AgentRun,
        metadata: TicketMetadata,
        matched_log: LogEntry,
    ) -> LocalizationResult:
        self.calls.append("localizer.localize")
        assert metadata.runid is not None
        assert matched_log.message is not None
        if self.error is not None:
            raise self.error
        return self.result.model_copy(deep=True)


class RecordingDiagnoser:
    def __init__(
        self,
        calls: list[str],
        outcome: DiagnosisOutcome,
        error: BaseException | None = None,
    ) -> None:
        self.calls = calls
        self.outcome = outcome
        self.error = error

    async def diagnose(self, run: AgentRun) -> DiagnosisOutcome:
        self.calls.append("diagnoser.diagnose")
        assert run.logs is not None
        if self.error is not None:
            raise self.error
        return self.outcome.model_copy(deep=True)


class RecordingFormatter:
    def __init__(
        self,
        calls: list[str],
        error: BaseException | None = None,
    ) -> None:
        self.calls = calls
        self.error = error

    def __call__(self, diagnosis: dict[str, Any], ticket_key: str) -> str:
        self.calls.append(f"formatter:{ticket_key}")
        if self.error is not None:
            raise self.error
        return f"Diagnosis: {diagnosis['root_cause']}"


class Harness:
    def __init__(
        self,
        *,
        store: StateStore,
        bus: EventBus,
        run: AgentRun,
        pipeline: DiagnosisPipeline,
        calls: list[str],
        jira: RecordingJira,
        evidence: RecordingEvidence,
        extractor: RecordingExtractor,
        matcher: RecordingMatcher,
        localizer: RecordingLocalizer,
        diagnoser: RecordingDiagnoser,
        formatter: RecordingFormatter,
    ) -> None:
        self.store = store
        self.bus = bus
        self.run = run
        self.pipeline = pipeline
        self.calls = calls
        self.jira = jira
        self.evidence = evidence
        self.extractor = extractor
        self.matcher = matcher
        self.localizer = localizer
        self.diagnoser = diagnoser
        self.formatter = formatter


async def _harness(
    tmp_path: Path,
    *,
    runid: str | None = "30832",
    match_index: int = 2,
    screenshot: bool = True,
    jira_writes_enabled: bool = True,
    localizer_error: BaseException | None = None,
    diagnoser_error: BaseException | None = None,
    formatter_error: BaseException | None = None,
    comment_error: BaseException | None = None,
    label_error: BaseException | None = None,
    extractor_must_be_skipped: bool = False,
) -> Harness:
    calls: list[str] = []
    store = StateStore(str(tmp_path / "agent.db"))
    await store.initialize()
    bus = EventBus(store)
    run = await AgentRun.create(
        store,
        bus,
        ticket_key="TESTAUTOMA-8055",
        mode="diagnose",
    )
    ticket = {
        "key": "TESTAUTOMA-8055",
        "fields": {
            "summary": "Ticket field summary",
            "description": "Ticket field description",
            "custom": "![active](https://unsafe.example/image.png)",
        },
    }
    logs = [
        LogEntry(
            message="Setup complete",
            severity="INFORMATIONAL",
            message_type="log",
        ),
        LogEntry(
            message="Captured failing screen",
            severity="INFORMATIONAL",
            message_type="imagefound",
            image_id="image-1",
        ),
        LogEntry(
            message="Unable to find Released",
            severity="INFORMATIONAL",
            message_type="imagefound",
        ),
    ]
    jira = RecordingJira(
        calls,
        ticket,
        comment_error=comment_error,
        label_error=label_error,
    )
    evidence = RecordingEvidence(calls, logs, logs[1] if screenshot else None)
    extractor = RecordingExtractor(
        calls,
        TicketMetadata(
            runid=runid,
            title="Released lookup failed",
            description="The Released field was not found",
            test_script_name="TESTAUTOMA_8055",
        ),
        fail_if_called=extractor_must_be_skipped,
    )
    matcher = RecordingMatcher(
        calls,
        ErrorMatch(index=match_index, reasoning="Matches the ticket"),
    )
    localizer = RecordingLocalizer(
        calls,
        LocalizationResult(
            scripts={"EngineeringCentral.suite/Scripts/TestCases/test.script": "run test"},
            call_chain=["test", "searchEnovia"],
            blast_radius={"searchEnovia": ["CommonEnovia.script:409"]},
        ),
        localizer_error,
    )
    diagnoser = RecordingDiagnoser(
        calls,
        DiagnosisOutcome(
            diagnosis={"root_cause": "Boolean condition rejects the valid state"},
            tokens_in=120,
            tokens_out=30,
            cost_usd=0.75,
        ),
        diagnoser_error,
    )
    formatter = RecordingFormatter(calls, formatter_error)
    pipeline = DiagnosisPipeline(
        state_store=store,
        event_bus=bus,
        jira=jira,
        evidence=evidence,
        ticket_extractor=extractor,
        error_matcher=matcher,
        localizer=localizer,
        diagnoser=diagnoser,
        format_for_jira=formatter,
        jira_writes_enabled=jira_writes_enabled,
        artifact_root=tmp_path / "artifacts",
    )
    return Harness(
        store=store,
        bus=bus,
        run=run,
        pipeline=pipeline,
        calls=calls,
        jira=jira,
        evidence=evidence,
        extractor=extractor,
        matcher=matcher,
        localizer=localizer,
        diagnoser=diagnoser,
        formatter=formatter,
    )


@pytest.mark.asyncio
async def test_pipeline_happy_path_persists_order_events_artifacts_and_totals(
    tmp_path: Path,
) -> None:
    harness = await _harness(tmp_path)

    result = await harness.pipeline.execute(harness.run)

    assert result is harness.run
    assert result.status is RunStatus.completed
    actions = await harness.store.list_jira_actions(result.run_id)
    assert harness.calls == [
        "jira.get_ticket:TESTAUTOMA-8055",
        "extractor.extract",
        "evidence.log_by_runid:30832",
        "matcher.match",
        "evidence.walk_back:2",
        "evidence.fetch_screenshot:image-1",
        "localizer.localize",
        "diagnoser.diagnose",
        "formatter:TESTAUTOMA-8055",
        (
            "jira.post_comment:TESTAUTOMA-8055:Diagnosis: Boolean condition rejects "
            f"the valid state\n\n[JARVIS action_id={actions[0]['action_id']}]"
        ),
        "jira.add_label:TESTAUTOMA-8055:ai-diagnosed",
    ]
    steps = await harness.store.list_steps(result.run_id)
    assert [step["name"] for step in steps] == [
        "read_ticket",
        "fetch_logs",
        "localize",
        "analyze",
        "post_diagnosis",
    ]
    events = await harness.store.list_events(result.run_id)
    assert [event["type"] for event in events] == [
        "step.started",
        "agent.message",
        "step.completed",
        "step.started",
        "agent.message",
        "step.completed",
        "step.started",
        "agent.message",
        "step.completed",
        "step.started",
        "agent.message",
        "step.completed",
        "artifact",
        "step.started",
        "agent.message",
        "jira.action.updated",
        "jira.action.updated",
        "jira.action.updated",
        "jira.action.updated",
        "jira.action.updated",
        "jira.action.updated",
        "step.completed",
        "run.completed",
    ]
    artifact = next(event for event in events if event["type"] == "artifact")
    assert artifact["payload"] == {
        "kind": "diagnosis",
        "data": result.diagnosis,
    }
    assert events[-1]["payload"]["totals"] == {
        "tokens_in": 120,
        "tokens_out": 30,
        "cost_usd": 0.75,
    }
    assert events[-1]["cost_usd_so_far"] == 0.75
    assert len(result.screenshots) == 1
    assert result.screenshots[0].endswith(f"{result.run_id}\\failure.png")
    assert Path(result.screenshots[0]).read_bytes() == b"png"
    persisted = await harness.store.get_run(result.run_id)
    assert persisted is not None
    assert persisted["status"] == "completed"
    assert persisted["completed_at"] == result.completed_at.isoformat()
    assert persisted["tokens_in"] == 120
    assert persisted["tokens_out"] == 30
    assert persisted["cost_usd"] == 0.75
    assert json.loads(persisted["summary_json"]) == {
        "ticket_key": "TESTAUTOMA-8055",
        "status": "completed",
        "reason": "diagnosed",
    }
    assert harness.extractor.framed_ticket.startswith("<<<TICKET_START>>>\n")
    assert harness.extractor.framed_ticket.endswith("\n<<<TICKET_END>>>")
    assert "https://unsafe.example" not in harness.extractor.framed_ticket
    assert harness.matcher.framed_logs.startswith("<<<DAI_LOG_START>>>\n")
    assert harness.matcher.framed_logs.endswith("\n<<<DAI_LOG_END>>>")
    for index in range(3):
        assert f'"i": {index}' in harness.matcher.framed_logs
    assert harness.matcher.framed_logs.count('"severity": "INFORMATIONAL"') == 3


@pytest.mark.asyncio
async def test_jira_actions_happy_path_are_persisted_footered_and_replayable(
    tmp_path: Path,
) -> None:
    harness = await _harness(tmp_path)

    result = await harness.pipeline.execute(harness.run)

    actions = await harness.store.list_jira_actions(result.run_id)
    assert [action["operation"] for action in actions] == [
        "post_comment",
        "add_label",
    ]
    assert [action["state"] for action in actions] == ["succeeded", "succeeded"]
    assert [action["attempts"] for action in actions] == [1, 1]
    assert actions[0]["intent"] == {
        "kind": "diagnosis_comment",
        "source": "diagnosis_artifact",
    }
    assert actions[1]["intent"] == {"label": "ai-diagnosed"}
    comment_call = next(
        call for call in harness.calls if call.startswith("jira.post_comment:")
    )
    assert comment_call.endswith(
        f"\n\n[JARVIS action_id={actions[0]['action_id']}]"
    )
    action_events = [
        event
        for event in await harness.store.list_events(result.run_id)
        if event["type"] == "jira.action.updated"
    ]
    assert len(action_events) == 6
    allowed = {
        "action_id",
        "operation",
        "state",
        "check_result",
        "attempts",
        "created_at",
        "updated_at",
    }
    assert all(set(event["payload"]) == allowed for event in action_events)
    assert [event["payload"]["attempts"] for event in action_events] == [
        0,
        1,
        1,
        0,
        1,
        1,
    ]
    post_step = (await harness.store.list_steps(result.run_id))[-1]
    assert post_step["detail"] == "Jira publication succeeded (2/2 actions)"

    reopened = StateStore(harness.store.db_path)
    await reopened.initialize()
    persisted = await reopened.list_events(result.run_id)
    stream = EventBus(reopened).subscribe(result.run_id)
    replayed = [await anext(stream) for _event in persisted]
    await stream.aclose()
    assert [event.payload for event in replayed if event.type == "jira.action.updated"] == [
        event["payload"] for event in action_events
    ]


@pytest.mark.asyncio
async def test_definite_comment_failure_does_not_block_label_or_fail_run(
    tmp_path: Path,
) -> None:
    harness = await _harness(
        tmp_path,
        comment_error=_http_status_error(400, "definite failure"),
    )

    result = await harness.pipeline.execute(harness.run)

    actions = await harness.store.list_jira_actions(result.run_id)
    assert [action["state"] for action in actions] == ["failed", "succeeded"]
    assert sum(call.startswith("jira.post_comment:") for call in harness.calls) == 1
    assert sum(call.startswith("jira.add_label:") for call in harness.calls) == 1
    assert result.status is RunStatus.completed
    post_step = (await harness.store.list_steps(result.run_id))[-1]
    assert post_step["status"] == "completed"
    assert post_step["detail"] == (
        "Diagnosis completed; Jira publication needs attention: "
        "post_comment=failed, add_label=succeeded"
    )
    event_types = [
        event["type"] for event in await harness.store.list_events(result.run_id)
    ]
    assert "step.failed" not in event_types
    assert "run.failed" not in event_types


async def _assert_unattempted_comment_failure(
    harness: Harness,
    error_type: str,
) -> None:
    result = await harness.pipeline.execute(harness.run)

    assert result.status is RunStatus.failed
    assert not any(call.startswith("jira.post_comment:") for call in harness.calls)
    assert not any(call.startswith("jira.add_label:") for call in harness.calls)

    reopened = StateStore(harness.store.db_path)
    await reopened.initialize()
    actions = await reopened.list_jira_actions(result.run_id)
    assert len(actions) == 1
    assert actions[0]["operation"] == "post_comment"
    assert actions[0]["state"] == "pending"
    assert actions[0]["attempts"] == 0
    assert actions[0]["check_result"] == "unknown"

    post_step = (await reopened.list_steps(result.run_id))[-1]
    assert post_step["name"] == "post_diagnosis"
    assert post_step["status"] == "failed"
    assert post_step["error"] == error_type

    persisted = await reopened.list_events(result.run_id)
    event_types = [event["type"] for event in persisted]
    assert "step.failed" in event_types
    assert "run.failed" in event_types
    assert "run.completed" not in event_types
    assert persisted[-1]["payload"]["summary"]["reason"] == "pipeline_error"
    action_events = [
        event for event in persisted if event["type"] == "jira.action.updated"
    ]
    assert len(action_events) == 1
    assert action_events[0]["payload"]["state"] == "pending"
    assert action_events[0]["payload"]["attempts"] == 0
    assert set(action_events[0]["payload"]) == {
        "action_id",
        "operation",
        "state",
        "check_result",
        "attempts",
        "created_at",
        "updated_at",
    }

    stream = EventBus(reopened).subscribe(result.run_id)
    replayed = [await anext(stream) for _event in persisted]
    await stream.aclose()
    assert [event.payload for event in replayed if event.type == "jira.action.updated"] == [
        event["payload"] for event in action_events
    ]


@pytest.mark.asyncio
async def test_formatter_failure_fails_run_with_unattempted_pending_comment(
    tmp_path: Path,
) -> None:
    harness = await _harness(
        tmp_path,
        formatter_error=RuntimeError("formatter failed"),
    )

    await _assert_unattempted_comment_failure(harness, "RuntimeError")


@pytest.mark.asyncio
async def test_footer_failure_fails_run_with_unattempted_pending_comment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = await _harness(tmp_path)

    def fail_footer(_body: str, _action_id: str) -> str:
        raise TypeError("footer failed")

    monkeypatch.setattr(
        "src.orchestrator.pipeline.append_jira_action_footer",
        fail_footer,
    )

    await _assert_unattempted_comment_failure(harness, "TypeError")
    assert "formatter:TESTAUTOMA-8055" in harness.calls


@pytest.mark.asyncio
async def test_uncertain_writes_are_not_retried_and_operations_remain_independent(
    tmp_path: Path,
) -> None:
    harness = await _harness(
        tmp_path,
        comment_error=JiraWriteUncertain("post_comment", "TESTAUTOMA-8055"),
    )

    result = await harness.pipeline.execute(harness.run)

    actions = await harness.store.list_jira_actions(result.run_id)
    assert [action["state"] for action in actions] == ["uncertain", "succeeded"]
    assert [action["attempts"] for action in actions] == [1, 1]
    assert sum(call.startswith("jira.post_comment:") for call in harness.calls) == 1
    assert sum(call.startswith("jira.add_label:") for call in harness.calls) == 1
    calls_before_reopen = list(harness.calls)
    reopened = StateStore(harness.store.db_path)
    await reopened.initialize()
    EventBus(reopened)
    assert harness.calls == calls_before_reopen
    assert result.status is RunStatus.completed


@pytest.mark.asyncio
async def test_cancelled_jira_write_leaves_replayable_pending_action(
    tmp_path: Path,
) -> None:
    harness = await _harness(tmp_path, comment_error=asyncio.CancelledError())

    with pytest.raises(asyncio.CancelledError):
        await harness.pipeline.execute(harness.run)

    assert sum(call.startswith("jira.post_comment:") for call in harness.calls) == 1
    assert not any(call.startswith("jira.add_label:") for call in harness.calls)
    reopened = StateStore(harness.store.db_path)
    await reopened.initialize()
    actions = await reopened.list_jira_actions(harness.run.run_id)
    assert len(actions) == 1
    assert actions[0]["operation"] == "post_comment"
    assert actions[0]["state"] == "pending"
    assert actions[0]["attempts"] == 1
    persisted = await reopened.list_events(harness.run.run_id)
    stream = EventBus(reopened).subscribe(harness.run.run_id)
    replayed = [await anext(stream) for _event in persisted]
    await stream.aclose()
    pending = [event for event in replayed if event.type == "jira.action.updated"]
    assert [event.payload["attempts"] for event in pending] == [0, 1]
    assert sum(call.startswith("jira.post_comment:") for call in harness.calls) == 1


@pytest.mark.parametrize(
    ("error", "error_type"),
    [
        (TypeError("adapter type defect"), "TypeError"),
        (AttributeError("adapter attribute defect"), "AttributeError"),
        (AssertionError("adapter assertion defect"), "AssertionError"),
    ],
)
@pytest.mark.asyncio
async def test_jira_write_programming_defect_fails_run_with_pending_action(
    tmp_path: Path,
    error: BaseException,
    error_type: str,
) -> None:
    harness = await _harness(tmp_path, comment_error=error)

    result = await harness.pipeline.execute(harness.run)

    assert result.status is RunStatus.failed
    assert sum(call.startswith("jira.post_comment:") for call in harness.calls) == 1
    assert not any(call.startswith("jira.add_label:") for call in harness.calls)

    reopened = StateStore(harness.store.db_path)
    await reopened.initialize()
    actions = await reopened.list_jira_actions(result.run_id)
    assert len(actions) == 1
    assert actions[0]["operation"] == "post_comment"
    assert actions[0]["state"] == "pending"
    assert actions[0]["attempts"] == 1
    assert actions[0]["check_result"] == "unknown"

    steps = await reopened.list_steps(result.run_id)
    post_step = steps[-1]
    assert post_step["name"] == "post_diagnosis"
    assert post_step["status"] == "failed"
    assert post_step["detail"] == "Publishing the diagnosis result"
    assert post_step["error"] == error_type

    persisted = await reopened.list_events(result.run_id)
    event_types = [event["type"] for event in persisted]
    assert "step.failed" in event_types
    assert "run.failed" in event_types
    assert "run.completed" not in event_types
    assert persisted[-1]["payload"]["summary"]["reason"] == "pipeline_error"

    stream = EventBus(reopened).subscribe(result.run_id)
    replayed = [await anext(stream) for _event in persisted]
    await stream.aclose()
    action_events = [
        event for event in replayed if event.type == "jira.action.updated"
    ]
    assert [event.payload["state"] for event in action_events] == [
        "pending",
        "pending",
    ]
    assert [event.payload["attempts"] for event in action_events] == [0, 1]
    assert all(
        set(event.payload)
        == {
            "action_id",
            "operation",
            "state",
            "check_result",
            "attempts",
            "created_at",
            "updated_at",
        }
        for event in action_events
    )
    serialized = json.dumps(
        {"actions": actions, "steps": steps, "events": persisted}
    )
    assert str(error) not in serialized


@pytest.mark.asyncio
async def test_jira_publication_errors_are_redacted_from_rows_events_and_step_detail(
    tmp_path: Path,
) -> None:
    secret = (
        "pat-secret https://user:password@jira.example.test body-secret raw-response"
    )
    request = httpx.Request(
        "POST",
        "https://jira.example.test/rest/api/2/issue/TESTAUTOMA-8055/comment",
    )
    harness = await _harness(
        tmp_path,
        comment_error=httpx.WriteError(secret, request=request),
    )

    result = await harness.pipeline.execute(harness.run)

    actions = await harness.store.list_jira_actions(result.run_id)
    events = await harness.store.list_events(result.run_id)
    post_step = (await harness.store.list_steps(result.run_id))[-1]
    serialized = json.dumps(
        {"actions": actions, "events": events, "detail": post_step["detail"]}
    )
    for forbidden in (
        "pat-secret",
        "user:password",
        "body-secret",
        "raw-response",
    ):
        assert forbidden not in serialized
    assert [action["state"] for action in actions] == ["uncertain", "succeeded"]
    assert sum(call.startswith("jira.post_comment:") for call in harness.calls) == 1
    assert sum(call.startswith("jira.add_label:") for call in harness.calls) == 1
    assert result.status is RunStatus.completed


@pytest.mark.asyncio
async def test_explicit_runid_skips_extractor_and_uses_deterministic_ticket_fields(
    tmp_path: Path,
) -> None:
    harness = await _harness(tmp_path, extractor_must_be_skipped=True)

    result = await harness.pipeline.execute(harness.run, runid_override=" 40200 ")

    assert result.status is RunStatus.completed
    assert "extractor.extract" not in harness.calls
    assert "evidence.log_by_runid:40200" in harness.calls
    assert harness.matcher.title == "Ticket field summary"
    assert harness.matcher.description == "Ticket field description"
    assert result.ticket_data is not None
    assert result.ticket_data["jarvis_metadata"] == {
        "runid": "40200",
        "title": "Ticket field summary",
        "description": "Ticket field description",
        "test_script_name": "",
    }


@pytest.mark.asyncio
async def test_missing_runid_fails_gracefully_and_preserves_step_detail(
    tmp_path: Path,
) -> None:
    harness = await _harness(tmp_path, runid="  ")

    result = await harness.pipeline.execute(harness.run)

    assert result.status is RunStatus.failed
    assert harness.calls == ["jira.get_ticket:TESTAUTOMA-8055", "extractor.extract"]
    assert result.steps[0].detail == "Reading Jira ticket TESTAUTOMA-8055"
    steps = await harness.store.list_steps(result.run_id)
    assert len(steps) == 1
    assert steps[0]["status"] == "failed"
    assert steps[0]["detail"] == "Reading Jira ticket TESTAUTOMA-8055"
    assert steps[0]["error"] == "missing_runid"
    events = await harness.store.list_events(result.run_id)
    assert [event["type"] for event in events] == [
        "step.started",
        "agent.message",
        "step.failed",
        "agent.message",
        "run.failed",
    ]
    assert events[-2]["payload"] == {
        "text": "No DAI run ID was found. Re-run with runid=NNN."
    }
    assert events[2]["payload"]["detail"] == "Reading Jira ticket TESTAUTOMA-8055"
    assert events[-1]["payload"]["summary"]["reason"] == "missing_runid"
    persisted = await harness.store.get_run(result.run_id)
    assert persisted is not None
    assert persisted["status"] == "failed"
    assert persisted["completed_at"] == result.completed_at.isoformat()


@pytest.mark.asyncio
async def test_pipeline_continues_without_prior_screenshot(tmp_path: Path) -> None:
    harness = await _harness(tmp_path, screenshot=False)

    result = await harness.pipeline.execute(harness.run)

    assert result.status is RunStatus.completed
    assert result.screenshots == []
    assert not any(call.startswith("evidence.fetch_screenshot") for call in harness.calls)
    assert "diagnoser.diagnose" in harness.calls


@pytest.mark.asyncio
async def test_jira_write_gate_blocks_formatter_comment_and_label(tmp_path: Path) -> None:
    harness = await _harness(tmp_path, jira_writes_enabled=False)

    result = await harness.pipeline.execute(harness.run)

    assert result.status is RunStatus.completed
    assert not any(call.startswith("formatter") for call in harness.calls)
    assert not any(call.startswith("jira.post_comment") for call in harness.calls)
    assert not any(call.startswith("jira.add_label") for call in harness.calls)
    post_step = (await harness.store.list_steps(result.run_id))[-1]
    assert post_step["name"] == "post_diagnosis"
    assert post_step["status"] == "completed"
    assert post_step["detail"] == "Jira writes disabled"


@pytest.mark.asyncio
async def test_budget_exceeded_is_safe_terminal_failure(tmp_path: Path) -> None:
    secret = "https://user:secret@unsafe.example/model"
    harness = await _harness(
        tmp_path,
        diagnoser_error=BudgetExceeded(secret),
    )

    result = await harness.pipeline.execute(harness.run)

    assert result.status is RunStatus.failed
    assert "formatter:TESTAUTOMA-8055" not in harness.calls
    assert not any(call.startswith("jira.post_comment") for call in harness.calls)
    analyze_step = (await harness.store.list_steps(result.run_id))[-1]
    assert analyze_step["name"] == "analyze"
    assert analyze_step["detail"] == "Analyzing the failure evidence"
    assert analyze_step["error"] == "budget_exceeded"
    events = await harness.store.list_events(result.run_id)
    assert events[-2]["payload"] == {
        "text": "Run stopped because its model budget was exhausted."
    }
    assert events[-1]["type"] == "run.failed"
    assert events[-1]["payload"]["summary"]["reason"] == "budget_exceeded"
    assert secret not in json.dumps(events)


@pytest.mark.asyncio
async def test_unexpected_exception_is_redacted_and_preserves_prior_artifacts(
    tmp_path: Path,
) -> None:
    secret = "https://token:credential@unsafe.example/path"
    harness = await _harness(
        tmp_path,
        localizer_error=RuntimeError(secret),
    )

    result = await harness.pipeline.execute(harness.run)

    assert result.status is RunStatus.failed
    assert result.logs is not None
    assert len(result.logs) == 3
    assert len(result.screenshots) == 1
    assert Path(result.screenshots[0]).exists()
    assert "diagnoser.diagnose" not in harness.calls
    failed_step = (await harness.store.list_steps(result.run_id))[-1]
    assert failed_step["name"] == "localize"
    assert failed_step["error"] == "RuntimeError"
    events = await harness.store.list_events(result.run_id)
    assert events[-1]["payload"]["summary"]["reason"] == "pipeline_error"
    assert secret not in json.dumps(events)
    persisted = await harness.store.get_run(result.run_id)
    assert persisted is not None
    assert persisted["status"] == "failed"


@pytest.mark.asyncio
async def test_invalid_error_match_index_fails_without_guessing(tmp_path: Path) -> None:
    harness = await _harness(tmp_path, match_index=99)

    result = await harness.pipeline.execute(harness.run)

    assert result.status is RunStatus.failed
    assert result.logs is not None
    assert result.screenshots == []
    assert "evidence.walk_back:99" not in harness.calls
    assert "localizer.localize" not in harness.calls
    assert "diagnoser.diagnose" not in harness.calls
    failed_step = (await harness.store.list_steps(result.run_id))[-1]
    assert failed_step["name"] == "fetch_logs"
    assert failed_step["error"] == "IndexError"


@pytest.mark.asyncio
async def test_cancelled_error_propagates_without_run_failed_event(tmp_path: Path) -> None:
    harness = await _harness(
        tmp_path,
        diagnoser_error=asyncio.CancelledError(),
    )

    with pytest.raises(asyncio.CancelledError):
        await harness.pipeline.execute(harness.run)

    events = await harness.store.list_events(harness.run.run_id)
    assert not any(event["type"] == "run.failed" for event in events)
    assert "formatter:TESTAUTOMA-8055" not in harness.calls
