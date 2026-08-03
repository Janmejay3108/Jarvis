from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from filelock import AsyncFileLock

_TRACK_ID = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


class TrackLockManager:
    def __init__(
        self,
        lock_root: Path = Path("data/locks"),
        *,
        timeout: float = -1,
    ) -> None:
        self._lock_root = lock_root
        self._lock_root.mkdir(parents=True, exist_ok=True)
        self._timeout = timeout
        self._async_locks: dict[str, asyncio.Lock] = {}
        self._file_locks: dict[str, AsyncFileLock] = {}

    @staticmethod
    def _canonical_track_id(track_id: str) -> str:
        canonical = track_id.strip().lower()
        if not _TRACK_ID.fullmatch(canonical):
            raise ValueError(f"Invalid track ID: {track_id!r}")
        return canonical

    def _locks_for(self, track_id: str) -> tuple[asyncio.Lock, AsyncFileLock]:
        canonical = self._canonical_track_id(track_id)
        process_lock = self._async_locks.setdefault(canonical, asyncio.Lock())
        file_lock = self._file_locks.get(canonical)
        if file_lock is None:
            file_lock = AsyncFileLock(
                self._lock_root / f"{canonical}.lock",
                timeout=self._timeout,
                run_in_executor=True,
                fallback_to_soft=False,
                preserve_lock_file=True,
            )
            self._file_locks[canonical] = file_lock
        return process_lock, file_lock

    @staticmethod
    async def _release_file_lock(file_lock: AsyncFileLock) -> None:
        release_task = asyncio.create_task(file_lock.release(force=True))
        try:
            await asyncio.shield(release_task)
        except asyncio.CancelledError:
            await release_task
            raise

    @asynccontextmanager
    async def hold(self, track_id: str) -> AsyncIterator[None]:
        process_lock, file_lock = self._locks_for(track_id)
        async with process_lock:
            acquired = False
            try:
                await file_lock.acquire()
                acquired = True
                yield
            except asyncio.CancelledError:
                if file_lock.is_locked:
                    await self._release_file_lock(file_lock)
                    acquired = False
                raise
            finally:
                if acquired:
                    await self._release_file_lock(file_lock)
