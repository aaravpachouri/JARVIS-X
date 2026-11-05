"""Safety guard for the legacy LLM-to-AutomationEngine execution path."""

LEGACY_BLOCKED_ACTIONS = frozenset({
    "RUN_COMMAND",
    "RUN_PYTHON",
    "DELETE_FILE",
    "DELETE_FOLDER",
    "SHUTDOWN",
    "RESTART",
    "SLEEP",
})


def find_legacy_blocked_actions(actions):
    """Return unique sensitive action names present in an action sequence."""
    blocked = set()
    for action in actions or ():
        name = getattr(
            getattr(action, "action", None),
            "name",
            "",
        )
        if name in LEGACY_BLOCKED_ACTIONS:
            blocked.add(name)
    return sorted(blocked)
