"""Integration coverage for the live shell-execution boundary.

These tests drive ComputerUseAgent._execute_tool - the single method that
turns an LLM-proposed tool call into a real AutomationEngine action. They
exist to prove that RUN_COMMAND and RUN_PYTHON are rejected by the policy
gate before TerminalExecutor can be reached.

Unlike tests/unit/test_agent_policy_safety.py, which exercises AgentPolicy
against a hand-written stub route table, these tests build the real
AgentPolicy from the real AutomationEngine route table, so they fail if the
engine ever gains a route that the policy does not block.

The desktop automation stack (pyautogui, pyperclip, mss, ...) is stubbed
before import, the same way tests/unit/test_local_client_context.py stubs
ollama. Nothing here touches a real screen, keyboard, clipboard or shell.
"""

import importlib.util
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

import pytest


############################################################
# STUB THE DESKTOP AUTOMATION STACK
#
# Importing automation.executors.engine pulls in every executor,
# which pulls in pyautogui, pyperclip, mss and friends. Those are
# not installed in CI and must not be installed for these tests.
############################################################

def _installed(name):
    """True when this module is already loaded, or is installed.

    A module already present in sys.modules counts as installed: whatever
    is there is the real thing, or a test-owned stand-in, and must not be
    replaced by ours.
    """

    if name in sys.modules:
        return True

    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        # A module in sys.modules without a __spec__ raises ValueError from
        # find_spec. It is still present, so it is not ours to replace.
        return name in sys.modules


def _module(name, **attrs):
    """Register a stub module, marked as a package so submodules work.

    A module that is genuinely installed is never stubbed. Overwriting a
    real dependency with an inert stand-in would silently break any other
    test that imports it later in the same session - Pillow is installed
    in CI, so stubbing PIL here would shadow the real Pillow for
    tests/unit/test_local_client_context.py.
    """

    if _installed(name):
        return None

    stub = ModuleType(name)
    stub.__path__ = []

    for attr, value in attrs.items():
        setattr(stub, attr, value)

    sys.modules[name] = stub

    return stub


def _install_stubs():

    ########################################################
    # Each stub is inert: constructing anything from it and
    # calling any method on it does nothing and returns None.
    ########################################################

    class Inert:
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    pyautogui = _module(
        "pyautogui",
        FAILSAFE=True,
        size=lambda: (1920, 1080),
    )

    for attr in (
        "moveTo",
        "click",
        "doubleClick",
        "rightClick",
        "scroll",
        "dragTo",
        "typewrite",
        "press",
        "hotkey",
        "keyDown",
        "keyUp",
        "screenshot",
        "position",
    ):
        setattr(pyautogui, attr, lambda *a, **k: None)

    _module(
        "pyperclip",
        copy=lambda *a, **k: None,
        paste=lambda *a, **k: "",
    )

    _module("pygetwindow", getWindowsWithTitle=lambda *a, **k: [])

    ########################################################
    # mss and mss.tools are imported separately, so both need
    # registering. mss must look like a package.
    ########################################################

    _module("mss", mss=Inert)
    _module("mss.tools", to_png=lambda *a, **k: None)

    _module("easyocr", Reader=Inert)

    ########################################################
    # numpy is used as `np.<something>` at import time by the
    # OCR service, so it needs a few real attributes.
    ########################################################

    _module(
        "numpy",
        ndarray=Inert,
        array=lambda *a, **k: [],
        uint8=object,
        float32=float,
    )

    ########################################################
    # Pillow is imported by the OCR service. In the full CI
    # workflow it is installed, but these tests must also run
    # in the dependency-light job, so stub it too.
    ########################################################

    _module("PIL")
    _module(
        "PIL.Image",
        Image=Inert,
        open=lambda *a, **k: Inert(),
        fromarray=lambda *a, **k: Inert(),
        Resampling=SimpleNamespace(LANCZOS=1),
    )
    _module(
        "PIL.ImageOps",
        exif_transpose=lambda img: img,
    )

    ########################################################
    # ollama backs LocalAIClient, which ComputerUseAgent
    # constructs when no client is injected. The tests always
    # inject a Mock, so this only has to exist.
    ########################################################

    _module("ollama", Client=Inert, chat=lambda *a, **k: None)

    ########################################################
    # openpyxl is imported by SpreadsheetService. Register it
    # once, with the names the import sites need.
    ########################################################

    openpyxl = _module(
        "openpyxl",
        Workbook=Inert,
        load_workbook=lambda *a, **k: None,
    )

    _module("openpyxl.workbook", Workbook=Inert)
    _module("openpyxl.workbook.workbook", Workbook=Inert)
    _module("openpyxl.utils", get_column_letter=lambda n: "A")
    _module("openpyxl.styles", Font=Inert)


