import threading


class ComputerAgentBusyError(RuntimeError):
    """Raised when another task currently owns the desktop-control loop."""

    def __init__(self):
        super().__init__(
            "Another computer task is already running, sir. "
            "Wait for it to finish or cancel it before starting another."
        )


class AgentRunGate:
    """Non-blocking process-wide gate for physical computer automation."""

    def __init__(self):
        self._lock = threading.Lock()

    def try_enter(self) -> bool:
        """Return True only when this caller owns the gate."""
        return self._lock.acquire(blocking=False)

    def enter_or_raise(self) -> None:
        """Acquire the gate or raise a clear busy error."""
        if not self.try_enter():
            raise ComputerAgentBusyError()

    def leave(self) -> None:
        """Release a gate acquired by the current task."""
        self._lock.release()


# A desktop should not receive actions from two autonomous loops at once,
# even if separate ComputerUseAgent instances were accidentally created.
GLOBAL_COMPUTER_AGENT_RUN_GATE = AgentRunGate()
