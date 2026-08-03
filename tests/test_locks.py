from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
from filelock import AsyncFileLock

from src.orchestrator.locks import TrackLockManager


@pytest.mark.asyncio
async def test_same_track_serializes_coroutines(tmp_path: Path) -> None:
    manager = TrackLockManager(tmp_path)
    first_entered = asyncio.Event()
    release_first = asyncio.Event()
    second_entered = asyncio.Event()
    active = 0
    maximum_active = 0

    async def owner(
        track_id: str, entered: asyncio.Event, release: asyncio.Event
    ) -> None:
        nonlocal active, maximum_active
        async with manager.hold(track_id):
            active += 1
            maximum_active = max(maximum_active, active)
            entered.set()
            await release.wait()
            active -= 1

    first = asyncio.create_task(owner(" Enovia ", first_entered, release_first))
    await first_entered.wait()
    release_second = asyncio.Event()
    second = asyncio.create_task(owner("enovia", second_entered, release_second))
    await asyncio.sleep(0)
    assert not second_entered.is_set()
    release_first.set()
    await second_entered.wait()
    release_second.set()
    await asyncio.gather(first, second)
    assert maximum_active == 1


@pytest.mark.asyncio
async def test_different_tracks_do_not_block_each_other(tmp_path: Path) -> None:
    manager = TrackLockManager(tmp_path)
    release_first = asyncio.Event()
    first_entered = asyncio.Event()
    second_entered = asyncio.Event()

    async def hold_first() -> None:
        async with manager.hold("enovia"):
            first_entered.set()
            await release_first.wait()

    first = asyncio.create_task(hold_first())
    await first_entered.wait()
    async with manager.hold("oracle"):
        second_entered.set()
    assert second_entered.is_set()
    release_first.set()
    await first


@pytest.mark.asyncio
async def test_cancelled_async_waiter_does_not_block_next_owner(tmp_path: Path) -> None:
    manager = TrackLockManager(tmp_path)
    owner_entered = asyncio.Event()
    release_owner = asyncio.Event()

    async def owner() -> None:
        async with manager.hold("enovia"):
            owner_entered.set()
            await release_owner.wait()

    async def waiter() -> None:
        async with manager.hold("enovia"):
            pass

    owner_task = asyncio.create_task(owner())
    await owner_entered.wait()
    cancelled_waiter = asyncio.create_task(waiter())
    await asyncio.sleep(0)
    cancelled_waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await cancelled_waiter
    release_owner.set()
    await owner_task
    await asyncio.wait_for(waiter(), timeout=2)


@pytest.mark.asyncio
async def test_cancelled_file_waiter_releases_async_layer(tmp_path: Path) -> None:
    lock_path = tmp_path / "enovia.lock"
    external = AsyncFileLock(
        lock_path,
        fallback_to_soft=False,
        preserve_lock_file=True,
    )
    await external.acquire()
    manager = TrackLockManager(tmp_path)
    waiter_started = asyncio.Event()

    async def waiter() -> None:
        waiter_started.set()
        async with manager.hold("enovia"):
            pass

    blocked = asyncio.create_task(waiter())
    await waiter_started.wait()
    await asyncio.sleep(0)
    blocked.cancel()
    with pytest.raises(asyncio.CancelledError):
        await blocked
    await external.release(force=True)
    other_manager = TrackLockManager(tmp_path, timeout=1)
    async with asyncio.timeout(2):
        async with other_manager.hold("enovia"):
            pass


@pytest.mark.asyncio
async def test_body_cancellation_and_exception_release_both_layers(
    tmp_path: Path,
) -> None:
    manager = TrackLockManager(tmp_path)
    entered = asyncio.Event()
    blocker = asyncio.Event()

    async def cancelled_body() -> None:
        async with manager.hold("enovia"):
            entered.set()
            await blocker.wait()

    task = asyncio.create_task(cancelled_body())
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    async with manager.hold("enovia"):
        pass

    with pytest.raises(RuntimeError, match="body failed"):
        async with manager.hold("enovia"):
            raise RuntimeError("body failed")
    async with manager.hold("enovia"):
        pass


async def _run_lock_child(lock_path: Path) -> str:
    code = """
import sys
from filelock import FileLock, Timeout
lock = FileLock(sys.argv[1], timeout=0, fallback_to_soft=False, preserve_lock_file=True)
try:
    with lock:
        print("acquired", flush=True)
except Timeout:
    print("contended", flush=True)
"""
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        code,
        str(lock_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
    except BaseException:
        process.kill()
        await process.wait()
        raise
    assert process.returncode == 0, stderr.decode()
    return stdout.decode().strip()


@pytest.mark.asyncio
async def test_native_file_lock_excludes_another_process_then_releases(
    tmp_path: Path,
) -> None:
    manager = TrackLockManager(tmp_path)
    lock_path = tmp_path / "enovia.lock"
    async with manager.hold("enovia"):
        assert await _run_lock_child(lock_path) == "contended"
    assert await _run_lock_child(lock_path) == "acquired"


@pytest.mark.asyncio
async def test_process_exit_releases_native_lock(tmp_path: Path) -> None:
    lock_path = tmp_path / "enovia.lock"
    code = """
import os
import sys
from filelock import FileLock
lock = FileLock(sys.argv[1], fallback_to_soft=False, preserve_lock_file=True)
lock.acquire()
print("acquired", flush=True)
os._exit(0)
"""
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        code,
        str(lock_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
    except BaseException:
        process.kill()
        await process.wait()
        raise
    assert process.returncode == 0, stderr.decode()
    assert stdout.decode().strip() == "acquired"

    manager = TrackLockManager(tmp_path, timeout=1)

    async def acquire_after_exit() -> None:
        async with manager.hold("enovia"):
            pass

    await asyncio.wait_for(acquire_after_exit(), timeout=2)
