from __future__ import annotations

from src.orchestrator.jira_actions import (
    append_jira_action_footer,
    jira_action_event_payload,
)


def test_jira_action_event_payload_is_exact_allowlist() -> None:
    action = {
        "action_id": "action-1",
        "run_id": "run-1",
        "ticket_key": "TESTAUTOMA-8055",
        "operation": "post_comment",
        "state": "uncertain",
        "check_result": "unknown",
        "attempts": 1,
        "created_at": "2026-08-03T12:00:00+00:00",
        "updated_at": "2026-08-03T12:00:01+00:00",
        "intent": {"body": "secret body"},
        "url": "https://user:secret@example.test/jira",
        "response": "raw response",
        "pat": "secret-token",
    }

    assert jira_action_event_payload(action) == {
        "action_id": "action-1",
        "operation": "post_comment",
        "state": "uncertain",
        "check_result": "unknown",
        "attempts": 1,
        "created_at": "2026-08-03T12:00:00+00:00",
        "updated_at": "2026-08-03T12:00:01+00:00",
    }


def test_append_jira_action_footer_preserves_body_and_uses_stable_marker() -> None:
    body = "Diagnosis line 1\nDiagnosis line 2"

    assert append_jira_action_footer(body, "action-1") == (
        "Diagnosis line 1\nDiagnosis line 2\n\n[JARVIS action_id=action-1]"
    )