class ConsecutiveFailureGuard:
    """Stops retry loops after repeated consecutive local-AI failures."""

    def __init__(self, limit: int = 3):
        limit = int(limit)
        if limit < 1:
            raise ValueError("Failure limit must be at least 1.")
        self.limit = limit
        self.consecutive_failures = 0

    def reset(self) -> None:
        self.consecutive_failures = 0

    def record_success(self) -> None:
        """A successful model response breaks the failure streak."""
        self.reset()

    def record_failure(self, error) -> str | None:
        """Record one failure; return a terminal message at the limit."""
        self.consecutive_failures += 1
        if self.consecutive_failures < self.limit:
            return None

        detail = str(error or "").strip() or "Unknown local AI error."
        if len(detail) > 240:
            detail = detail[:237] + "..."

        return (
            "JARVIS stopped computer automation after "
            f"{self.consecutive_failures} consecutive local AI failures. "
            f"Last error: {detail}"
        )
