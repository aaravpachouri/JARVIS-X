from types import SimpleNamespace

from backend.legacy_action_policy import find_legacy_blocked_actions


def action(name):
    return SimpleNamespace(action=SimpleNamespace(name=name), parameters={})


def test_legacy_execution_blocks_shell_python_and_destructive_actions():
    actions = [
        action("RUN_COMMAND"),
        action("RUN_PYTHON"),
        action("DELETE_FILE"),
        action("SHUTDOWN"),
    ]

    assert find_legacy_blocked_actions(actions) == [
        "DELETE_FILE",
        "RUN_COMMAND",
        "RUN_PYTHON",
        "SHUTDOWN",
    ]


def test_legacy_execution_allows_non_sensitive_actions():
    actions = [action("OPEN_URL"), action("SEARCH_WEB")]

    assert find_legacy_blocked_actions(actions) == []
