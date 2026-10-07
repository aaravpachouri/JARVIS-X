from __future__ import annotations

import time
from typing import Any, Optional


class VoiceComputerSyncHealthGuard:

    """
    Final runtime guard for Phase 8.7.

    It detects synchronization inconsistencies before they leak into
    the rest of JARVIS.

    It does not repair controllers directly; it reports whether the
    synchronization layer is healthy and what corrective transition
    is recommended.
    """

    MAX_IDLE_TASK_AGE = 60.0
    MAX_INTERRUPTION_AGE = 15.0

    def __init__(
        self,
        coordinator,
        *,
        max_idle_task_age: float = MAX_IDLE_TASK_AGE,
        max_interruption_age: float = MAX_INTERRUPTION_AGE,
    ):

        self.coordinator = coordinator

        self.max_idle_task_age = max(
            1.0,
            float(
                max_idle_task_age
            ),
        )

        self.max_interruption_age = max(
            1.0,
            float(
                max_interruption_age
            ),
        )

    ############################################################
    # HEALTH CHECK
    ############################################################

    def check(
        self,
    ) -> dict[str, Any]:

        snapshot = self.coordinator.snapshot()

        sync = snapshot.get(
            "sync",
            {}
        )

        priority = snapshot.get(
            "priority",
            {}
        )

        tts = snapshot.get(
            "tts",
            {}
        )

        recovery = snapshot.get(
            "recovery",
            {}
        )

        issues = []

        state = str(
            sync.get(
                "state",
                ""
            )
            or
            ""
        )

        task_id = int(
            sync.get(
                "active_task_id",
                0
            )
            or
            0
        )

        interrupt_requested = bool(
            sync.get(
                "interrupt_requested",
                False
            )
        )

        ########################################################
        # Active-task consistency.
        ########################################################

        current_lease = priority.get(
            "current"
        )

        if (
            task_id
            and
            not current_lease
        ):

            issues.append(
                "Active synchronization task has no priority lease."
            )

        if (
            current_lease
            and
            not task_id
        ):

            issues.append(
                "Priority lease exists without an active synchronization task."
            )

        ########################################################
        # Interruption consistency.
        ########################################################

        if interrupt_requested:

            requested_at = (
                recovery.get(
                    "requested_at"
                )
            )

            if requested_at:

                age = max(
                    0.0,
                    time.monotonic()
                    -
                    float(
                        requested_at
                    ),
                )

                if age > self.max_interruption_age:

                    issues.append(
                        "Interruption request has not been cleared."
                    )

        ########################################################
        # TTS consistency.
        ########################################################

        if (
            state
            in {
                "COMPUTER_ACTIVE",
                "CANCELLING",
                "INTERRUPTING",
            }
            and
            tts.get(
                "speaking",
                False
            )
        ):

            issues.append(
                "TTS is speaking while computer/interruption state is active."
            )

        ########################################################
        # Recovery consistency.
        ########################################################

        attempts = int(
            recovery.get(
                "attempts",
                0
            )
            or
            0
        )

        if attempts >= 3:

            issues.append(
                "Synchronization recovery limit has been reached."
            )

        healthy = not issues

        return {
            "healthy":
                healthy,

            "issues":
                issues,

            "state":
                state,

            "active_task_id":
                task_id,

            "recommended_action":
                (
                    "CONTINUE"
                    if healthy
                    else
                    self._recommend(
                        state,
                        interrupt_requested,
                        issues,
                    )
                ),
        }

    ############################################################
    # RECOMMENDATION
    ############################################################

    @staticmethod
    def _recommend(
        state: str,
        interrupt_requested: bool,
        issues,
    ) -> str:

        if interrupt_requested:

            return "CLEAR_OR_COMPLETE_INTERRUPTION"

        if any(
            "TTS is speaking"
            in issue
            for issue in issues
        ):

            return "CANCEL_STALE_TTS"

        if any(
            "lease"
            in issue.lower()
            for issue in issues
        ):

            return "RECONCILE_TASK_OWNERSHIP"

        if any(
            "recovery"
            in issue.lower()
            for issue in issues
        ):

            return "STOP_AND_REINITIALIZE_SYNC"

        return "REFRESH_SYNC_STATE"

    ############################################################
    # SNAPSHOT
    ############################################################

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return self.check()