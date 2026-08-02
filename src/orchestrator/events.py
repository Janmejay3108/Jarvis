from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from src.orchestrator.state_store import StateStore


@dataclass(frozen=True, slots=True)
class EventEnvelope:
	event_id: str
	run_id: str
	ts: str
	type: str
	payload: dict[str, Any]
	cost_usd_so_far: float


def _to_envelope(event: dict[str, Any]) -> EventEnvelope:
	return EventEnvelope(
		event_id=str(event["event_id"]),
		run_id=str(event["run_id"]),
		ts=str(event["ts"]),
		type=str(event["type"]),
		payload=dict(event["payload"]),
		cost_usd_so_far=float(event["cost_usd_so_far"]),
	)


class EventBus:
	def __init__(self, store: StateStore) -> None:
		self._store = store
		self._subscribers: dict[
			str,
			set[asyncio.Queue[EventEnvelope]],
		] = {}
		self._lock = asyncio.Lock()

	async def publish(
		self,
		run_id: str,
		event_type: str,
		payload: dict[str, Any],
		cost_usd_so_far: float = 0.0,
	) -> EventEnvelope:
		"""Persist an event and fan it out to this run's subscribers."""
		async with self._lock:
			event_id = await self._store.append_event(
				run_id,
				event_type,
				payload,
				cost_usd_so_far,
			)
			persisted = await self._store.get_event(event_id)
			if persisted is None:
				raise RuntimeError(f"Persisted event {event_id} could not be read back")
			envelope = _to_envelope(persisted)
			for queue in tuple(self._subscribers.get(run_id, ())):
				queue.put_nowait(envelope)
			return envelope

	async def subscribe(self, run_id: str) -> AsyncIterator[EventEnvelope]:
		"""Replay persisted events, then yield new events for this run."""
		queue: asyncio.Queue[EventEnvelope] = asyncio.Queue()
		async with self._lock:
			replay = await self._store.list_events(run_id)
			self._subscribers.setdefault(run_id, set()).add(queue)

		try:
			for event in replay:
				yield _to_envelope(event)
			while True:
				yield await queue.get()
		finally:
			async with self._lock:
				subscribers = self._subscribers.get(run_id)
				if subscribers is not None:
					subscribers.discard(queue)
					if not subscribers:
						del self._subscribers[run_id]

	def subscriber_count(self, run_id: str) -> int:
		"""Return the number of active subscribers for a run."""
		return len(self._subscribers.get(run_id, ()))