_install_stubs()


############################################################
# OTHER TESTS MAY REPLACE backend.computer_agent
#
# tests/unit/test_computer_agent_success_verification.py installs a
# placeholder module into sys.modules at import time. It does so with
# sys.modules.setdefault, which means that once it has run, the real
# module is no longer importable in that process. These tests need the
# real ComputerUseAgent, so drop the placeholder before importing it.
#
# pytest imports every test module before running any test, so this is
# deterministic rather than order-dependent.
############################################################

_placeholder = sys.modules.get("backend.computer_agent")

if _placeholder is not None and not getattr(
    _placeholder,
    "__file__",
    None,
):
    del sys.modules["backend.computer_agent"]


from automation.executors.engine import AutomationEngine
from backend.agent_policy import AgentPolicy
from backend.computer_agent import ComputerUseAgent
from core.actions import ActionType


############################################################
# FIXTURES
############################################################

class _RecordingExecutor:
    """Inert executor that records the actions routed to it."""

    def __init__(self, name):
        self.name = name
        self.calls = []

    def execute(self, action):
        self.calls.append(
            getattr(
                getattr(action, "action", None),
                "name",
                "",
            )
        )
        return True


def build_agent():
    """Build a ComputerUseAgent with the real engine and real policy."""

    engine = AutomationEngine()

    agent = ComputerUseAgent(
        engine=engine,
        ai_client=Mock(),
    )

    ########################################################
    # The terminal executor is the only route to a shell.
    # Record calls so a leak is detected rather than inferred.
    ########################################################

    terminal = engine.terminal

    terminal.execute = Mock(
        side_effect=AssertionError(
            "TerminalExecutor was reached - the policy gate failed."
        )
    )

    return agent, engine, terminal


############################################################
# TESTS
############################################################

@pytest.mark.parametrize(
    "tool,parameters",
    [
        ("RUN_COMMAND", {"command": "echo unsafe"}),
        ("RUN_PYTHON", {"script": "unsafe.py"}),
    ],
)
def test_shell_tools_are_rejected_before_the_executor(
    tool,
    parameters,
):

    agent, engine, terminal = build_agent()

    result = agent._execute_tool(
        {
            "tool": tool,
            "parameters": parameters,
        }
    )

    ########################################################
    # The call must fail with a policy rejection.
    ########################################################

    assert result["success"] is False
    assert "Policy rejected action" in result["error"]
    assert "confirmation" in result["error"]

    ########################################################
    # And the executor must never have been invoked.
    ########################################################

    terminal.execute.assert_not_called()


def test_shell_tools_are_absent_from_the_policy_capability_set():

    engine = AutomationEngine()

    policy = AgentPolicy(engine)

    available = policy.available()

    assert "RUN_COMMAND" not in available
    assert "RUN_PYTHON" not in available

    ########################################################
    # The engine still routes them; the policy is what removes
    # them. If this assertion ever fails, the route table changed
    # and the policy must be re-checked.
    ########################################################

    routed = {
        action_type.name
        for action_type in engine.routes
    }

    assert "RUN_COMMAND" in routed
    assert "RUN_PYTHON" in routed


def test_ordinary_actions_are_not_policy_rejected():

    agent, engine, terminal = build_agent()

    ########################################################
    # A harmless action must still pass the same gate. We assert
    # only that the policy did not reject it, and that the route
    # was resolved. The browser executor is replaced on the
    # instance so no browser is ever opened.
    ########################################################

    ########################################################
    # AutomationEngine.routes captured the executor objects at
    # construction, so replacing engine.browser would not be seen.
    # Swap the routed executor itself.
    ########################################################

    recorder = _RecordingExecutor("OPEN_URL")

    engine.routes[ActionType.OPEN_URL] = recorder

    result = agent._execute_tool(
        {
            "tool": "OPEN_URL",
            "parameters": {"url": "https://example.com"},
        }
    )

    assert "Policy rejected action" not in str(
        result.get("error", "")
    )

    assert recorder.calls == ["OPEN_URL"]

def test_shell_tools_are_not_advertised_in_agent_prompts_or_catalogs():
    from ai.tools import TOOLS

    agent, engine, terminal = build_agent()
    prompt = agent._build_prompt("Open YouTube", 1, {})

    assert "RUN_COMMAND" not in prompt
    assert "RUN_PYTHON" not in prompt
    assert "RUN_COMMAND" not in TOOLS
    assert "RUN_PYTHON" not in TOOLS

    available = agent.tools.available()
    assert "RUN_COMMAND" not in available
    assert "RUN_PYTHON" not in available
