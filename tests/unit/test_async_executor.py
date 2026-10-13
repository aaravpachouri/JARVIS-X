from threading import Event

import pytest

from automation.async_executor import AsyncExecutor


def test_submit_tracks_and_completes_future():
    executor = AsyncExecutor(max_workers=1)

    try:
        future = executor.submit(lambda: 42)

        assert future.result(timeout=2) == 42
        assert future.done()
        assert future not in executor._futures
    finally:
        executor.shutdown()


def test_cancel_pending_cancels_queued_work_but_not_running_work():
    executor = AsyncExecutor(max_workers=1)
    started = Event()
    release = Event()

    def blocking_handler():
        started.set()
        if not release.wait(timeout=3):
            raise TimeoutError("test did not release the worker")
        return "finished"

    try:
        running = executor.submit(blocking_handler)
        assert started.wait(timeout=2), "worker did not start"

        queued = executor.submit(lambda: "should not run")
        executor.cancel_pending()

        assert queued.cancelled()
        assert not running.cancelled()

        release.set()
        assert running.result(timeout=2) == "finished"
    finally:
        release.set()
        executor.shutdown()


def test_cancel_pending_is_safe_when_no_work_is_pending():
    executor = AsyncExecutor(max_workers=1)

    try:
        executor.cancel_pending()
        assert executor.submit(lambda: "ok").result(timeout=2) == "ok"
    finally:
        executor.shutdown()


def test_submit_rejects_non_callable_handlers():
    executor = AsyncExecutor()

    try:
        with pytest.raises(TypeError, match="handler must be callable"):
            executor.submit(None)
    finally:
        executor.shutdown()
