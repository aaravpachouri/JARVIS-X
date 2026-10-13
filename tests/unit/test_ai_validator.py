from ai.schema import AIResponse, Action
from ai.tools import TOOLS
from ai.validator import AIValidator


def test_response_defaults_are_independent():
    first = AIResponse()
    second = AIResponse()

    first.actions.append(Action(tool="OPEN_URL"))

    assert len(first.actions) == 1
    assert second.actions == []
    assert first.text is None
    assert first.local is False


def test_validator_preserves_known_actions_and_order():
    response = AIResponse(
        actions=[
            Action(tool="OPEN_URL", parameters={"url": "https://example.com"}),
            Action(tool="SEARCH_WEB", parameters={"query": "python"}),
        ]
    )

    result = AIValidator().validate(response)

    assert result is response
    assert [action.tool for action in result.actions] == [
        "OPEN_URL",
        "SEARCH_WEB",
    ]


def test_validator_removes_unknown_actions(capsys):
    known_tool = TOOLS[0]
    response = AIResponse(
        actions=[
            Action(tool=known_tool),
            Action(tool="UNKNOWN_UNREGISTERED_TOOL"),
        ]
    )

    result = AIValidator().validate(response)

    assert [action.tool for action in result.actions] == [known_tool]
    assert "Unknown tool: UNKNOWN_UNREGISTERED_TOOL" in capsys.readouterr().out


def test_validator_handles_empty_action_list():
    response = AIResponse(actions=[])

    result = AIValidator().validate(response)

    assert result is response
    assert result.actions == []
