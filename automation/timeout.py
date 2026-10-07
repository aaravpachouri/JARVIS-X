from __future__ import annotations

from concurrent.futures import Future
from dataclasses import dataclass
from time import monotonic
from typing import Any, Callable, Optional


############################################################
# TIMEOUT RESULT
############################################################

@dataclass
class TimeoutResult:

    success: bool = False

    result: Any = None

    timed_out: bool = False

    error: str = ""

    duration: float = 0.0


############################################################
# TIMEOUT MANAGER
############################################################

class TimeoutManager:

    """
    Small timeout utility for JARVIS runtime operations.

    It does not force-kill running threads.

    A timeout means:
        "Stop waiting for this operation and treat it as
         unsuccessful."

    Cooperative cancellation should be handled separately by
    CancellationToken / CancellationContext.
    """

    ########################################################
    # CALL WITH TIMEOUT
    ########################################################

    def run(
        self,
        handler: Callable[..., Any],
        timeout: float,
        *args,
        **kwargs,
    ) -> TimeoutResult:

        if not callable(
            handler
        ):

            raise TypeError(
                "handler must be callable."
            )

        try:

            timeout = max(
                0.01,
                float(
                    timeout
                ),
            )

        except (
            TypeError,
            ValueError,
        ):

            timeout = 10.0

        started = monotonic()

        try:

            result = (
                self._run_with_future(
                    handler,
                    timeout,
                    args,
                    kwargs,
                )
            )

            duration = (
                monotonic()
                -
                started
            )

            return TimeoutResult(
                success=True,
                result=result,
                duration=duration,
            )

        except TimeoutError:

            duration = (
                monotonic()
                -
                started
            )

            return TimeoutResult(
                success=False,
                timed_out=True,
                error=(
                    "Operation timed out."
                ),
                duration=duration,
            )

        except Exception as exc:

            duration = (
                monotonic()
                -
                started
            )

            return TimeoutResult(
                success=False,
                error=str(
                    exc
                ),
                duration=duration,
            )

    ########################################################
    # FUTURE SUPPORT
    ########################################################

    @staticmethod
    def _run_with_future(
        handler: Callable[..., Any],
        timeout: float,
        args: tuple,
        kwargs: dict,
    ) -> Any:

        """
        Use a short-lived executor for isolated operations.

        This is intended for bounded operations, not for
        replacing the main AsyncExecutor.
        """

        from concurrent.futures import (
            ThreadPoolExecutor,
        )

        with ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="JARVIS-TIMEOUT",
        ) as pool:

            future: Future = (
                pool.submit(
                    handler,
                    *args,
                    **kwargs,
                )
            )

            try:

                return future.result(
                    timeout=timeout
                )

            except TimeoutError:

                future.cancel()

                raise

    ########################################################
    # WAIT FOR FUTURE
    ########################################################

    @staticmethod
    def wait(
        future: Future,
        timeout: float,
    ) -> TimeoutResult:

        started = monotonic()

        try:

            result = future.result(
                timeout=max(
                    0.01,
                    float(
                        timeout
                    ),
                )
            )

            return TimeoutResult(
                success=True,
                result=result,
                duration=(
                    monotonic()
                    -
                    started
                ),
            )

        except TimeoutError:

            return TimeoutResult(
                success=False,
                timed_out=True,
                error=(
                    "Operation timed out."
                ),
                duration=(
                    monotonic()
                    -
                    started
                ),
            )

        except Exception as exc:

            return TimeoutResult(
                success=False,
                error=str(
                    exc
                ),
                duration=(
                    monotonic()
                    -
                    started
                ),
            )