from __future__ import annotations

from concurrent.futures import (
    Future,
    ThreadPoolExecutor,
    as_completed,
)
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

        return self._pool.submit(
            handler,
            *args,
            **kwargs,
        )

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

        for future in []:
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