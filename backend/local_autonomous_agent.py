import io
import json
import re
import time

import mss
from PIL import Image
from ollama import chat

from core.actions import Action, ActionType


class LocalAutonomousAgent:

    # ==========================================================
    # CONFIGURATION
    # ==========================================================

    MODEL = "qwen3-vl:4b-instruct"

    MAX_STEPS = 40
    THINK_RETRIES = 3

    ACTION_DELAY = 0.25
    FAILURE_DELAY = 0.60
    APP_START_DELAY = 0.80

    KEEP_ALIVE = "10m"

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self, engine):

        self.engine = engine

        self.sct = mss.mss()

        self.goal = ""

        self.history = []

        self.variables = {}

        self.current_step = 0

        self.last_decision = None

        print(
            f"[LocalAgent] Model: {self.MODEL}"
        )

        print(
            "[LocalAgent] Universal computer agent ready."
        )

    # ==========================================================
    # SHOULD HANDLE
    #
    # This is intentionally broad.
    #
    # The agent is NOT restricted to a list of demo commands.
    # ==========================================================

    def shouldHandle(self, command):

        text = str(
            command or ""
        ).strip()

        if not text:
            return False

        return True

    # ==========================================================
    # RUN
    # ==========================================================

    def run(self, command):

        self.goal = str(
            command or ""
        ).strip()

        self.history.clear()
        self.variables.clear()

        self.current_step = 0
        self.last_decision = None

        if not self.goal:

            return (
                "I did not receive a computer command, sir."
            )

        print()
        print("=" * 78)
        print(
            "[LocalAgent] JARVIS UNIVERSAL COMPUTER MODE"
        )
        print(
            f"[LocalAgent] Goal: {self.goal}"
        )
        print(
            f"[LocalAgent] Model: {self.MODEL}"
        )
        print("=" * 78)

        # ======================================================
        # AUTONOMOUS LOOP
        # ======================================================

        for step in range(
            1,
            self.MAX_STEPS + 1
        ):

            self.current_step = step

            print()
            print(
                f"[LocalAgent] STEP {step}/{self.MAX_STEPS}"
            )

            # --------------------------------------------------
            # OBSERVE
            # --------------------------------------------------

            try:

                screen = self.captureScreen()

            except Exception as exc:

                print(
                    "[LocalAgent] Screen capture failed:"
                )

                print(exc)

                return (
                    "I could not observe the computer, sir."
                )

            # --------------------------------------------------
            # THINK
            # --------------------------------------------------

            try:

                decision = self.think(
                    screen,
                    step
                )

            except Exception as exc:

                print(
                    "[LocalAgent] Reasoning failed:"
                )

                print(exc)

                return (
                    "I could not reason through "
                    "the computer task locally, sir."
                )

            self.last_decision = decision

            # --------------------------------------------------
            # REASON
            # --------------------------------------------------

            reason = str(
                decision.get(
                    "reason",
                    ""
                )
            ).strip()

            if reason:

                print(
                    "[LocalAgent] Reason:"
                )

                print(reason)

            # --------------------------------------------------
            # COMPLETION
            # --------------------------------------------------

            if decision.get(
                "done",
                False
            ):

                message = str(
                    decision.get(
                        "message",
                        "Task completed, sir."
                    )
                ).strip()

                if not message:

                    message = (
                        "Task completed, sir."
                    )

                print()
                print(
                    "[LocalAgent] COMPLETE:"
                )

                print(message)

                return message

            # --------------------------------------------------
            # EXTRACT ACTION
            # --------------------------------------------------

            action_data = decision.get(
                "action"
            )

            if not isinstance(
                action_data,
                dict
            ):

                print(
                    "[LocalAgent] "
                    "No valid action returned."
                )

                self.recordFailure(
                    step,
                    "No action returned by model."
                )

                time.sleep(
                    self.FAILURE_DELAY
                )

                continue

            # --------------------------------------------------
            # TOOL
            # --------------------------------------------------

            tool = str(
                action_data.get(
                    "tool",
                    ""
                )
            ).strip().upper()

            if not tool:

                print(
                    "[LocalAgent] "
                    "Model returned an empty tool."
                )

                self.recordFailure(
                    step,
                    "Empty action tool."
                )

                time.sleep(
                    self.FAILURE_DELAY
                )

                continue

            # --------------------------------------------------
            # PARAMETERS
            # --------------------------------------------------

            parameters = action_data.get(
                "parameters",
                {}
            )

            if not isinstance(
                parameters,
                dict
            ):

                parameters = {}

            parameters = (
                self.normalizeParameters(
                    tool,
                    parameters
                )
            )

            # --------------------------------------------------
            # DUPLICATE ACTION GUARD
            # --------------------------------------------------

            if self.isRepeatedSuccessfulAction(
                tool,
                parameters
            ):

                print(
                    "[LocalAgent] "
                    "Repeated successful action detected."
                )

                self.history.append(
                    {
                        "step": step,
                        "tool": tool,
                        "parameters": parameters,
                        "success": False,
                        "error":
                            "duplicate successful action"
                    }
                )

                time.sleep(
                    self.FAILURE_DELAY
                )

                continue

            # --------------------------------------------------
            # CONVERT TO CORE ACTION
            # --------------------------------------------------

            core_action = (
                self.toCoreAction(
                    tool,
                    parameters
                )
            )

            if core_action is None:

                print(
                    "[LocalAgent] "
                    f"Rejected action: {tool}"
                )

                self.recordFailure(
                    step,
                    f"Unsupported or blocked action: {tool}",
                    tool,
                    parameters
                )

                time.sleep(
                    self.FAILURE_DELAY
                )

                continue

            # --------------------------------------------------
            # EXECUTE
            # --------------------------------------------------

            print(
                f"[LocalAgent] ACTION: {tool}"
            )

            print(
                f"[LocalAgent] PARAMETERS: "
                f"{parameters}"
            )

            try:

                result = (
                    self.engine.executeAction(
                        core_action
                    )
                )

                success = (
                    result is not False
                )

            except Exception as exc:

                result = str(
                    exc
                )

                success = False

            # --------------------------------------------------
            # RESULT
            # --------------------------------------------------

            print(
                f"[LocalAgent] RESULT: {result}"
            )

            # --------------------------------------------------
            # RECORD
            # --------------------------------------------------

            self.history.append(
                {
                    "step": step,
                    "tool": tool,
                    "parameters": parameters,
                    "success": success,
                    "result": self.safeString(
                        result
                    )
                }
            )

            # --------------------------------------------------
            # VARIABLES
            # --------------------------------------------------

            if "variable" in parameters:

                name = str(
                    parameters.get(
                        "variable",
                        ""
                    )
                ).strip()

                if name:

                    self.variables[name] = (
                        self.safeString(
                            result
                        )
                    )

            # --------------------------------------------------
            # RECOVERY / TIMING
            # --------------------------------------------------

            if not success:

                print(
                    "[LocalAgent] "
                    "Action failed."
                )

                print(
                    "[LocalAgent] "
                    "Re-observing for recovery."
                )

                time.sleep(
                    self.FAILURE_DELAY
                )

                continue

            # Applications need a little time to initialize.
            if tool in {
                "OPEN_APP",
                "OPEN_APPLICATION",
                "LAUNCH_APP",
                "LAUNCH_APPLICATION"
            }:

                time.sleep(
                    self.APP_START_DELAY
                )

            elif tool == "WAIT":

                # The engine handles WAIT.
                pass

            else:

                time.sleep(
                    self.ACTION_DELAY
                )

        # ======================================================
        # MAXIMUM STEPS
        # ======================================================

        print()
        print(
            "[LocalAgent] "
            "Maximum autonomous steps reached."
        )

        return (
            "I reached the autonomous step limit "
            "before I could verify completion, sir."
        )

    # ==========================================================
    # SCREEN CAPTURE
    #
    # IMPORTANT:
    #
    # The screenshot is NEVER written to disk.
    #
    # It exists only in memory and is immediately passed to
    # the local vision model.
    # ==========================================================

    def captureScreen(self):

        monitor = (
            self.sct.monitors[0]
        )

        screenshot = (
            self.sct.grab(
                monitor
            )
        )

        image = Image.frombytes(
            "RGB",
            screenshot.size,
            screenshot.rgb
        )

        buffer = io.BytesIO()

        try:

            image.save(
                buffer,
                format="PNG"
            )

            return buffer.getvalue()

        finally:

            buffer.close()

    # ==========================================================
    # THINK
    # ==========================================================

    def think(
        self,
        image_bytes,
        step
    ):

        prompt = self.buildPrompt(
            step
        )

        last_error = None

        for attempt in range(
            1,
            self.THINK_RETRIES + 1
        ):

            try:

                response = chat(
                    model=self.MODEL,

                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                            "images": [
                                image_bytes
                            ]
                        }
                    ],

                    stream=False,

                    format="json",

                    options={
                        "temperature": 0,
                        "num_ctx": 8192,
                        "num_predict": 512
                    },

                    keep_alive=self.KEEP_ALIVE
                )

                message = (
                    response.message
                )

                content = str(
                    getattr(
                        message,
                        "content",
                        ""
                    ) or ""
                ).strip()

                thinking = str(
                    getattr(
                        message,
                        "thinking",
                        ""
                    ) or ""
                ).strip()

                print()
                print(
                    "[LocalAgent] QWEN RESPONSE:"
                )

                print(
                    f"[LocalAgent] "
                    f"Content length: {len(content)}"
                )

                if thinking:

                    print(
                        f"[LocalAgent] "
                        f"Thinking length: "
                        f"{len(thinking)}"
                    )

                # --------------------------------------------------
                # VALID RESPONSE
                # --------------------------------------------------

                if content:

                    print()
                    print(
                        "[LocalAgent] RAW QWEN RESPONSE:"
                    )

                    print(content)

                    decision = (
                        self.parseJSON(
                            content
                        )
                    )

                    return (
                        self.normalizeDecision(
                            decision
                        )
                    )

                # --------------------------------------------------
                # EMPTY RESPONSE
                # --------------------------------------------------

                if thinking:

                    last_error = (
                        "Model returned thinking "
                        "without final content."
                    )

                else:

                    last_error = (
                        "Model returned empty content."
                    )

                print(
                    f"[LocalAgent] "
                    f"Think attempt {attempt} failed: "
                    f"{last_error}"
                )

            except Exception as exc:

                last_error = str(
                    exc
                )

                print(
                    f"[LocalAgent] "
                    f"Think attempt {attempt} failed:"
                )

                print(exc)

            time.sleep(
                0.5
            )

        raise RuntimeError(
            "Local reasoning failed after "
            f"{self.THINK_RETRIES} attempts: "
            f"{last_error}"
        )

    # ==========================================================
    # PROMPT
    #
    # THIS IS UNIVERSAL.
    #
    # There are deliberately NO:
    #
    # - Notepad instructions
    # - Calculator instructions
    # - Chrome instructions
    # - YouTube instructions
    # - Demo commands
    #
    # ==========================================================

    def buildPrompt(
        self,
        step
    ):

        recent_history = (
            self.history[-12:]
        )

        history_text = json.dumps(
            recent_history,
            indent=2,
            ensure_ascii=False
        )

        variables_text = json.dumps(
            self.variables,
            indent=2,
            ensure_ascii=False
        )

        return f"""
You are JARVIS, the autonomous computer-use brain.

You control a real Windows computer through an existing
automation engine.

Your purpose is to execute the user's computer task.

You are NOT a conversational assistant.

You are NOT writing a tutorial.

You are controlling the computer.

============================================================
USER GOAL
============================================================

{self.goal}

============================================================
CURRENT STEP
============================================================

{step}

============================================================
RECENT ACTION HISTORY
============================================================

{history_text}

============================================================
KNOWN VARIABLES
============================================================

{variables_text}

============================================================
CORE OPERATING LOOP
============================================================

The computer state shown in the screenshot is the current
reality.

The user's goal is the mission.

Your job is to determine the single best next computer action.

After that action is executed, you will receive a new
screenshot and must reason again.

Therefore:

OBSERVE
THINK
ACT
OBSERVE AGAIN
VERIFY
CONTINUE

Do not assume that an action worked.

Do not assume that an application opened successfully.

Do not assume that text was entered successfully.

Do not assume that a button was clicked.

Use the next screenshot to determine the new state.

============================================================
GENERAL RULES
============================================================

1. Preserve the COMPLETE original user goal.

2. Never forget unfinished parts of the goal.

3. Perform ONE action per response.

4. Never claim completion until the ENTIRE goal is complete.

5. Never invent visible UI elements.

6. Never invent text.

7. Never invent numbers.

8. Never invent results.

9. Never repeat a successful action unless the current
   screen proves it is necessary.

10. If an action fails, recover from the new computer state.

11. If an application has just launched, allow it to stabilize.

12. Prefer direct computer actions.

13. Use visual interaction when the task requires interacting
    with visible UI.

14. Use keyboard actions when they are more reliable.

15. Preserve exact user-provided text.

16. Do not transform a general web search into a search on
    a specific website unless the user explicitly requested it.

17. Do not open files merely because their names resemble
    application names.

18. When the user requests an application to be opened,
    use OPEN_APP.

19. When the user requests a website to be opened directly,
    use OPEN_URL.

20. When the user requests a general internet search,
    use SEARCH_WEB.

21. When the user requests an exact piece of text to be typed,
    use one TYPE_TEXT action containing the complete text.

22. Do not type long exact text character-by-character.

23. If the goal contains multiple operations, complete them
    in logical order.

24. Do not jump backwards to an already completed part of
    the goal.

25. If the current screen contradicts your previous assumption,
    trust the current screen.

============================================================
COMPUTER CAPABILITIES
============================================================

You may use the capabilities exposed by the automation engine.

APPLICATIONS:

OPEN_APP
CLOSE_APP

WINDOWS:

FOCUS_WINDOW
CLOSE_WINDOW
MINIMIZE_WINDOW
MAXIMIZE_WINDOW
RESTORE_WINDOW
MOVE_WINDOW
RESIZE_WINDOW

BROWSER:

OPEN_URL
SEARCH_WEB

MOUSE:

MOUSE_MOVE
MOUSE_MOVE_CENTER
LEFT_CLICK
RIGHT_CLICK
DOUBLE_CLICK
SCROLL_UP
SCROLL_DOWN
DRAG

KEYBOARD:

TYPE_TEXT
PRESS_KEY
HOTKEY
HOLD_KEY
RELEASE_KEY

CLIPBOARD:

READ_CLIPBOARD
WRITE_CLIPBOARD
CLEAR_CLIPBOARD

VISION:

TAKE_SCREENSHOT
TAKE_REGION_SCREENSHOT
TAKE_WINDOW_SCREENSHOT
OCR_SCREEN
OCR_IMAGE
LOCATE_TEXT
CLICK_TEXT
CLICK_TYPE_ENTER
CLICK_FIRST_VIDEO

SYSTEM:

RUN_COMMAND
RUN_PYTHON
VOLUME
BRIGHTNESS
WAIT
NOTIFY

FILES:

CREATE_FILE
CREATE_FOLDER
COPY
MOVE
RENAME

============================================================
ACTION SELECTION
============================================================

Choose the action that directly advances the user's goal.

Examples of GENERAL reasoning:

If the user wants an application opened:

OPEN_APP

If the user wants a URL opened:

OPEN_URL

If the user wants information searched on the web:

SEARCH_WEB

If text must be entered into the currently active application:

TYPE_TEXT

If a keyboard command is required:

PRESS_KEY or HOTKEY

If a visible UI element must be selected:

LOCATE_TEXT or CLICK_TEXT

If the application needs time to load:

WAIT

If a file must be manipulated:

use the appropriate file capability.

These are capability examples, not hardcoded tasks.

============================================================
VISUAL REASONING
============================================================

When using the screenshot:

1. Identify the active application.

2. Identify the current window state.

3. Identify visible UI elements.

4. Identify what has already happened.

5. Compare the current state with the user's goal.

6. Select the next action.

Never assume that the first visible result is the correct
result.

Never click blindly when multiple possible targets exist.

============================================================
MULTI-STEP TASKS
============================================================

For a multi-step goal:

Track:

- completed operations
- current operation
- remaining operations
- failed operations
- important results
- application state

Do not restart the entire task after one failed action.

Recover from the current state.

============================================================
COMPLETION
============================================================

Only return done=true when the ENTIRE user goal has actually
been achieved.

If any meaningful part remains, done MUST be false.

============================================================
SAFETY
============================================================

Do not autonomously:

- shut down the computer
- restart the computer
- format drives
- destroy system data
- disable security systems

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

For an action:

{{
    "done": false,
    "reason": "Explain why this is the correct next action.",
    "action": {{
        "tool": "ACTION_NAME",
        "parameters": {{}}
    }}
}}

For genuine completion:

{{
    "done": true,
    "reason": "Explain the visible evidence that the entire goal is complete.",
    "message": "Task completed, sir."
}}

No markdown.

No code fences.

No text outside JSON.
"""

    # ==========================================================
    # JSON PARSER
    # ==========================================================

    def parseJSON(
        self,
        text
    ):

        text = str(
            text or ""
        ).strip()

        if not text:

            raise ValueError(
                "Empty model response."
            )

        # Remove <think> blocks if they appear.
        text = re.sub(
            r"<think>.*?</think>",
            "",
            text,
            flags=re.I | re.S
        ).strip()

        # Remove markdown fences.
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.I
        )

        text = re.sub(
            r"\s*```$",
            "",
            text
        ).strip()

        # Direct JSON.
        try:

            value = json.loads(
                text
            )

            if isinstance(
                value,
                dict
            ):

                return value

        except json.JSONDecodeError:

            pass

        # ------------------------------------------------------
        # FIND FIRST COMPLETE JSON OBJECT
        # ------------------------------------------------------

        start = text.find(
            "{"
        )

        if start == -1:

            raise ValueError(
                "No JSON object found in model response."
            )

        depth = 0

        in_string = False

        escaped = False

        for index in range(
            start,
            len(text)
        ):

            char = text[index]

            if escaped:

                escaped = False

                continue

            if (
                char == "\\"
                and in_string
            ):

                escaped = True

                continue

            if char == '"':

                in_string = not in_string

                continue

            if in_string:

                continue

            if char == "{":

                depth += 1

            elif char == "}":

                depth -= 1

                if depth == 0:

                    candidate = text[
                        start:index + 1
                    ]

                    try:

                        value = json.loads(
                            candidate
                        )

                        if isinstance(
                            value,
                            dict
                        ):

                            return value

                    except json.JSONDecodeError:

                        pass

                    break

        raise ValueError(
            "Model returned invalid JSON."
        )

    # ==========================================================
    # DECISION NORMALIZATION
    # ==========================================================

    def normalizeDecision(
        self,
        decision
    ):

        if not isinstance(
            decision,
            dict
        ):

            raise ValueError(
                "Decision is not a JSON object."
            )

        done = decision.get(
            "done",
            False
        )

        if isinstance(
            done,
            str
        ):

            done = (
                done.lower().strip()
                in {
                    "true",
                    "yes",
                    "1",
                    "done"
                }
            )

        action = decision.get(
            "action"
        )

        # Standard format.
        if isinstance(
            action,
            dict
        ):

            return {
                "done": bool(done),

                "reason": str(
                    decision.get(
                        "reason",
                        ""
                    )
                ),

                "message": str(
                    decision.get(
                        "message",
                        ""
                    )
                ),

                "action": action
            }

        # Compatibility with action arrays.
        actions = decision.get(
            "actions"
        )

        if isinstance(
            actions,
            list
        ):

            for candidate in actions:

                if not isinstance(
                    candidate,
                    dict
                ):

                    continue

                if candidate.get(
                    "tool"
                ):

                    return {
                        "done": bool(done),

                        "reason": str(
                            decision.get(
                                "reason",
                                ""
                            )
                        ),

                        "message": str(
                            decision.get(
                                "message",
                                ""
                            )
                        ),

                        "action": candidate
                    }

        # Compatibility with top-level tool.
        tool = decision.get(
            "tool"
        )

        if tool:

            return {
                "done": bool(done),

                "reason": str(
                    decision.get(
                        "reason",
                        ""
                    )
                ),

                "message": str(
                    decision.get(
                        "message",
                        ""
                    )
                ),

                "action": {
                    "tool": tool,

                    "parameters": decision.get(
                        "parameters",
                        {}
                    )
                }
            }

        return {
            "done": bool(done),

            "reason": str(
                decision.get(
                    "reason",
                    ""
                )
            ),

            "message": str(
                decision.get(
                    "message",
                    ""
                )
            ),

            "action": None
        }

    # ==========================================================
    # PARAMETER NORMALIZATION
    # ==========================================================

    def normalizeParameters(
        self,
        tool,
        parameters
    ):

        if not isinstance(
            parameters,
            dict
        ):

            return {}

        parameters = dict(
            parameters
        )

        # ------------------------------------------------------
        # APPLICATION
        # ------------------------------------------------------

        if (
            "app" not in parameters
        ):

            for key in (
                "app_name",
                "application",
                "application_name"
            ):

                if key in parameters:

                    parameters["app"] = (
                        parameters[key]
                    )

                    break

        # ------------------------------------------------------
        # URL
        # ------------------------------------------------------

        if (
            "url" not in parameters
            and "website" in parameters
        ):

            parameters["url"] = (
                parameters["website"]
            )

        if (
            "url" not in parameters
            and "website_url" in parameters
        ):

            parameters["url"] = (
                parameters["website_url"]
            )

        # ------------------------------------------------------
        # SEARCH QUERY
        # ------------------------------------------------------

        if (
            "query" not in parameters
            and "search_query" in parameters
        ):

            parameters["query"] = (
                parameters["search_query"]
            )

        # ------------------------------------------------------
        # TEXT
        # ------------------------------------------------------

        if (
            "text" not in parameters
            and "content" in parameters
        ):

            parameters["text"] = (
                parameters["content"]
            )

        # ------------------------------------------------------
        # WAIT
        # ------------------------------------------------------

        if (
            "seconds" not in parameters
            and "time_ms" in parameters
        ):

            try:

                parameters["seconds"] = (
                    float(
                        parameters["time_ms"]
                    ) / 1000.0
                )

            except Exception:

                parameters["seconds"] = 1

        # ------------------------------------------------------
        # COORDINATES
        # ------------------------------------------------------

        if (
            "x" not in parameters
            and "x_position" in parameters
        ):

            parameters["x"] = (
                parameters["x_position"]
            )

        if (
            "y" not in parameters
            and "y_position" in parameters
        ):

            parameters["y"] = (
                parameters["y_position"]
            )

        return parameters

    # ==========================================================
    # CORE ACTION CONVERSION
    # ==========================================================

    def toCoreAction(
        self,
        tool,
        parameters
    ):

        # ------------------------------------------------------
        # AUTONOMOUS SAFETY BLOCK
        # ------------------------------------------------------

        blocked = {
            "SHUTDOWN",
            "RESTART",
            "SLEEP",
            "FORMAT_DRIVE",
            "FORMAT_DISK",
            "DESTROY_SYSTEM"
        }

        if tool in blocked:

            print(
                f"[LocalAgent] "
                f"Blocked unsafe action: {tool}"
            )

            return None

        # ------------------------------------------------------
        # MODEL ALIASES
        # ------------------------------------------------------

        aliases = {
            "OPEN_APPLICATION":
                "OPEN_APP",

            "LAUNCH_APP":
                "OPEN_APP",

            "LAUNCH_APPLICATION":
                "OPEN_APP",

            "TYPE":
                "TYPE_TEXT",

            "TYPE_TEXT_INTO":
                "TYPE_TEXT",

            "PRESS":
                "PRESS_KEY",

            "KEY_PRESS":
                "PRESS_KEY",

            "CLICK":
                "LEFT_CLICK",

            "LEFTCLICK":
                "LEFT_CLICK",

            "RIGHTCLICK":
                "RIGHT_CLICK",

            "DOUBLECLICK":
                "DOUBLE_CLICK",

            "WAIT_SECONDS":
                "WAIT"
        }

        tool = aliases.get(
            tool,
            tool
        )

        # ------------------------------------------------------
        # ACTION TYPE
        # ------------------------------------------------------

        action_type = getattr(
            ActionType,
            tool,
            None
        )

        if action_type is None:

            print(
                "[LocalAgent] "
                f"Unknown ActionType: {tool}"
            )

            return None

        # ------------------------------------------------------
        # PARAMETERS
        # ------------------------------------------------------

        if not isinstance(
            parameters,
            dict
        ):

            parameters = {}

        # ------------------------------------------------------
        # WAIT SAFETY
        # ------------------------------------------------------

        if tool == "WAIT":

            try:

                seconds = float(
                    parameters.get(
                        "seconds",
                        1
                    )
                )

            except Exception:

                seconds = 1

            seconds = max(
                0.1,
                min(
                    seconds,
                    30
                )
            )

            parameters = {
                "seconds": seconds
            }

        # ------------------------------------------------------
        # CREATE ACTION
        # ------------------------------------------------------

        return Action(
            action=action_type,
            parameters=parameters
        )

    # ==========================================================
    # DUPLICATE ACTION DETECTION
    # ==========================================================

    def isRepeatedSuccessfulAction(
        self,
        tool,
        parameters
    ):

        if not self.history:

            return False

        for item in reversed(
            self.history[-3:]
        ):

            if not item.get(
                "success",
                False
            ):

                continue

            if item.get(
                "tool"
            ) != tool:

                continue

            previous_parameters = (
                item.get(
                    "parameters",
                    {}
                )
            )

            if previous_parameters == parameters:

                return True

        return False

    # ==========================================================
    # FAILURE RECORD
    # ==========================================================

    def recordFailure(
        self,
        step,
        error,
        tool=None,
        parameters=None
    ):

        self.history.append(
            {
                "step": step,
                "tool": tool or "",
                "parameters":
                    parameters or {},
                "success": False,
                "error": str(
                    error
                )
            }
        )

    # ==========================================================
    # SAFE STRING
    # ==========================================================

    def safeString(
        self,
        value
    ):

        try:

            return str(
                value
            )

        except Exception:

            return "<unprintable result>"