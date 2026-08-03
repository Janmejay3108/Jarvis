from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiosqlite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
	id TEXT PRIMARY KEY,
	title TEXT,
	created_at TEXT,
	updated_at TEXT
);
CREATE TABLE IF NOT EXISTS messages (
	id TEXT PRIMARY KEY,
	conversation_id TEXT,
	role TEXT,
	content TEXT,
	run_id TEXT NULL,
	ts TEXT
);
CREATE TABLE IF NOT EXISTS runs (
	run_id TEXT PRIMARY KEY,
	ticket_key TEXT,
	track_id TEXT,
	mode TEXT,
	status TEXT,
	conversation_id TEXT,
	created_at TEXT,
	completed_at TEXT,
	tokens_in INTEGER DEFAULT 0,
	tokens_out INTEGER DEFAULT 0,
	cost_usd REAL DEFAULT 0.0,
	summary_json TEXT
);
CREATE TABLE IF NOT EXISTS run_steps (
	id TEXT PRIMARY KEY,
	run_id TEXT,
	name TEXT,
	status TEXT,
	started_at TEXT,
	completed_at TEXT,
	detail TEXT,
	error TEXT
);
CREATE TABLE IF NOT EXISTS events (
	event_id TEXT PRIMARY KEY,
	run_id TEXT,
	ts TEXT,
	type TEXT,
	payload_json TEXT
);
CREATE TABLE IF NOT EXISTS approvals (
	id TEXT PRIMARY KEY,
	run_id TEXT,
	requested_at TEXT,
	resolved_at TEXT,
	decision TEXT,
	comment TEXT,
	payload_json TEXT
);
"""

_RUN_UPDATE_FIELDS = {
	"ticket_key",
	"track_id",
	"mode",
	"status",
	"conversation_id",
	"completed_at",
	"tokens_in",
	"tokens_out",
	"cost_usd",
	"summary_json",
}


def _now() -> str:
	return datetime.now(UTC).isoformat()


def _id() -> str:
	return uuid4().hex


def _as_dict(row: aiosqlite.Row | None) -> dict[str, Any] | None:
	return dict(row) if row is not None else None


class StateStore:
	def __init__(self, db_path: str = "data/agent.db") -> None:
		self.db_path = db_path

	async def initialize(self) -> None:
		"""Create the persistent schema if it does not exist."""
		if self.db_path != ":memory:":
			Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
		async with aiosqlite.connect(self.db_path) as db:
			await db.executescript(_SCHEMA)
			await db.commit()

	async def create_conversation(self, title: str = "") -> str:
		conversation_id = _id()
		timestamp = _now()
		async with aiosqlite.connect(self.db_path) as db:
			await db.execute(
				"INSERT INTO conversations VALUES (?, ?, ?, ?)",
				(conversation_id, title, timestamp, timestamp),
			)
			await db.commit()
		return conversation_id

	async def get_conversation(
		self,
		conversation_id: str,
	) -> dict[str, Any] | None:
		async with aiosqlite.connect(self.db_path) as db:
			db.row_factory = aiosqlite.Row
			cursor = await db.execute(
				"SELECT * FROM conversations WHERE id = ?",
				(conversation_id,),
			)
			return _as_dict(await cursor.fetchone())

	async def list_conversations(self) -> list[dict[str, Any]]:
		async with aiosqlite.connect(self.db_path) as db:
			db.row_factory = aiosqlite.Row
			cursor = await db.execute(
				"SELECT * FROM conversations ORDER BY updated_at DESC, rowid DESC"
			)
			return [dict(row) for row in await cursor.fetchall()]

	async def save_message(
		self,
		conversation_id: str,
		role: str,
		content: str,
		run_id: str | None = None,
	) -> str:
		message_id = _id()
		timestamp = _now()
		async with aiosqlite.connect(self.db_path) as db:
			await db.execute(
				"INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
				(message_id, conversation_id, role, content, run_id, timestamp),
			)
			await db.execute(
				"UPDATE conversations SET updated_at = ? WHERE id = ?",
				(timestamp, conversation_id),
			)
			await db.commit()
		return message_id

	async def list_messages(self, conversation_id: str) -> list[dict[str, Any]]:
		async with aiosqlite.connect(self.db_path) as db:
			db.row_factory = aiosqlite.Row
			cursor = await db.execute(
				"SELECT * FROM messages WHERE conversation_id = ? ORDER BY rowid",
				(conversation_id,),
			)
			return [dict(row) for row in await cursor.fetchall()]

	async def create_run(
		self,
		ticket_key: str,
		track_id: str,
		mode: str,
		conversation_id: str | None,
		*,
		run_id: str | None = None,
		status: str = "queued",
		created_at: str | None = None,
	) -> str:
		stored_run_id = run_id if run_id is not None else _id()
		stored_created_at = created_at if created_at is not None else _now()
		async with aiosqlite.connect(self.db_path) as db:
			await db.execute(
				"""
				INSERT INTO runs (
					run_id, ticket_key, track_id, mode, status,
					conversation_id, created_at, completed_at,
					tokens_in, tokens_out, cost_usd, summary_json
				) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 0, 0, 0.0, ?)
				""",
				(
					stored_run_id,
					ticket_key,
					track_id,
					mode,
					status,
					conversation_id,
					stored_created_at,
					"{}",
				),
			)
			await db.commit()
		return stored_run_id

	async def update_run(self, run_id: str, **fields: Any) -> None:
		if not fields:
			return
		unknown = set(fields) - _RUN_UPDATE_FIELDS
		if unknown:
			names = ", ".join(sorted(unknown))
			raise ValueError(f"Unsupported run fields: {names}")
		if isinstance(fields.get("summary_json"), Mapping):
			fields["summary_json"] = json.dumps(fields["summary_json"])
		assignments = ", ".join(f"{name} = ?" for name in fields)
		async with aiosqlite.connect(self.db_path) as db:
			await db.execute(
				f"UPDATE runs SET {assignments} WHERE run_id = ?",
				(*fields.values(), run_id),
			)
			await db.commit()

	async def get_run(self, run_id: str) -> dict[str, Any] | None:
		async with aiosqlite.connect(self.db_path) as db:
			db.row_factory = aiosqlite.Row
			cursor = await db.execute(
				"SELECT * FROM runs WHERE run_id = ?",
				(run_id,),
			)
			return _as_dict(await cursor.fetchone())

	async def append_step(
		self,
		run_id: str,
		name: str,
		status: str = "started",
		detail: str = "",
		*,
		started_at: str | None = None,
	) -> str:
		step_id = _id()
		stored_started_at = started_at if started_at is not None else _now()
		async with aiosqlite.connect(self.db_path) as db:
			await db.execute(
				"INSERT INTO run_steps VALUES (?, ?, ?, ?, ?, NULL, ?, ?)",
				(step_id, run_id, name, status, stored_started_at, detail, ""),
			)
			await db.commit()
		return step_id

	async def complete_step(
		self,
		step_id: str,
		status: str = "completed",
		error: str = "",
		*,
		completed_at: str | None = None,
		detail: str | None = None,
	) -> None:
		assignments = ["status = ?", "completed_at = ?", "error = ?"]
		values = [
			status,
			completed_at if completed_at is not None else _now(),
			error,
		]
		if detail is not None:
			assignments.append("detail = ?")
			values.append(detail)
		async with aiosqlite.connect(self.db_path) as db:
			await db.execute(
				f"UPDATE run_steps SET {', '.join(assignments)} WHERE id = ?",
				(*values, step_id),
			)
			await db.commit()

	async def list_steps(self, run_id: str) -> list[dict[str, Any]]:
		async with aiosqlite.connect(self.db_path) as db:
			db.row_factory = aiosqlite.Row
			cursor = await db.execute(
				"SELECT * FROM run_steps WHERE run_id = ? ORDER BY rowid",
				(run_id,),
			)
			return [dict(row) for row in await cursor.fetchall()]

	async def append_event(
		self,
		run_id: str,
		event_type: str,
		payload: dict[str, Any],
		cost_usd_so_far: float = 0.0,
	) -> str:
		event_id = _id()
		stored_payload = {
			"payload": payload,
			"cost_usd_so_far": cost_usd_so_far,
		}
		async with aiosqlite.connect(self.db_path) as db:
			await db.execute(
				"INSERT INTO events VALUES (?, ?, ?, ?, ?)",
				(event_id, run_id, _now(), event_type, json.dumps(stored_payload)),
			)
			await db.commit()
		return event_id

	async def list_events(
		self,
		run_id: str,
		after: str | None = None,
	) -> list[dict[str, Any]]:
		parameters: tuple[str, ...]
		if after is None:
			query = "SELECT * FROM events WHERE run_id = ? ORDER BY rowid"
			parameters = (run_id,)
		else:
			query = """
				SELECT * FROM events
				WHERE run_id = ?
				  AND rowid > (
					  SELECT rowid FROM events
					  WHERE event_id = ? AND run_id = ?
				  )
				ORDER BY rowid
			"""
			parameters = (run_id, after, run_id)
		async with aiosqlite.connect(self.db_path) as db:
			db.row_factory = aiosqlite.Row
			cursor = await db.execute(query, parameters)
			rows = await cursor.fetchall()

		events = []
		for row in rows:
			event = dict(row)
			stored_payload = json.loads(event.pop("payload_json"))
			event["payload"] = stored_payload["payload"]
			event["cost_usd_so_far"] = stored_payload["cost_usd_so_far"]
			events.append(event)
		return events

	async def get_event(self, event_id: str) -> dict[str, Any] | None:
		async with aiosqlite.connect(self.db_path) as db:
			db.row_factory = aiosqlite.Row
			cursor = await db.execute(
				"SELECT * FROM events WHERE event_id = ?",
				(event_id,),
			)
			event = _as_dict(await cursor.fetchone())
		if event is not None:
			stored_payload = json.loads(event.pop("payload_json"))
			event["payload"] = stored_payload["payload"]
			event["cost_usd_so_far"] = stored_payload["cost_usd_so_far"]
		return event

	async def request_approval(self, run_id: str, payload: dict[str, Any]) -> str:
		approval_id = _id()
		async with aiosqlite.connect(self.db_path) as db:
			await db.execute(
				"INSERT INTO approvals VALUES (?, ?, ?, NULL, NULL, ?, ?)",
				(approval_id, run_id, _now(), "", json.dumps(payload)),
			)
			await db.commit()
		return approval_id

	async def resolve_approval(
		self,
		approval_id: str,
		decision: str,
		comment: str = "",
	) -> None:
		async with aiosqlite.connect(self.db_path) as db:
			await db.execute(
				"""
				UPDATE approvals
				SET resolved_at = ?, decision = ?, comment = ?
				WHERE id = ?
				""",
				(_now(), decision, comment, approval_id),
			)
			await db.commit()

	async def get_approval(self, approval_id: str) -> dict[str, Any] | None:
		async with aiosqlite.connect(self.db_path) as db:
			db.row_factory = aiosqlite.Row
			cursor = await db.execute(
				"SELECT * FROM approvals WHERE id = ?",
				(approval_id,),
			)
			approval = _as_dict(await cursor.fetchone())
		if approval is not None:
			approval["payload"] = json.loads(approval.pop("payload_json"))
		return approval
