class ActionTypeStub:
    def __init__(self, name):
        self.name = name


from backend.agent_policy import AgentPolicy


class FakeEngine:
    routes = {
        ActionTypeStub("RUN_COMMAND"): object(),
        ActionTypeStub("RUN_PYTHON"): object(),
        ActionTypeStub("OPEN_URL"): object(),
        ActionTypeStub("DELETE_FILE"): object(),
    }


def test_autonomous_policy_blocks_arbitrary_shell_and_python_execution():
    policy = AgentPolicy(FakeEngine())

    for action in ("RUN_COMMAND", "RUN_PYTHON"):
        allowed, reason = policy.validate(action, {"command": "echo unsafe"})

        assert allowed is False
        assert "confirmation" in reason


def test_policy_keeps_ordinary_supported_actions_available():
    policy = AgentPolicy(FakeEngine())

    allowed, reason = policy.validate("OPEN_URL", {"url": "https://example.com"})

    assert allowed is True
    assert reason == "ok"


def test_policy_continues_to_block_destructive_filesystem_actions():
    policy = AgentPolicy(FakeEngine())

    for action in ("DELETE_FILE", "DELETE_FOLDER"):
        allowed, reason = policy.validate(action, {"path": "example.txt"})

        assert allowed is False
        assert "confirmation" in reason
