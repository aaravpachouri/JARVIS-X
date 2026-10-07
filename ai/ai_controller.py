from __future__ import annotations

import threading

from ai.router import AIRouter

from core.actions import (
    Action as CoreAction,
    ActionType,
)

from automation.executors.engine import AutomationEngine

from backend.ai_brain import (
    AIBrain,
    BrainResponse,
)

from backend.local_responder import LocalResponder

from backend.computer_agent import (
    ComputerUseAgent,
)

from voice.tts_engine import TTSEngine


class AIController:

    """
    JARVIS X
    UNIVERSAL AI CONTROLLER

    The controller is now the bridge between:

        USER
          |
          v
        AIBrain
          |
          +---- CHAT ------> normal AI response
          |
          +---- COMPUTER --> ComputerUseAgent
          |
          +---- HYBRID ----> brain result + computer task

    IMPORTANT:

    ComputerUseAgent is NOT the primary brain anymore.

    It is a computer-control capability used when the AIBrain
    determines that physical computer interaction is required.

    The legacy AIRouter remains available only as a compatibility
    fallback if the new brain fails.
    """

    INTERRUPTED_RESULT = "__JARVIS_INTERRUPT__"

    ############################################################
    # INITIALIZATION
    ############################################################

    def __init__(self):

        ########################################################
        # GENERAL AI BRAIN
        ########################################################

        print(
            "[AIController] "
            "Loading JARVIS universal brain..."
        )

        self.brain = AIBrain()

        print(
            "[AIController] "
            "Universal AI brain ready."
        )

        ########################################################
        # LEGACY ROUTER
        #
        # Kept for compatibility/fallback.
        ########################################################

        self.router = AIRouter()

        ########################################################
        # AUTOMATION ENGINE
        ########################################################

        self.engine = AutomationEngine()

        ########################################################
        # LOCAL RESPONDER
        #
        # Kept available for compatibility and simple local
        # responses, but it is NO LONGER the primary decision
        # maker.
        ########################################################

        self.localResponder = (
            LocalResponder()
        )

        ########################################################
        # UNIVERSAL COMPUTER AGENT
        #
        # This is now a capability of the brain.
        ########################################################

        self.localAgent = (
            ComputerUseAgent(
                engine=self.engine
            )
        )

        ########################################################
        # TTS
        ########################################################

        print(
            "[AIController] "
            "Loading JARVIS voice..."
        )

        self.tts = TTSEngine()

        print(
            "[AIController] "
            "Voice ready."
        )

        ########################################################
        # EXECUTION CONTROL
        #
        # Every command receives its own run id.
        #
        # Interrupting a command invalidates that run id. If the
        # Gemini call returns later, the stale result is discarded.
        ########################################################

        self._execution_lock = threading.Lock()

        self._execution_counter = 0

        self._active_execution_id = 0

        self._cancel_event = threading.Event()

        ########################################################
        # ACTION MAP
        #
        # Retained for legacy router compatibility.
        ########################################################

        self.actionMap = {

            ####################################################
            # APPLICATIONS
            ####################################################

            "OPEN_APP":
                ActionType.OPEN_APP,

            "CLOSE_APP":
                ActionType.CLOSE_APP,

            ####################################################
            # WEB
            ####################################################

            "OPEN_URL":
                ActionType.OPEN_URL,

            "SEARCH_WEB":
                ActionType.SEARCH_WEB,

            ####################################################
            # FILE SYSTEM
            ####################################################

            "CREATE_FILE":
                ActionType.CREATE_FILE,

            "DELETE_FILE":
                ActionType.DELETE_FILE,

            "CREATE_FOLDER":
                ActionType.CREATE_FOLDER,

            "DELETE_FOLDER":
                ActionType.DELETE_FOLDER,

            "COPY":
                ActionType.COPY,

            "MOVE":
                ActionType.MOVE,

            "RENAME":
                ActionType.RENAME,

            ####################################################
            # MOUSE
            ####################################################

            "MOUSE_MOVE":
                ActionType.MOUSE_MOVE,

            "MOUSE_MOVE_CENTER":
                ActionType.MOUSE_MOVE_CENTER,

            "LEFT_CLICK":
                ActionType.LEFT_CLICK,

            "RIGHT_CLICK":
                ActionType.RIGHT_CLICK,

            "DOUBLE_CLICK":
                ActionType.DOUBLE_CLICK,

            "SCROLL_UP":
                ActionType.SCROLL_UP,

            "SCROLL_DOWN":
                ActionType.SCROLL_DOWN,

            "DRAG":
                ActionType.DRAG,

            ####################################################
            # KEYBOARD
            ####################################################

            "TYPE_TEXT":
                ActionType.TYPE_TEXT,

            "PRESS_KEY":
                ActionType.PRESS_KEY,

            "HOTKEY":
                ActionType.HOTKEY,

            "HOLD_KEY":
                ActionType.HOLD_KEY,

            "RELEASE_KEY":
                ActionType.RELEASE_KEY,

            ####################################################
            # WINDOWS
            ####################################################

            "FOCUS_WINDOW":
                ActionType.FOCUS_WINDOW,

            "CLOSE_WINDOW":
                ActionType.CLOSE_WINDOW,

            "MINIMIZE_WINDOW":
                ActionType.MINIMIZE_WINDOW,

            "MAXIMIZE_WINDOW":
                ActionType.MAXIMIZE_WINDOW,

            "RESTORE_WINDOW":
                ActionType.RESTORE_WINDOW,

            "MOVE_WINDOW":
                ActionType.MOVE_WINDOW,

            "RESIZE_WINDOW":
                ActionType.RESIZE_WINDOW,

            ####################################################
            # CLIPBOARD
            ####################################################

            "READ_CLIPBOARD":
                ActionType.READ_CLIPBOARD,

            "WRITE_CLIPBOARD":
                ActionType.WRITE_CLIPBOARD,

            "CLEAR_CLIPBOARD":
                ActionType.CLEAR_CLIPBOARD,

            ####################################################
            # SCREENSHOT
            ####################################################

            "TAKE_SCREENSHOT":
                ActionType.TAKE_SCREENSHOT,

            "TAKE_REGION_SCREENSHOT":
                ActionType.TAKE_REGION_SCREENSHOT,

            "TAKE_WINDOW_SCREENSHOT":
                ActionType.TAKE_WINDOW_SCREENSHOT,

            "SAVE_SCREENSHOT":
                ActionType.SAVE_SCREENSHOT,

            ####################################################
            # OCR
            ####################################################

            "OCR_SCREEN":
                ActionType.OCR_SCREEN,

            "OCR_IMAGE":
                ActionType.OCR_IMAGE,

            ####################################################
            # VISION
            ####################################################

            "LOCATE_TEXT":
                ActionType.LOCATE_TEXT,

            "CLICK_TEXT":
                ActionType.CLICK_TEXT,

            "CLICK_TYPE_ENTER":
                ActionType.CLICK_TYPE_ENTER,

            "CLICK_FIRST_VIDEO":
                ActionType.CLICK_FIRST_VIDEO,

            ####################################################
            # TERMINAL
            ####################################################

            "RUN_COMMAND":
                ActionType.RUN_COMMAND,

            "RUN_PYTHON":
                ActionType.RUN_PYTHON,

            ####################################################
            # SYSTEM
            ####################################################

            "VOLUME":
                ActionType.VOLUME,

            "BRIGHTNESS":
                ActionType.BRIGHTNESS,

            "SHUTDOWN":
                ActionType.SHUTDOWN,

            "RESTART":
                ActionType.RESTART,

            "SLEEP":
                ActionType.SLEEP,

            ####################################################
            # AI
            ####################################################

            "ASK_AI":
                ActionType.ASK_AI,

            ####################################################
            # CONTROL
            ####################################################

            "WAIT":
                ActionType.WAIT,

            "NOTIFY":
                ActionType.NOTIFY,
        }

        ########################################################
        # DYNAMIC ACTION FALLBACK
        ########################################################

        for name in dir(
            ActionType
        ):

            if not name.isupper():
                continue

            if name.startswith("_"):
                continue

            value = getattr(
                ActionType,
                name,
                None
            )

            if value is not None:

                self.actionMap.setdefault(
                    name,
                    value
                )

        print(
            "[AIController] "
            "Brain + Computer capability integrated."
        )

    ############################################################
    # EXECUTION CONTROL
    ############################################################

    def _begin_execution(
        self
    ):

        with self._execution_lock:

            self._execution_counter += 1

            execution_id = (
                self._execution_counter
            )

            self._active_execution_id = (
                execution_id
            )

            self._cancel_event.clear()

            return execution_id

    def _is_execution_cancelled(
        self,
        execution_id
    ):

        with self._execution_lock:

            return (
                self._cancel_event.is_set()
                or
                execution_id
                !=
                self._active_execution_id
            )

    def _cancel_execution(
        self
    ):

        ########################################################
        # Event cancellation stops cooperative work.
        ########################################################

        self._cancel_event.set()

        ########################################################
        # Generation invalidation is the hard guarantee.
        #
        # Even if a running Gemini call returns later, its
        # execution id can NEVER become current again.
        ########################################################

        with self._execution_lock:

            self._execution_counter += 1

            self._active_execution_id = (
                self._execution_counter
            )

    ############################################################
    ############################################################
    # SPEAK
    ############################################################

    def _speak(
        self,
        text,
        execution_id=None
    ):

        if not text:
            return

        if (
            execution_id is not None
            and
            self._is_execution_cancelled(
                execution_id
            )
        ):

            print(
                "[AIController] "
                "Speech suppressed: execution was cancelled."
            )

            return

        try:

            print(
                f"[JARVIS] {text}"
            )

            self.tts.speak(
                text
            )

        except Exception as exc:

            print(
                f"[TTS] Error: {exc}"
            )

    ############################################################
    # BRAIN
    ############################################################

    def _think(
        self,
        command
    ):

        print()
        print(
            "[AIController] "
            "JARVIS BRAIN"
        )

        print(
            "[AIController] "
            "Understanding request..."
        )

        try:

            response = (
                self.brain.think(
                    command
                )
            )

            return response

        except Exception as exc:

            print()
            print(
                "[AIController] "
                "Brain error:",
                exc
            )

            return BrainResponse(
                mode=AIBrain.CHAT,
                answer="",
                success=False,
                error=str(exc)
            )

    ############################################################
    # EXECUTE COMPUTER GOAL
    ############################################################

    def _execute_computer_goal(
        self,
        goal
    ):

        goal = str(
            goal or ""
        ).strip()

        if not goal:

            return (
                "I could not determine "
                "the computer task, sir."
            )

        print()
        print(
            "[AIController] "
            "COMPUTER MODE"
        )

        print(
            "[AIController] "
            "JARVIS is taking control "
            "of the computer."
        )

        print(
            "[AIController] "
            f"Computer objective: {goal}"
        )

        try:

            if not self.localAgent.shouldHandle(
                goal
            ):

                return (
                    "I could not safely start "
                    "the computer task, sir."
                )

            result = (
                self.localAgent.run(
                    goal
                )
            )

            if result:

                return str(
                    result
                )

            return (
                "The computer task finished "
                "without a final response, sir."
            )

        except Exception as exc:

            print()
            print(
                "[AIController] "
                "Computer agent error:"
            )

            print(
                exc
            )

            return (
                f"I encountered a computer-control "
                f"error: {exc}"
            )

    ############################################################
    # HYBRID
    ############################################################

    def _execute_hybrid(
        self,
        brain_response
    ):

        """
        Execute the physical portion of a hybrid request.

        The brain response may already contain a normal answer
        or reasoning result.

        The computer portion is executed separately.

        This is intentionally simple for the first integration.
        A later hybrid coordinator can preserve richer state
        between multiple reasoning/computer phases.
        """

        computer_goal = str(
            getattr(
                brain_response,
                "computer_goal",
                ""
            )
            or ""
        ).strip()

        answer = str(
            getattr(
                brain_response,
                "answer",
                ""
            )
            or ""
        ).strip()

        if not computer_goal:

            return (
                answer
                or
                "I could not determine the "
                "computer portion of that task, sir."
            )

        computer_result = (
            self._execute_computer_goal(
                computer_goal
            )
        )

        ########################################################
        # If the brain already supplied a useful response,
        # preserve it and report the physical task result.
        ########################################################

        if answer:

            return (
                f"{answer}\n\n"
                f"{computer_result}"
            )

        return computer_result

    ############################################################
    # EXECUTE
    ############################################################

    def execute(
        self,
        command
    ):

        command = str(
            command or ""
        ).strip()

        if not command:

            return (
                "No command received."
            )

        execution_id = (
            self._begin_execution()
        )

        print()
        print(
            "=" * 70
        )

        print(
            "[AIController] COMMAND"
        )

        print(
            command
        )

        print(
            "=" * 70
        )

        ########################################################
        # PRIMARY JARVIS BRAIN
        ########################################################

        brain_response = (
            self._think(
                command
            )
        )

        ########################################################
        # A stop request may arrive while Gemini is thinking.
        #
        # We cannot safely kill a blocking network call, but we
        # MUST discard its result as soon as it returns.
        ########################################################

        if self._is_execution_cancelled(
            execution_id
        ):

            print(
                "[AIController] "
                "Discarding stale brain result."
            )

            return self.INTERRUPTED_RESULT

        ########################################################
        # BRAIN FAILURE
        ########################################################

        if (
            brain_response is None
            or
            not brain_response.success
        ):

            print(
                "[AIController] "
                "Primary brain unavailable."
            )

            if brain_response is not None:

                print(
                    "[AIController] "
                    f"Brain error: "
                    f"{brain_response.error}"
                )

            if self._is_execution_cancelled(
                execution_id
            ):

                return self.INTERRUPTED_RESULT

            return self._legacy_fallback(
                command
            )

        ########################################################
        # MODE
        ########################################################

        mode = str(
            brain_response.mode
            or
            AIBrain.CHAT
        ).upper().strip()

        print(
            "[AIController] "
            f"BRAIN MODE: {mode}"
        )

        ########################################################
        # CHAT
        ########################################################

        if mode == AIBrain.CHAT:

            answer = str(
                brain_response.answer
                or
                ""
            ).strip()

            if answer:

                print(
                    "[AIController] "
                    "NORMAL AI RESPONSE"
                )

                if self._is_execution_cancelled(
                    execution_id
                ):

                    return self.INTERRUPTED_RESULT

                self._speak(
                    answer,
                    execution_id
                )

                if self._is_execution_cancelled(
                    execution_id
                ):

                    return self.INTERRUPTED_RESULT

                return answer

            print(
                "[AIController] "
                "Brain returned an empty answer."
            )

            if self._is_execution_cancelled(
                execution_id
            ):

                return self.INTERRUPTED_RESULT

            return self._legacy_fallback(
                command
            )

        ########################################################
        # COMPUTER
        ########################################################

        if mode == AIBrain.COMPUTER:

            if self._is_execution_cancelled(
                execution_id
            ):

                return self.INTERRUPTED_RESULT

            result = (
                self._execute_computer_goal(
                    brain_response.computer_goal
                )
            )

            if self._is_execution_cancelled(
                execution_id
            ):

                return self.INTERRUPTED_RESULT

            self._speak(
                result,
                execution_id
            )

            if self._is_execution_cancelled(
                execution_id
            ):

                return self.INTERRUPTED_RESULT

            return result

        ########################################################
        # HYBRID
        ########################################################

        if mode == AIBrain.HYBRID:

            if self._is_execution_cancelled(
                execution_id
            ):

                return self.INTERRUPTED_RESULT

            result = (
                self._execute_hybrid(
                    brain_response
                )
            )

            if self._is_execution_cancelled(
                execution_id
            ):

                return self.INTERRUPTED_RESULT

            self._speak(
                result,
                execution_id
            )

            if self._is_execution_cancelled(
                execution_id
            ):

                return self.INTERRUPTED_RESULT

            return result

        ########################################################
        # UNKNOWN MODE
        ########################################################

        print(
            "[AIController] "
            f"Unknown brain mode: {mode}"
        )

        if self._is_execution_cancelled(
            execution_id
        ):

            return self.INTERRUPTED_RESULT

        return self._legacy_fallback(
            command
        )

    ############################################################
    ############################################################
    # LEGACY FALLBACK
    ############################################################

    def _legacy_fallback(
        self,
        command
    ):

        ########################################################
        # LOCAL RESPONDER
        #
        # This is now a FALLBACK, not the primary brain.
        ########################################################

        try:

            local_response = (
                self.localResponder.respond(
                    command
                )
            )

        except Exception as exc:

            print(
                "[AIController] "
                "Local responder error:",
                exc
            )

            local_response = None

        if local_response:

            print(
                "[AIController] "
                "LEGACY LOCAL RESPONSE"
            )

            self._speak(
                local_response
            )

            return local_response

        ########################################################
        # LEGACY ROUTER
        ########################################################

        try:

            response = (
                self.router.route(
                    command
                )
            )

            if (
                not response
                or
                not response.actions
            ):

                message = (
                    "I could not determine "
                    "how to handle that request, sir."
                )

                self._speak(
                    message
                )

                return message

            ####################################################
            # CONVERT
            ####################################################

            actions = []

            for aiAction in (
                response.actions
            ):

                coreAction = (
                    self._toCoreAction(
                        aiAction
                    )
                )

                if coreAction is None:

                    print(
                        "[AIController] "
                        "Unsupported action:",
                        getattr(
                            aiAction,
                            "tool",
                            ""
                        )
                    )

                    continue

                actions.append(
                    coreAction
                )

            if not actions:

                message = (
                    "I understood the request, "
                    "but could not create an "
                    "executable action."
                )

                self._speak(
                    message
                )

                return message

            ####################################################
            # EXECUTION
            ####################################################

            print()
            print(
                "[AIController] "
                "LEGACY EXECUTION"
            )

            for index, action in enumerate(
                actions,
                start=1
            ):

                print(
                    f"  {index}. "
                    f"{action.action.name} "
                    f"{action.parameters}"
                )

            result = (
                self.engine.execute(
                    actions
                )
            )

            ####################################################
            # Do not claim success based only on engine return
            # values. This path is compatibility-only.
            ####################################################

            message = (
                f"Completed "
                f"{len(actions)} action(s), sir."
            )

            self._speak(
                message
            )

            return message

        except Exception as exc:

            print()
            print(
                "[AIController] "
                "Legacy execution error:"
            )

            print(
                exc
            )

            message = (
                f"I encountered an error: {exc}"
            )

            self._speak(
                message
            )

            return message

    ############################################################
    # AI ACTION -> CORE ACTION
    ############################################################

    def _toCoreAction(
        self,
        aiAction
    ):

        if not aiAction:

            return None

        if not hasattr(
            aiAction,
            "tool"
        ):

            return None

        tool = str(
            aiAction.tool
        ).strip().upper()

        actionType = (
            self.actionMap.get(
                tool
            )
        )

        if actionType is None:

            actionType = getattr(
                ActionType,
                tool,
                None
            )

        if actionType is None:

            print(
                "[AIController] "
                f"Unknown tool: {tool}"
            )

            return None

        parameters = (
            aiAction.parameters
            if isinstance(
                aiAction.parameters,
                dict
            )
            else {}
        )

        return CoreAction(
            action=actionType,
            parameters=parameters
        )

    ############################################################
    # INTERRUPT
    ############################################################

    def interrupt(
        self,
        reason="Task interrupted by user."
    ):

        reason = str(
            reason or
            "Task interrupted by user."
        ).strip()

        print()
        print(
            "[AIController] INTERRUPT REQUESTED"
        )

        ########################################################
        # Invalidate the current execution immediately.
        ########################################################

        self._cancel_execution()

        ########################################################
        # Stop current speech immediately.
        ########################################################

        try:

            tts = getattr(
                self,
                "tts",
                None
            )

            stop = getattr(
                tts,
                "stop",
                None
            )

            if callable(
                stop
            ):

                stop()

        except Exception as exc:

            print(
                "[AIController] "
                "TTS interrupt warning:",
                exc
            )

        ########################################################
        # Cancel physical computer execution.
        ########################################################

        try:

            agent = getattr(
                self,
                "localAgent",
                None
            )

            cancel = getattr(
                agent,
                "cancel",
                None
            )

            if callable(
                cancel
            ):

                cancel(
                    reason
                )

        except Exception as exc:

            print(
                "[AIController] "
                "Computer interrupt warning:",
                exc
            )

        return self.INTERRUPTED_RESULT

    ############################################################
    ############################################################
    # RUN COMPATIBILITY
    ############################################################

    def run(
        self,
        command
    ):

        return self.execute(
            command
        )