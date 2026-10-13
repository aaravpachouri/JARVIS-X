from __future__ import annotations

from concurrent.futures import (
    Future,
    ThreadPoolExecutor,
    as_completed,
)
from threading import Lock
from typing import Any, Callable, Iterable


############################################################
# ASYNC EXECUTOR
############################################################

class AsyncExecutor:

    """
    Small bounded thread-based executor for independent
    operations.

    This is intentionally isolated from TaskOrchestrator.

    It does not decide whether something is safe to run in
    parallel. ParallelSafetyAnalyzer handles that decision.
    """

    def __init__(
        self,
        max_workers: int = 4,
    ):

        self.max_workers = max(
            1,
            int(
                max_workers
            ),
        )

        self._pool = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="JARVIS"
        )

        self._futures: set[Future] = set()
        self._futures_lock = Lock()

    ########################################################
    # SUBMIT
    ########################################################

    def submit(
        self,
        handler: Callable[..., Any],
        *args,
        **kwargs,
    ) -> Future:

        if not callable(
            handler
        ):

            raise TypeError(
                "handler must be callable."
            )

        future = self._pool.submit(
            handler,
            *args,
            **kwargs,
        )

        with self._futures_lock:
            self._futures.add(future)

        future.add_done_callback(
            self._forget_future
        )

        return future

    def _forget_future(
        self,
        future: Future,
    ) -> None:

        with self._futures_lock:
            self._futures.discard(future)

    ########################################################
    # RUN MANY
    ########################################################

    def run_many(
        self,
        operations: Iterable[
            tuple[
                Callable[..., Any],
                tuple,
                dict,
            ]
        ],
    ) -> list[Any]:

        futures = []

        for handler, args, kwargs in operations:

            futures.append(
                self.submit(
                    handler,
                    *args,
                    **kwargs,
                )
            )

        results = []

        for future in as_completed(
            futures
        ):

            results.append(
                future.result()
            )

        return results

    ########################################################
    # CANCEL
    ########################################################

    def cancel_pending(
        self,
    ) -> None:

        """
        Cancel work that has not started yet.

        Python cannot safely force-stop a running thread; active
        handlers must use their own cooperative cancellation
        mechanism if they need to stop early.
        """

        with self._futures_lock:
            futures = tuple(self._futures)

        for future in futures:
            future.cancel()

    ########################################################
    # SHUTDOWN
    ########################################################

    def shutdown(
        self,
        wait: bool = True,
        cancel_futures: bool = True,
    ) -> None:

        self._pool.shutdown(
            wait=wait,
            cancel_futures=cancel_futures,
        )

    ########################################################
    # CONTEXT MANAGER
    ########################################################

    def __enter__(
        self,
    ):

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        self.shutdown()

        return False

    ########################################################
    # REPRESENTATION
    ########################################################

    def __repr__(
        self,
    ):

        return (
            "<AsyncExecutor "
            f"max_workers={self.max_workers}>"
        )
