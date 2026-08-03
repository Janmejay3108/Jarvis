from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

JiraActionState = Literal[
    "pending",
    "succeeded",
    "failed",
    "uncertain",
    "reconciled",
]
JiraCheckResult = Literal["present", "absent", "unknown"]

JIRA_ACTION_STATES: frozenset[str] = frozenset(
    {"pending", "succeeded", "failed", "uncertain", "reconciled"}
)
JIRA_CHECK_RESULTS: frozenset[str] = frozenset({"present", "absent", "unknown"})

_EVENT_FIELDS = (
    "action_id",
    "operation",
    "state",
    "check_result",
    "attempts",
    "created_at",
    "updated_at",
)


def jira_action_event_payload(action: Mapping[str, Any]) -> dict[str, Any]:
    return {field: action[field] for field in _EVENT_FIELDS}


def append_jira_action_footer(body: str, action_id: str) -> str:
    return f"{body}\n\n[JARVIS action_id={action_id}]"