import json
import re
import threading
import time

from collections import deque
from pathlib import Path
from ai.local_client import LocalAIClient

from automation.executors.engine import AutomationEngine
from automation.services.spreadsheet_service import SpreadsheetService
from automation.file_intelligence import FileIntelligence
from automation.browser_intelligence import BrowserIntelligence

from backend.agent_memory import AgentMemory
from backend.agent_recovery import AgentRecoveryPlanner
from backend.agent_observer import AgentObserver
from backend.agent_policy import AgentPolicy
from backend.agent_state import AgentState
from backend.agent_tools import AgentToolset
from backend.task_planner import TaskPlanner


class ComputerUseAgent:

    ############################################################
    # CONFIGURATION
    ############################################################

    MODEL_NAME = "qwen3-vl:4b-instruct"

    MAX_STEPS = 60

    MAX_HISTORY = 6

    MAX_FAILURES = 3

    ACTION_DELAY = 0.20

    OBSERVATION_DELAY = 0.15

    ############################################################
    # INITIALIZATION
    ############################################################

    def __init__(
        self,
        engine=None,
        ai_client=None
    ):

        self.ai = (
            ai_client
            or LocalAIClient()
        )

        self.engine = (
            engine
            or AutomationEngine()
        )

        self.state = AgentState()

        self.memory = AgentMemory(
            self.state
        )

        self.observer = AgentObserver()

        self.policy = AgentPolicy(
            self.engine
        )

        self.tools = AgentToolset(
            self.engine
        )

        self.planner = TaskPlanner()

        self.recovery = AgentRecoveryPlanner()

        self.sheets = SpreadsheetService()

        ########################################################
        # FILE & FOLDER INTELLIGENCE
        #
        # Read-only discovery/ranking layer. It never performs
        # filesystem mutations; FilesystemExecutor remains the
        # authority for CREATE / MOVE / COPY / RENAME / DELETE.
        ########################################################

        self.file_intelligence = (
            FileIntelligence()
        )

        ########################################################
        # BROWSER INTELLIGENCE
        ########################################################

        self.browser_intelligence = (
            BrowserIntelligence()
        )

        ########################################################
        # LOOP PROTECTION
        ########################################################

        self.recent_actions = deque(
            maxlen=8
        )

        self.failure_count = 0

        self.last_failure = None

        ########################################################
        # TASK STATE
        ########################################################

        self.current_goal = ""

        self.completed_actions = []

        self.failed_actions = []

        ########################################################
        # SEMANTIC ACTION VERIFICATION
        #
        # Executor success only means the input was sent.
        # The next screenshot/model decision must determine
        # whether the intended outcome actually happened.
        ########################################################

        self.last_action = None
        self.last_expected_outcome = ""
        self.last_action_step = None
        self.last_action_result = None
        self.last_action_verified = None
        self.blocked_action_signature = None

        ########################################################
        # COOPERATIVE CANCELLATION
        ########################################################

        self._cancel_event = threading.Event()

        self._cancel_reason = ""

        self.recovery.reset()

        print()

        print(
            "[ComputerAgent] "
            "JARVIS UNIVERSAL COMPUTER KERNEL READY"
        )

        print(
            f"[ComputerAgent] Brain: "
            f"{self.MODEL_NAME}"
        )

    ############################################################
    # SHOULD HANDLE
    ############################################################

    def shouldHandle(
        self,
        command
    ):

        text = str(
            command or ""
        ).strip()

        return bool(
            text
        )

    ############################################################
    # RUN
    ############################################################

    def run(
        self,
        goal
    ):

        goal = str(
            goal or ""
        ).strip()

        if not goal:

            return (
                "No computer task received, sir."
            )

        ########################################################
        # RESET TASK
        ########################################################

        self.current_goal = goal

        self.completed_actions = []

        self.failed_actions = []

        self._filesystem_cache_goal = ""

        self._filesystem_candidates_cache = None

        self.recent_actions.clear()

        self.failure_count = 0

        self.last_failure = None

        self.last_action = None
        self.last_expected_outcome = ""
        self.last_action_step = None
        self.last_action_result = None
        self.last_action_verified = None
        self.blocked_action_signature = None

        self.blocked_action_counts = {}

        self._cancel_event.clear()

        self._cancel_reason = ""

        self.recovery.reset()

        ########################################################
        # FAST FILESYSTEM FIND
        #
        # Requests whose entire objective is simply to locate a
        # file/folder should not require a 60-step visual mission.
        # Use FileIntelligence directly and return the path when
        # confidence is strong.
        ########################################################

        fast_find = (
            self._try_fast_filesystem_find()
        )

        if fast_find is not None:

            return fast_find

        ########################################################
        # STATE
        ########################################################

        try:

            self.state.start(
                goal
            )

        except Exception as exc:

            print(
                "[ComputerAgent] "
                "State start warning:",
                exc
            )

        ########################################################
        # PLAN
        ########################################################

        try:

            stages = (
                self.planner.plan(
                    goal
                )
            )

        except Exception as exc:

            print(
                "[ComputerAgent] "
                "Planner warning:",
                exc
            )

            stages = []

        try:

            self.state.set_stages(
                stages
            )

        except Exception:

            pass

        ########################################################
        # MEMORY
        ########################################################

        try:

            self.memory.record(
                {
                    "type":
                        "TASK_STARTED",

                    "goal":
                        goal,

                    "brain":
                        self.MODEL_NAME
                }
            )

        except Exception:

            pass

        ########################################################
        # HEADER
        ########################################################

        print()

        print(
            "=" * 78
        )

        print(
            "[ComputerAgent] "
            "JARVIS UNIVERSAL COMPUTER MODE"
        )

        print(
            f"[ComputerAgent] Goal: {goal}"
        )

        print(
            f"[ComputerAgent] Model: "
            f"{self.MODEL_NAME}"
        )

        try:

            current_stage = (
                self.state.currentStage()
                or ""
            )

        except Exception:

            current_stage = ""

        if current_stage:

            print(
                "[ComputerAgent] "
                f"Stage: "
                f"{current_stage}"
            )

        print(
            "=" * 78
        )

        ########################################################
        # MAIN AUTONOMOUS LOOP
        ########################################################

        for step in range(
            1,
            self.MAX_STEPS + 1
        ):

            if self.is_cancelled():

                return self._cancel_task()

            try:

                self.state.step = step

            except Exception:

                pass

            ####################################################
            # CURRENT STAGE
            ####################################################

            try:

                current_stage = (
                    self.state.currentStage()
                    or ""
                )

            except Exception:

                current_stage = ""

            print()

            print(
                f"[ComputerAgent] "
                f"STEP {step}/{self.MAX_STEPS}"
            )

            if current_stage:

                print(
                    "[ComputerAgent] "
                    f"CURRENT STAGE: "
                    f"{current_stage}"
                )

            ####################################################
            # OBSERVE
            ####################################################

            screenshot = None

            if self.is_cancelled():

                return self._cancel_task()

            try:

                screenshot = (
                    self._capture_observation()
                )

            except Exception as exc:

                print(
                    "[ComputerAgent] "
                    "Observation error:",
                    exc
                )

                self._record_failure(
                    step,
                    "OBSERVE",
                    {},
                    str(exc)
                )

                time.sleep(
                    self.OBSERVATION_DELAY
                )

                continue

            ####################################################
            # INDEPENDENT VERIFICATION OF PREVIOUS ACTION
            ####################################################

            if self.last_action is not None:

                verification = (
                    self._verify_previous_action(
                        screenshot
                    )
                )

                verified = verification.get(
                    "verified"
                )

                observed_outcome = str(
                    verification.get(
                        "observed_outcome",
                        ""
                    )
                )

                self.last_action_verified = verified

                if verified is False:

                    self._record_semantic_failure(
                        observed_outcome
                    )

                elif verified is True:

                    print(
                        "[ComputerAgent] "
                        "PREVIOUS ACTION VERIFIED BY VISION:"
                    )

                    if observed_outcome:

                        print(
                            observed_outcome
                        )

            ####################################################
            # CONTEXT
            ####################################################

            context = (
                self._build_context()
            )

            ####################################################
            # THINK
            ####################################################

            try:

                decision = (
                    self.ai.vision_json(
                        screenshot,
                        self._build_prompt(
                            goal,
                            step,
                            context
                        )
                    )
                )

                if self.is_cancelled():

                    self._cleanup_observation(
                        screenshot
                    )

                    return self._cancel_task(
                        "Task interrupted while reasoning."
                    )

            except Exception as exc:

                print()

                print(
                    "[ComputerAgent] "
                    "LOCAL BRAIN ERROR:"
                )

                print(exc)

                self._record_failure(
                    step,
                    "THINK",
                    {},
                    str(exc)
                )

                self._cleanup_observation(
                    screenshot
                )

                time.sleep(
                    self.OBSERVATION_DELAY
                )

                continue

            ####################################################
            # CLEAN TEMP SCREENSHOT
            ####################################################

            self._cleanup_observation(
                screenshot
            )

            ####################################################
            # NORMALIZE MODEL RESPONSE
            ####################################################

            decision = (
                self._normalize_decision(
                    decision
                )
            )

            status = (
                decision["status"]
            )

            reason = (
                decision["reason"]
            )

            print(
                "[ComputerAgent] STATUS:",
                status
            )

            print(
                "[ComputerAgent] REASON:",
                reason
            )

            ####################################################
            # DONE
            ####################################################

            if status == "DONE":

                ################################################
                # IMPORTANT:
                #
                # Never trust a single model response as proof
                # of completion.
                #
                # Capture the computer again and ask Qwen to
                # verify the ENTIRE original goal.
                ################################################

                verified = (
                    self._verify_completion(
                        goal
                    )
                )

                if not verified:

                    print()

                    print(
                        "[ComputerAgent] "
                        "COMPLETION VERIFICATION FAILED"
                    )

                    self._record_failure(
                        step,
                        "VERIFY_COMPLETION",
                        {},
                        (
                            "Model claimed DONE but "
                            "final verification failed."
                        )
                    )

                    time.sleep(
                        self.OBSERVATION_DELAY
                    )

                    continue

                message = str(
                    decision.get(
                        "message",
                        "Task completed, sir."
                    )
                )

                self._complete_task(
                    goal,
                    step,
                    message
                )

                return message

            ####################################################
            # BLOCKED
            ####################################################

            if status == "BLOCKED":

                message = str(
                    decision.get(
                        "message",
                        "I could not safely complete "
                        "that task, sir."
                    )
                )

                try:

                    self.state.fail(
                        message
                    )

                except Exception:

                    pass

                return message

            ####################################################
            # ACTIONS
            ####################################################

            actions = (
                decision.get(
                    "actions",
                    []
                )
            )

            if not isinstance(
                actions,
                list
            ):

                actions = []

            ####################################################
            # UNIVERSAL NORMALIZATION
            ####################################################

            actions = (
                self._normalize_actions(
                    actions
                )
            )

            if not actions:

                self._record_no_action(
                    step,
                    reason
                )

                time.sleep(
                    self.OBSERVATION_DELAY
                )

                continue

            ####################################################
            # ONE ACTION PER OBSERVATION CYCLE
            ####################################################

            action = actions[0]

            ####################################################
            # RECOVERY PLANNER GATE
            ####################################################

            if self.recovery.is_blocked(
                action
            ):

                print()
                print(
                    "[ComputerAgent] "
                    "RECOVERY PLANNER BLOCKED ROUTE:"
                )
                print(action)

                self._record_failure(
                    step,
                    action.get("tool", ""),
                    action.get("parameters", {}),
                    (
                        "Recovery planner rejected a previously "
                        "failed route. Choose a different strategy."
                    )
                )

                time.sleep(
                    self.OBSERVATION_DELAY
                )

                continue

            ####################################################
            # SEMANTIC LOOP PROTECTION
            #
            # If the immediately previous attempt of this exact
            # action failed semantically, do not blindly send it
            # again. The model must choose another route.
            #
            # WAIT is exempt because waiting can legitimately be
            # repeated while an application is loading.
            ####################################################

            action_signature = (
                self._action_signature(
                    action.get(
                        "tool",
                        ""
                    ),
                    action.get(
                        "parameters",
                        {}
                    )
                )
            )

            if (
                self.blocked_action_signature
                and
                action_signature
                ==
                self.blocked_action_signature
                and
                action.get(
                    "tool",
                    ""
                ).upper().strip()
                !=
                "WAIT"
            ):

                blocked_count = (
                    self.blocked_action_counts.get(
                        action_signature,
                        0,
                    )
                    + 1
                )

                self.blocked_action_counts[
                    action_signature
                ] = blocked_count

                print()
                print(
                    "[ComputerAgent] "
                    "ALTERNATIVE ROUTE REQUIRED:"
                )

                print(
                    "[ComputerAgent] "
                    f"Blocked signature proposed again "
                    f"({blocked_count}/2)."
                )

                self._record_failure(
                    step,
                    action.get(
                        "tool",
                        ""
                    ),
                    action.get(
                        "parameters",
                        {}
                    ),
                    (
                        "The previous identical action "
                        "did not achieve its expected outcome. "
                        "A different strategy is required."
                    )
                )

                ################################################
                # DETERMINISTIC RECOVERY HARD-STOP
                ################################################

                if blocked_count >= 2:

                    message = (
                        "I could not safely complete the task "
                        "because the same computer action kept "
                        "failing. I stopped instead of repeating it."
                    )

                    print()
                    print(
                        "[ComputerAgent] "
                        "RECOVERY HARD-STOP"
                    )

                    try:

                        self.state.fail(
                            message
                        )

                    except Exception:

                        pass

                    return message

                time.sleep(
                    self.OBSERVATION_DELAY
                )

                continue

            ####################################################
            # LOOP PROTECTION
            ####################################################

            if self._is_repeated_failure(
                action
            ):

                print()

                print(
                    "[ComputerAgent] "
                    "REPEATED FAILED ACTION BLOCKED:"
                )

                print(
                    action
                )

                self._record_failure(
                    step,
                    action.get(
                        "tool",
                        ""
                    ),
                    action.get(
                        "parameters",
                        {}
                    ),
                    (
                        "Same action has already "
                        "failed repeatedly."
                    )
                )

                time.sleep(
                    self.OBSERVATION_DELAY
                )

                continue

            ####################################################
            # EXECUTE
            ####################################################

            expected_outcome = str(
                decision.get(
                    "expected_outcome",
                    ""
                )
            ).strip()

            if not expected_outcome:

                expected_outcome = (
                    "A visible or observable computer-state "
                    "change that advances the user's goal."
                )

            self.last_action = {
                "tool":
                    action.get(
                        "tool",
                        ""
                    ),

                "parameters":
                    dict(
                        action.get(
                            "parameters",
                            {}
                        )
                    )
            }

            self.last_expected_outcome = (
                expected_outcome
            )

            self.last_action_step = step
            self.last_action_verified = None
            self.last_action_result = None

            self.blocked_action_signature = None

            print(
                "[ComputerAgent] EXPECTED OUTCOME:",
                expected_outcome
            )

            if self.is_cancelled():

                return self._cancel_task(
                    "Task interrupted before computer action."
                )

            result = (
                self._execute_tool(
                    action
                )
            )

            self.last_action_result = result

            if self.is_cancelled():

                return self._cancel_task(
                    "Task interrupted after computer action."
                )

            success = bool(
                result.get(
                    "success",
                    False
                )
            )

            ####################################################
            # RECORD RESULT
            ####################################################

            self._record_step(
                step,
                (
                    f"{reason} | "
                    f"Expected outcome: {expected_outcome}"
                ),
                action,
                result,
                success
            )

            ####################################################
            # SUCCESS
            ####################################################

            if success:

                self.failure_count = 0

                # Keep the previous action pending for semantic
                # verification on the next screenshot.
                self.completed_actions.append(
                    action
                )

                self.recent_actions.append(
                    {
                        "tool":
                            action.get(
                                "tool",
                                ""
                            ),

                        "parameters":
                            action.get(
                                "parameters",
                                {}
                            ),

                        "success":
                            True
                    }
                )

                ################################################
                # STAGE PROGRESSION
                #
                # Qwen explicitly tells the kernel when the
                # current planner stage has been completed.
                ################################################

                if decision.get(
                    "stage_complete",
                    False
                ):

                    try:

                        advanced = (
                            self.state.advanceStage()
                        )

                        if advanced:

                            next_stage = (
                                self.state.currentStage()
                                or ""
                            )

                            print(
                                "[ComputerAgent] "
                                "STAGE ADVANCED:"
                            )

                            if next_stage:

                                print(
                                    next_stage
                                )

                            else:

                                print(
                                    "[ComputerAgent] "
                                    "No remaining planner stage."
                                )

                    except Exception as exc:

                        print(
                            "[ComputerAgent] "
                            "Stage advancement warning:",
                            exc
                        )

            ####################################################
            # FAILURE
            ####################################################

            else:

                error_text = str(
                    result.get(
                        "error",
                        "Action failed."
                    )
                )

                self.recovery.record_failure(
                    action,
                    error_text,
                    self.recovery.classify_executor_failure(
                        error_text
                    )
                )

                self._record_failed_action(
                    action,
                    result
                )

            ####################################################
            # WAIT FOR COMPUTER
            ####################################################

            time.sleep(
                self.ACTION_DELAY
            )

        ########################################################
        # MAXIMUM STEP LIMIT
        ########################################################

        try:

            self.state.fail(
                "Maximum autonomous "
                "execution steps reached."
            )

        except Exception:

            pass

        return (
            "I reached the autonomous execution "
            "limit before verifying completion, sir."
        )

    ############################################################
    # CANCELLATION
    ############################################################

    def cancel(
        self,
        reason="Task interrupted by user."
    ):
        """
        Request cooperative cancellation of the current task.

        This is thread-safe and intentionally non-blocking.
        """

        self._cancel_reason = str(
            reason
            or
            "Task interrupted by user."
        ).strip()

        self._cancel_event.set()

        print()
        print(
            "[ComputerAgent] "
            "CANCELLATION REQUESTED"
        )

        print(
            f"[ComputerAgent] {self._cancel_reason}"
        )

        ########################################################
        # Give the engine an opportunity to cancel an active
        # executor if it exposes an interrupt() method.
        ########################################################

        try:

            interrupt = getattr(
                self.engine,
                "interrupt",
                None
            )

            if callable(
                interrupt
            ):

                interrupt()

        except Exception as exc:

            print(
                "[ComputerAgent] "
                "Engine interrupt warning:",
                exc
            )

    def is_cancelled(
        self
    ):

        return self._cancel_event.is_set()

    def clear_cancel(
        self
    ):

        self._cancel_event.clear()

        self._cancel_reason = ""

    def _cancel_task(
        self,
        message=None
    ):

        message = str(
            message
            or
            self._cancel_reason
            or
            "Task interrupted by user."
        ).strip()

        try:

            self.memory.record(
                {
                    "type":
                        "TASK_CANCELLED",

                    "goal":
                        self.current_goal,

                    "step":
                        getattr(
                            self.state,
                            "step",
                            0
                        ),

                    "message":
                        message
                }
            )

        except Exception:
            pass

        try:

            self.state.fail(
                message
            )

        except Exception:
            pass

        print()
        print(
            "=" * 78
        )

        print(
            "[ComputerAgent] "
            "TASK INTERRUPTED"
        )

        print(
            f"[ComputerAgent] {message}"
        )

        print(
            "=" * 78
        )

        return (
            "Task interrupted, sir."
        )

    ############################################################
    # OBSERVATION
    ############################################################

    def _capture_observation(
        self
    ):

        ########################################################
        # Prefer temporary observation.
        #
        # LocalAIClient can consume the temporary screenshot
        # path directly.
        ########################################################

        capture_temp = getattr(
            self.observer,
            "capture_to_temp",
            None
        )

        if callable(
            capture_temp
        ):

            return capture_temp()

        ########################################################
        # Compatibility with older observer.
        ########################################################

        capture = getattr(
            self.observer,
            "capture",
            None
        )

        if callable(
            capture
        ):

            return capture()

        raise RuntimeError(
            "AgentObserver has no capture method."
        )

    ############################################################
    # CLEANUP OBSERVATION
    ############################################################

    def _cleanup_observation(
        self,
        screenshot
    ):

        if not screenshot:

            return

        ########################################################
        # The current observer exposes delete_temp().
        ########################################################

        delete_temp = getattr(
            self.observer,
            "delete_temp",
            None
        )

        if callable(
            delete_temp
        ):

            try:

                delete_temp(
                    screenshot
                )

                return

            except Exception:

                pass

        ########################################################
        # If the observer returned raw bytes there is nothing
        # to delete.
        ########################################################

    ############################################################
    # FILESYSTEM OPERATION VERIFICATION
    ############################################################

    def _verify_filesystem_operation(
        self,
        tool,
        parameters,
    ):

        """
        Deterministically verify filesystem mutations from the
        real filesystem state.
        """

        tool = str(
            tool or ""
        ).upper().strip()

        params = dict(
            parameters or {}
        )

        def as_path(
            value
        ):

            value = str(
                value or ""
            ).strip()

            if not value:
                return None

            try:
                resolved = self.tools.filesystem._resolve(
                    value
                )

                return Path(
                    resolved
                )

            except Exception:

                return Path(
                    value
                )

        source = as_path(
            params.get(
                "source"
            )
        )

        destination = as_path(
            params.get(
                "destination"
            )
        )

        path = as_path(
            params.get(
                "path"
            )
        )

        ########################################################
        # CREATE FILE
        ########################################################

        if tool == "CREATE_FILE":

            target = path

            verified = bool(
                target
                and
                target.exists()
                and
                target.is_file()
            )

            return {
                "verified":
                    verified,

                "reason":
                    (
                        f"File verified at {target}"
                        if verified
                        else
                        f"Created file was not found at {target}"
                    ),
            }

        ########################################################
        # CREATE FOLDER
        ########################################################

        if tool == "CREATE_FOLDER":

            target = path

            if target is None:

                name = str(
                    params.get(
                        "name",
                        ""
                    )
                    or
                    ""
                ).strip()

                if name:

                    target = as_path(
                        f"Desktop/{name}"
                    )

            verified = bool(
                target
                and
                target.exists()
                and
                target.is_dir()
            )

            return {
                "verified":
                    verified,

                "reason":
                    (
                        f"Folder verified at {target}"
                        if verified
                        else
                        f"Created folder was not found at {target}"
                    ),
            }

        ########################################################
        # DELETE FILE / FOLDER
        ########################################################

        if tool in {
            "DELETE_FILE",
            "DELETE_FOLDER",
        }:

            target = (
                path
                or
                source
            )

            verified = bool(
                target
                and
                not target.exists()
            )

            return {
                "verified":
                    verified,

                "reason":
                    (
                        f"Deletion verified: {target}"
                        if verified
                        else
                        f"Target still exists: {target}"
                    ),
            }

        ########################################################
        # COPY
        ########################################################

        if tool == "COPY":

            if source is None or destination is None:

                return {
                    "verified":
                        False,

                    "reason":
                        "Copy verification lacks source or destination.",
                }

            target = destination

            if (
                destination.exists()
                and
                destination.is_dir()
            ):

                target = (
                    destination
                    /
                    source.name
                )

            verified = bool(
                source.exists()
                and
                target.exists()
            )

            return {
                "verified":
                    verified,

                "reason":
                    (
                        f"Copy verified at {target}"
                        if verified
                        else
                        f"Copy target was not found: {target}"
                    ),
            }

        ########################################################
        # MOVE
        ########################################################

        if tool == "MOVE":

            if source is None or destination is None:

                return {
                    "verified":
                        False,

                    "reason":
                        "Move verification lacks source or destination.",
                }

            target = destination

            if (
                destination.exists()
                and
                destination.is_dir()
            ):

                target = (
                    destination
                    /
                    source.name
                )

            verified = bool(
                not source.exists()
                and
                target.exists()
            )

            return {
                "verified":
                    verified,

                "reason":
                    (
                        f"Move verified at {target}"
                        if verified
                        else
                        (
                            "Move verification failed: "
                            f"source={source}, target={target}"
                        )
                    ),
            }

        ########################################################
        # RENAME
        ########################################################

        if tool == "RENAME":

            if source is None:

                return {
                    "verified":
                        False,

                    "reason":
                        "Rename verification lacks source.",
                }

            new_name = str(
                params.get(
                    "new_name",
                    params.get(
                        "name",
                        ""
                    )
                )
                or
                ""
            ).strip()

            if not new_name:

                return {
                    "verified":
                        False,

                    "reason":
                        "Rename verification lacks new_name.",
                }

            target = (
                source.with_name(
                    new_name
                )
            )

            verified = bool(
                not source.exists()
                and
                target.exists()
            )

            return {
                "verified":
                    verified,

                "reason":
                    (
                        f"Rename verified at {target}"
                        if verified
                        else
                        f"Renamed target was not found: {target}"
                    ),
            }

        return {
            "verified":
                None,

            "reason":
                "Not a filesystem mutation.",
        }

    ############################################################
    # FINAL COMPLETION VERIFICATION
    ############################################################

    def _verify_completion(
        self,
        goal
    ):

        screenshot = None

        try:

            screenshot = (
                self._capture_observation()
            )

        except Exception as exc:

            print(
                "[ComputerAgent] "
                "Final observation error:",
                exc
            )

            return False

        try:

            prompt = f"""
You are the FINAL VERIFICATION SYSTEM for JARVIS.

The user originally requested:

============================================================
USER GOAL
============================================================

{goal}

============================================================
YOUR TASK
============================================================

Look at the current computer screen.

Determine whether the ENTIRE original user goal is
actually complete.

Do NOT judge based on what JARVIS intended to do.

Judge ONLY based on visible evidence and the current
computer state.

Ask yourself:

1. Did every required part of the user's goal happen?
2. Is the final requested result actually present?
3. Is there any unfinished part?
4. Is the correct application/window visible?
5. Is the expected data/text/file/result actually present?
6. Is there evidence that the task is still in progress?

If ANY required part is incomplete or uncertain:

{{
    "verified": false,
    "reason": "Why the complete goal is not visibly verified."
}}

If the ENTIRE goal is clearly complete:

{{
    "verified": true,
    "reason": "Visible evidence proving the entire goal is complete."
}}

IMPORTANT:

- Do not assume.
- Do not guess.
- Do not rely on previous actions.
- The current screen is the source of truth.
- Partial completion is NOT completion.

Return ONLY valid JSON.
""".strip()

            verification = (
                self.ai.vision_json(
                    screenshot,
                    prompt
                )
            )

            if not isinstance(
                verification,
                dict
            ):

                return False

            verified = (
                verification.get(
                    "verified",
                    False
                )
            )

            reason = str(
                verification.get(
                    "reason",
                    ""
                )
            )

            print(
                "[ComputerAgent] "
                "FINAL VERIFICATION:",
                verified
            )

            print(
                "[ComputerAgent] "
                "VERIFICATION REASON:",
                reason
            )

            return bool(
                verified
            )

        except Exception as exc:

            print(
                "[ComputerAgent] "
                "Final verification error:",
                exc
            )

            return False

        finally:

            self._cleanup_observation(
                screenshot
            )

    ############################################################
    # INDEPENDENT PREVIOUS-ACTION VERIFICATION
    ############################################################

    def _verify_previous_action(
        self,
        screenshot
    ):

        if self.last_action is None:

            return {
                "verified": None,
                "observed_outcome": ""
            }

        expected = str(
            self.last_expected_outcome
            or ""
        ).strip()

        if not expected:

            return {
                "verified": None,
                "observed_outcome": "No expected outcome was recorded."
            }

        action_text = json.dumps(
            self.last_action,
            ensure_ascii=False,
            separators=(
                ",",
                ":"
            ),
            default=str
        )

        prompt = f"""
You are JARVIS ACTION VERIFIER.

You are NOT choosing the next action.
You are NOT planning the task.
You are NOT allowed to use execution logs, prior claims,
or assumptions.

Use ONLY the CURRENT SCREENSHOT provided to you.

PREVIOUS ACTION:
{action_text}

EXPECTED OUTCOME:
{expected}

Determine whether the expected outcome is actually
visible or otherwise clearly observable on the current
screen.

Rules:
- Do not assume success because the action was sent.
- Do not use the executor result as evidence.
- Do not use previous model reasoning as evidence.
- If the expected outcome is not visible, return false.
- If the screen is genuinely ambiguous, return false.
- Only return true when the current screenshot provides
  clear evidence that the expected outcome happened.

Return ONLY valid JSON:

{{
    "verified": true or false,
    "observed_outcome": "Brief description of what the current screen shows."
}}
""".strip()

        try:

            result = (
                self.ai.vision_json(
                    screenshot,
                    prompt
                )
            )

            if not isinstance(
                result,
                dict
            ):

                return {
                    "verified": False,
                    "observed_outcome":
                        "Verifier returned no usable result."
                }

            verified = result.get(
                "verified",
                False
            )

            observed = str(
                result.get(
                    "observed_outcome",
                    ""
                )
            ).strip()

            if verified is not True:

                verified = False

            print(
                "[ComputerAgent] "
                "ACTION VERIFIER:",
                verified
            )

            if observed:

                print(
                    "[ComputerAgent] "
                    "OBSERVED OUTCOME:",
                    observed
                )

            return {
                "verified":
                    verified,

                "observed_outcome":
                    observed
            }

        except Exception as exc:

            print(
                "[ComputerAgent] "
                "Action verifier error:",
                exc
            )

            return {
                "verified": False,
                "observed_outcome":
                    "Independent visual verification failed."
            }

    ############################################################
    # DECISION NORMALIZATION
    ############################################################

    def _normalize_decision(
        self,
        decision
    ):

        ########################################################
        # Invalid model response
        ########################################################

        if not isinstance(
            decision,
            dict
        ):

            return {
                "status":
                    "CONTINUE",

                "reason":
                    "Model returned no usable decision.",

                "message":
                    "",

                "expected_outcome":
                    "",

                "previous_action_verified":
                    None,

                "observed_outcome":
                    "",

                "stage_complete":
                    False,

                "actions":
                    []
            }

        ########################################################
        # STATUS
        ########################################################

        status = str(
            decision.get(
                "status",
                "CONTINUE"
            )
        ).upper().strip()

        ########################################################
        # Legacy format compatibility
        ########################################################

        if (
            "done" in decision
            and
            "status" not in decision
        ):

            if decision.get(
                "done"
            ) is True:

                status = "DONE"

            else:

                status = "CONTINUE"

        if status not in {
            "CONTINUE",
            "DONE",
            "BLOCKED"
        }:

            status = "CONTINUE"

        ########################################################
        # ACTIONS
        ########################################################

        actions = decision.get(
            "actions",
            None
        )

        ########################################################
        # Legacy single action
        ########################################################

        if actions is None:

            legacy_action = (
                decision.get(
                    "action"
                )
            )

            if isinstance(
                legacy_action,
                dict
            ):

                actions = [
                    legacy_action
                ]

            else:

                actions = []

        ########################################################
        # Dict -> list
        ########################################################

        if isinstance(
            actions,
            dict
        ):

            actions = [
                actions
            ]

        if not isinstance(
            actions,
            list
        ):

            actions = []

        ########################################################
        # Clean actions
        ########################################################

        clean = []

        for item in actions:

            if not isinstance(
                item,
                dict
            ):

                continue

            raw_tool = str(
                item.get(
                    "tool",
                    ""
                )
            ).upper().strip()

            tool = self.recovery.normalize_tool(
                raw_tool
            )

            if not tool:

                continue

            parameters = item.get(
                "parameters",
                {}
            )

            if not isinstance(
                parameters,
                dict
            ):

                parameters = {}

            parameters = dict(parameters)

            ####################################################
            # Browser natural-language normalization
            ####################################################

            if tool in {
                "OPEN_URL",
                "SEARCH_WEB",
            }:

                url_value = str(
                    parameters.get(
                        "url",
                        ""
                    )
                    or ""
                ).strip()

                if tool == "OPEN_URL":

                    browser_match = re.search(
                        r"\b(?:on|using|in)\s+"
                        r"(chrome|google chrome|edge|microsoft edge|"
                        r"firefox|mozilla firefox|opera)\b",
                        url_value,
                        flags=re.IGNORECASE,
                    )

                    if browser_match:

                        parameters[
                            "browser"
                        ] = (
                            self.browser_intelligence.normalize_browser(
                                browser_match.group(1)
                            )
                        )

                if tool == "SEARCH_WEB":

                    query_value = str(
                        parameters.get(
                            "query",
                            parameters.get(
                                "search_query",
                                parameters.get(
                                    "text",
                                    ""
                                )
                            )
                        )
                        or ""
                    ).strip()

                    youtube_match = re.search(
                        r"\s+(?:on|in)\s+youtube\s*$",
                        query_value,
                        flags=re.IGNORECASE,
                    )

                    if youtube_match:

                        query_value = re.sub(
                            r"\s+(?:on|in)\s+youtube\s*$",
                            "",
                            query_value,
                            flags=re.IGNORECASE,
                        ).strip()

                        parameters[
                            "query"
                        ] = query_value

                        parameters[
                            "engine"
                        ] = "youtube"

            # Universal keyboard normalization.
            # Common model output like PRESS_KEY {"keys":["ctrl","s"]}
            # is converted into the existing HOTKEY contract.
            if tool == "PRESS_KEY" and "keys" in parameters:

                keys = parameters.get("keys")

                if isinstance(keys, (list, tuple)):

                    cleaned_keys = [
                        str(key).strip().lower()
                        for key in keys
                        if str(key).strip()
                    ]

                    if len(cleaned_keys) > 1:

                        tool = "HOTKEY"

                        parameters = {
                            "keys": cleaned_keys
                        }

                    elif len(cleaned_keys) == 1:

                        parameters = {
                            "key": cleaned_keys[0]
                        }

                    else:

                        parameters = {}

            # Universal single-click alias normalization.
            if tool == "LEFT_CLICK" and "target" in parameters and not {"x", "y"}.issubset(parameters):

                parameters.pop("target", None)

            clean.append(
                {
                    "tool":
                        tool,

                    "parameters":
                        parameters
                }
            )

        ########################################################
        # Completion message
        ########################################################

        message = str(
            decision.get(
                "message",
                (
                    "Task completed, sir."
                    if status == "DONE"
                    else ""
                )
            )
        )

        ########################################################
        # EXPECTED / OBSERVED OUTCOME
        ########################################################

        expected_outcome = str(
            decision.get(
                "expected_outcome",
                ""
            )
        ).strip()

        observed_outcome = str(
            decision.get(
                "observed_outcome",
                ""
            )
        ).strip()

        previous_action_verified = (
            decision.get(
                "previous_action_verified",
                None
            )
        )

        if previous_action_verified not in {
            True,
            False
        }:

            previous_action_verified = None

        ########################################################
        # Stage completion
        ########################################################

        stage_complete = bool(
            decision.get(
                "stage_complete",
                False
            )
        )

        return {
            "status":
                status,

            "reason":
                str(
                    decision.get(
                        "reason",
                        ""
                    )
                ),

            "message":
                message,

            "expected_outcome":
                expected_outcome,

            "previous_action_verified":
                previous_action_verified,

            "observed_outcome":
                observed_outcome,

            "stage_complete":
                stage_complete,

            "actions":
                clean
        }

    ############################################################
    # SEMANTIC ACTION FAILURE
    ############################################################

    def _record_semantic_failure(
        self,
        observed_outcome
    ):

        if self.last_action is None:

            return

        tool = str(
            self.last_action.get(
                "tool",
                ""
            )
        ).upper().strip()

        parameters = self.last_action.get(
            "parameters",
            {}
        )

        signature = (
            self._action_signature(
                tool,
                parameters
            )
        )

        expected = (
            self.last_expected_outcome
            or
            "Expected computer-state change."
        )

        observed = (
            str(
                observed_outcome
                or
                "Expected outcome was not observed."
            )
        )

        semantic_result = {
            "success":
                False,

            "error":
                (
                    "Semantic verification failed. "
                    f"Expected: {expected} "
                    f"Observed: {observed}"
                )
        }

        self._record_failed_action(
            self.last_action,
            semantic_result
        )

        self.recovery.record_failure(
            self.last_action,
            semantic_result.get("error", ""),
            "semantic"
        )

        self.blocked_action_signature = signature

        print()
        print(
            "[ComputerAgent] "
            "SEMANTIC ACTION FAILURE:"
        )

        print(
            "[ComputerAgent] Expected:",
            expected
        )

        print(
            "[ComputerAgent] Observed:",
            observed
        )

        print(
            "[ComputerAgent] "
            "Same action is blocked until a different "
            "strategy is chosen."
        )

    ############################################################
    # ACTION NORMALIZATION
    ############################################################

    def _normalize_actions(
        self,
        actions
    ):

        clean = []

        for item in actions:

            if not isinstance(
                item,
                dict
            ):

                continue

            tool = str(
                item.get(
                    "tool",
                    ""
                )
            ).upper().strip()

            if not tool:

                continue

            parameters = item.get(
                "parameters",
                {}
            )

            if not isinstance(
                parameters,
                dict
            ):

                parameters = {}

            ####################################################
            # AgentToolset owns parameter normalization.
            ####################################################

            try:

                parameters = (
                    self.tools.normalize_parameters(
                        tool,
                        parameters
                    )
                )

            except Exception as exc:

                print(
                    "[ComputerAgent] "
                    "Parameter normalization warning:",
                    exc
                )

            ####################################################
            # FILESYSTEM TARGET RESOLUTION
            ####################################################

            if tool in {
                "COPY",
                "MOVE",
                "RENAME",
                "DELETE_FILE",
                "DELETE_FOLDER",
                "OPEN_FILE",
            }:

                try:

                    resolution = (
                        self._resolve_filesystem_targets(
                            tool,
                            parameters,
                        )
                    )

                    parameters = dict(
                        resolution.get(
                            "parameters",
                            parameters,
                        )
                    )

                    candidates = resolution.get(
                        "candidates",
                        [],
                    )

                    if candidates:

                        parameters[
                            "_resolution_candidates"
                        ] = candidates

                    parameters[
                        "_filesystem_ambiguity"
                    ] = (
                        self._check_filesystem_ambiguity(
                            parameters
                        )
                    )

                except Exception as exc:

                    print(
                        "[ComputerAgent] "
                        "Filesystem resolution warning:",
                        exc
                    )

            clean.append(
                {
                    "tool":
                        tool,

                    "parameters":
                        parameters
                }
            )

        return clean

    ############################################################
    # EXECUTE UNIVERSAL TOOL
    ############################################################

    def _execute_tool(
        self,
        action
    ):

        if not isinstance(
            action,
            dict
        ):

            return {
                "success":
                    False,

                "error":
                    "Invalid action object."
            }

        tool = str(
            action.get(
                "tool",
                ""
            )
        ).upper().strip()

        parameters = action.get(
            "parameters",
            {}
        )

        if not isinstance(
            parameters,
            dict
        ):

            parameters = {}

        ########################################################
        # FILESYSTEM AMBIGUITY GUARD
        ########################################################

        if tool in {
            "COPY",
            "MOVE",
            "RENAME",
            "DELETE_FILE",
            "DELETE_FOLDER",
        }:

            ambiguity = parameters.get(
                "_filesystem_ambiguity",
                {},
            )

            status = str(
                ambiguity.get(
                    "status",
                    "",
                )
                or
                ""
            ).upper()

            if status in {
                "AMBIGUOUS",
                "NOT_FOUND",
            }:

                print()
                print(
                    "[ComputerAgent] "
                    "FILESYSTEM ACTION BLOCKED"
                )

                print(
                    ambiguity.get(
                        "reason",
                        "Filesystem target could not be resolved safely.",
                    )
                )

                return {
                    "success":
                        False,

                    "blocked":
                        True,

                    "error":
                        ambiguity.get(
                            "reason",
                            "Filesystem target could not be resolved safely.",
                        ),

                    "candidates":
                        ambiguity.get(
                            "candidates",
                            [],
                        ),
                }

        print()

        print(
            "[ComputerAgent] ACTION:",
            tool
        )

        print(
            "[ComputerAgent] PARAMETERS:",
            parameters
        )

        ########################################################
        # INTERNAL MEMORY ACTIONS
        ########################################################

        if tool == "RECORD":

            try:

                data = parameters.get(
                    "data",
                    parameters
                )

                self.memory.record(
                    data
                )

                return {
                    "success":
                        True,

                    "result":
                        "recorded"
                }

            except Exception as exc:

                return {
                    "success":
                        False,

                    "error":
                        str(exc)
                }

        ########################################################
        # REMEMBER
        ########################################################

        if tool == "REMEMBER":

            try:

                key = (
                    parameters.get(
                        "key",
                        ""
                    )
                )

                value = (
                    parameters.get(
                        "value",
                        ""
                    )
                )

                self.memory.remember(
                    key,
                    value
                )

                return {
                    "success":
                        True,

                    "result":
                        "remembered"
                }

            except Exception as exc:

                return {
                    "success":
                        False,

                    "error":
                        str(exc)
                }

        ########################################################
        # CREATE SPREADSHEET
        ########################################################

        if tool == "CREATE_SPREADSHEET":

            try:

                filename = parameters.get(
                    "filename",
                    "jarvis_results.xlsx"
                )

                columns = parameters.get(
                    "columns",
                    []
                )

                path = (
                    self.sheets.create(
                        filename,
                        columns
                    )
                )

                self.state.variables[
                    "spreadsheet"
                ] = path

                self.memory.artifact(
                    path
                )

                self.memory.remember(
                    "spreadsheet",
                    path
                )

                return {
                    "success":
                        True,

                    "path":
                        path
                }

            except Exception as exc:

                return {
                    "success":
                        False,

                    "error":
                        str(exc)
                }

        ########################################################
        # APPEND SPREADSHEET
        ########################################################

        if tool == "APPEND_SPREADSHEET":

            try:

                path = (
                    parameters.get(
                        "path"
                    )
                    or
                    self.state.variables.get(
                        "spreadsheet"
                    )
                )

                if not path:

                    return {
                        "success":
                            False,

                        "error":
                            "No spreadsheet exists."
                    }

                path = (
                    self.sheets.append(
                        path,

                        parameters.get(
                            "row",
                            {}
                        ),

                        parameters.get(
                            "columns"
                        )
                    )
                )

                return {
                    "success":
                        True,

                    "path":
                        path
                }

            except Exception as exc:

                return {
                    "success":
                        False,

                    "error":
                        str(exc)
                }

        ########################################################
        # FINISH
        ########################################################

        if tool == "FINISH":

            message = str(
                parameters.get(
                    "message",
                    "Task completed, sir."
                )
            )

            try:

                self.state.complete()

            except Exception:

                pass

            return {
                "success":
                    True,

                "result":
                    message
            }

        ########################################################
        # POLICY
        ########################################################

        try:

            valid, policy_reason = (
                self.policy.validate(
                    tool,
                    parameters
                )
            )

        except Exception as exc:

            return {
                "success":
                    False,

                "error":
                    str(exc)
            }

        if not valid:

            return {
                "success":
                    False,

                "error":
                    (
                        "Policy rejected action: "
                        f"{policy_reason}"
                    )
            }

        ########################################################
        # UNIVERSAL TOOLSET
        ########################################################

        try:

            core_action = (
                self.tools.core(
                    tool,
                    parameters
                )
            )

        except Exception as exc:

            return {
                "success":
                    False,

                "error":
                    str(exc)
            }

        if core_action is None:

            return {
                "success":
                    False,

                "error":
                    (
                        "Unsupported computer "
                        f"action: {tool}"
                    )
            }

        ########################################################
        # EXECUTE
        ########################################################

        try:

            result = (
                self.engine.executeAction(
                    core_action
                )
            )

            success = (
                result is not False
            )

            filesystem_tools = {
                "CREATE_FILE",
                "CREATE_FOLDER",
                "DELETE_FILE",
                "DELETE_FOLDER",
                "COPY",
                "MOVE",
                "RENAME",
            }

            if tool in filesystem_tools:

                verification = (
                    self._verify_filesystem_operation(
                        tool,
                        parameters,
                    )
                )

                return {
                    "success":
                        (
                            success
                            and
                            verification.get(
                                "verified",
                                False,
                            ) is True
                        ),

                    "verified":
                        verification.get(
                            "verified",
                            False,
                        ),

                    "verification_reason":
                        verification.get(
                            "reason",
                            "",
                        ),

                    "result":
                        self._safe_result(
                            result
                        ),
                }

            return {
                "success":
                    success,

                "result":
                    self._safe_result(
                        result
                    )
            }

        except Exception as exc:

            print()

            print(
                "[ComputerAgent] "
                "EXECUTION ERROR:",
                exc
            )

            return {
                "success":
                    False,

                "error":
                    str(exc)
            }

    ############################################################
    # FAILURE DETECTION
    ############################################################

    def _is_repeated_failure(
        self,
        action
    ):

        tool = str(
            action.get(
                "tool",
                ""
            )
        ).upper().strip()

        parameters = action.get(
            "parameters",
            {}
        )

        signature = (
            self._action_signature(
                tool,
                parameters
            )
        )

        failure_matches = 0

        for item in self.failed_actions:

            if (
                item.get(
                    "signature"
                )
                ==
                signature
            ):

                failure_matches += 1

        return (
            failure_matches
            >=
            self.MAX_FAILURES
        )

    ############################################################
    # ACTION SIGNATURE
    ############################################################

    @staticmethod
    def _action_signature(
        tool,
        parameters
    ):

        try:

            serialized = json.dumps(
                parameters or {},
                sort_keys=True,
                ensure_ascii=False,
                default=str
            )

        except Exception:

            serialized = str(
                parameters
            )

        return (
            f"{str(tool).upper().strip()}"
            f"|"
            f"{serialized}"
        )

    ############################################################
    # RECORD FAILED ACTION
    ############################################################

    def _record_failed_action(
        self,
        action,
        result
    ):

        self.failure_count += 1

        tool = str(
            action.get(
                "tool",
                ""
            )
        ).upper().strip()

        parameters = action.get(
            "parameters",
            {}
        )

        signature = (
            self._action_signature(
                tool,
                parameters
            )
        )

        error = str(
            result.get(
                "error",
                "Action failed."
            )
        )

        failure = {
            "signature":
                signature,

            "tool":
                tool,

            "parameters":
                parameters,

            "error":
                error
        }

        self.failed_actions.append(
            failure
        )

        self.last_failure = (
            failure
        )

        self.recent_actions.append(
            {
                "tool":
                    tool,

                "parameters":
                    parameters,

                "success":
                    False,

                "error":
                    error
            }
        )

        print()

        print(
            "[ComputerAgent] "
            "ACTION FAILED:"
        )

        print(
            f"[ComputerAgent] {tool}"
        )

        print(
            f"[ComputerAgent] {error}"
        )

    ############################################################
    # RECORD STEP
    ############################################################

    def _record_step(
        self,
        step,
        reason,
        action,
        result,
        success
    ):

        record = {
            "type":
                "STEP",

            "step":
                step,

            "reason":
                reason,

            "action":
                action,

            "result":
                result,

            "success":
                success
        }

        try:

            self.memory.record(
                record
            )

        except Exception:

            pass

        try:

            self.state.add_history(
                record
            )

        except Exception:

            pass

    ############################################################
    # RECORD NO ACTION
    ############################################################

    def _record_no_action(
        self,
        step,
        reason
    ):

        try:

            self.memory.record(
                {
                    "type":
                        "NO_ACTION",

                    "step":
                        step,

                    "reason":
                        reason
                }
            )

        except Exception:

            pass

    ############################################################
    # RECORD FAILURE
    ############################################################

    def _record_failure(
        self,
        step,
        tool,
        parameters,
        error
    ):

        record = {
            "type":
                "FAILURE",

            "step":
                step,

            "tool":
                tool,

            "parameters":
                parameters,

            "error":
                error
        }

        try:

            self.memory.record(
                record
            )

        except Exception:

            pass

        try:

            self.state.add_history(
                record
            )

        except Exception:

            pass

        self.last_failure = record

    ############################################################
    # CONTEXT
    ############################################################

        ############################################################
    # FAST FILESYSTEM FIND
    ############################################################

    def _try_fast_filesystem_find(
        self
    ):

        goal = str(
            self.current_goal or ""
        ).strip()

        lower = goal.lower()

        ########################################################
        # Only intercept pure "find/locate/where/show" requests.
        # Modification or opening requests continue through the
        # normal computer-use pipeline.
        ########################################################

        find_intents = (
            r"^find\s+",
            r"^locate\s+",
            r"^where\s+is\s+",
            r"^where\s+are\s+",
            r"^show\s+me\s+where",
        )

        if not any(
            re.search(
                pattern,
                lower,
            )
            for pattern in find_intents
        ):

            return None

        ########################################################
        # Must actually reference a filesystem object.
        ########################################################

        file_terms = (
            "file",
            "folder",
            "directory",
            "pdf",
            "document",
            "spreadsheet",
            "excel",
            "word",
            "photo",
            "image",
            "video",
            "notes",
        )

        if not any(
            term in lower
            for term in file_terms
        ):

            return None

        candidates = (
            self._build_filesystem_context()
        )

        if not candidates:

            return None

        ########################################################
        # Strong match: answer immediately.
        ########################################################

        best = candidates[0]

        try:
            best_score = float(
                best.get(
                    "score",
                    0,
                )
                or 0
            )
        except Exception:
            best_score = 0.0

        if best_score >= 65.0:

            print()
            print(
                "[ComputerAgent] "
                "FAST FILESYSTEM MATCH:"
            )

            print(
                best["path"]
            )

            return (
                "I found it, sir. "
                f"{best['name']} is at "
                f"{best['path']}"
            )

        ########################################################
        # Ambiguous result: provide candidates rather than
        # pretending certainty.
        ########################################################

        lines = []

        for item in candidates[:3]:

            lines.append(
                f"- {item['path']}"
            )

        if lines:

            return (
                "I found several possible matches, sir:\n"
                +
                "\n".join(
                    lines
                )
            )

        return None

    ############################################################
    # FILESYSTEM AMBIGUITY CHECK
    ############################################################

    def _check_filesystem_ambiguity(
        self,
        parameters,
    ):

        params = dict(
            parameters or {}
        )

        candidates = params.get(
            "_resolution_candidates",
            [],
        )

        if not isinstance(
            candidates,
            list,
        ):
            candidates = []

        explicit = str(
            params.get(
                "source",
                params.get(
                    "path",
                    "",
                )
            )
            or
            ""
        ).strip()

        if (
            explicit
            and
            (
                Path(explicit).is_absolute()
                or "/" in explicit
                or "\\" in explicit
                or explicit.startswith("~")
            )
        ):

            return {
                "status":
                    "CLEAR",
                "reason":
                    "Explicit filesystem path supplied.",
                "candidates":
                    candidates,
            }

        if not candidates:

            return {
                "status":
                    "NOT_FOUND",
                "reason":
                    "No filesystem candidate was found.",
                "candidates":
                    [],
            }

        ranked = []

        for item in candidates:

            if not isinstance(
                item,
                dict,
            ):
                continue

            try:
                score = float(
                    item.get(
                        "score",
                        0,
                    )
                    or
                    0
                )
            except Exception:
                score = 0.0

            ranked.append(
                {
                    "path":
                        str(
                            item.get(
                                "path",
                                "",
                            )
                            or
                            ""
                        ),

                    "name":
                        str(
                            item.get(
                                "name",
                                "",
                            )
                            or
                            ""
                        ),

                    "score":
                        score,
                }
            )

        ranked.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        if not ranked:

            return {
                "status":
                    "NOT_FOUND",
                "reason":
                    "No usable filesystem candidates were returned.",
                "candidates":
                    [],
            }

        best = ranked[0]

        if best["score"] < 75.0:

            return {
                "status":
                    "AMBIGUOUS",
                "reason":
                    (
                        "Filesystem match confidence is not "
                        "strong enough for automatic mutation."
                    ),
                "candidates":
                    ranked[:5],
            }

        if (
            len(ranked) >= 2
            and
            ranked[1]["score"] >= 60.0
            and
            best["score"] - ranked[1]["score"] < 10.0
        ):

            return {
                "status":
                    "AMBIGUOUS",
                "reason":
                    (
                        "Multiple filesystem candidates have "
                        "similar confidence."
                    ),
                "candidates":
                    ranked[:5],
            }

        return {
            "status":
                "CLEAR",
            "reason":
                "Strong unique filesystem candidate found.",
            "candidates":
                ranked[:5],
        }

    ############################################################
    # FILESYSTEM TARGET RESOLUTION
    ############################################################

    def _resolve_filesystem_targets(
        self,
        tool,
        parameters
    ):

        """
        Resolve natural-language filesystem references through
        FileIntelligence before a filesystem mutation executes.

        This method is read-only. It never changes the filesystem.
        """

        tool = str(
            tool or ""
        ).upper().strip()

        params = dict(
            parameters or {}
        )

        if tool not in {
            "COPY",
            "MOVE",
            "RENAME",
            "DELETE_FILE",
            "DELETE_FOLDER",
            "OPEN_FILE",
        }:

            return {
                "resolved": False,
                "parameters": params,
                "candidates": [],
            }

        def is_concrete(
            value
        ):

            value = str(
                value or ""
            ).strip()

            if not value:
                return False

            return (
                Path(value).is_absolute()
                or value.startswith("~")
                or "/" in value
                or "\\" in value
            )

        def query_from_reference(
            value
        ):

            stop = {
                "my",
                "the",
                "a",
                "an",
                "this",
                "that",
                "file",
                "folder",
                "document",
                "directory",
                "pdf",
                "please",
                "to",
                "from",
                "in",
                "on",
            }

            tokens = [
                token
                for token in re.findall(
                    r"[a-z0-9._-]+",
                    str(value or "").lower(),
                )
                if len(token) >= 2
                and token not in stop
            ]

            return " ".join(
                tokens[:8]
            ).strip()

        def discover(
            value,
            extension=None,
            directories=False,
        ):

            query = query_from_reference(
                value
            )

            if not query:
                query = str(
                    value or ""
                ).strip()

            if not query:
                return []

            roots = (
                Path.home() / "Desktop",
                Path.home() / "Documents",
                Path.home() / "Downloads",
            )

            found = []

            for root in roots:

                if (
                    not root.exists()
                    or not root.is_dir()
                ):
                    continue

                try:

                    found.extend(
                        self.file_intelligence.search(
                            root=root,
                            query=query,
                            extension=extension,
                            max_results=8,
                            recursive=True,
                        )
                    )

                except Exception as exc:

                    print(
                        "[ComputerAgent] "
                        "Filesystem resolution warning:",
                        exc,
                    )

            unique = {}

            for item in found:
                unique[
                    item.path
                ] = item

            items = list(
                unique.values()
            )

            items.sort(
                key=lambda item: (
                    bool(
                        item.is_directory
                    )
                    if directories
                    else
                    bool(
                        item.is_file
                    ),
                    item.score,
                ),
                reverse=True,
            )

            return items[:8]

        source = params.get(
            "source",
            params.get(
                "path",
                params.get(
                    "file",
                    "",
                )
            )
        )

        source_text = str(
            source or ""
        ).lower()

        extension = None

        if re.search(
            r"\bpdf\b|\.pdf\b",
            source_text,
        ):

            extension = ".pdf"

        elif re.search(
            r"\bdocx?\b",
            source_text,
        ):

            extension = ".docx"

        elif re.search(
            r"\bxlsx?\b",
            source_text,
        ):

            extension = ".xlsx"

        source_candidates = []

        if (
            source
            and
            not is_concrete(
                source
            )
            and
            not Path(
                str(source)
            ).exists()
        ):

            source_candidates = discover(
                source,
                extension=extension,
            )

            if source_candidates:

                params[
                    "source"
                ] = source_candidates[
                    0
                ].path

        destination = params.get(
            "destination",
            params.get(
                "folder",
                "",
            )
        )

        destination_candidates = []

        if (
            tool in {
                "COPY",
                "MOVE",
            }
            and
            destination
            and
            not is_concrete(
                destination
            )
            and
            not Path(
                str(destination)
            ).exists()
        ):

            destination_candidates = discover(
                destination,
                directories=True,
            )

            directories = [
                item
                for item in destination_candidates
                if item.is_directory
            ]

            if directories:

                params[
                    "destination"
                ] = directories[
                    0
                ].path

        if (
            tool
            ==
            "DELETE_FOLDER"
            and
            params.get(
                "path",
                "",
            )
            and
            not is_concrete(
                params.get(
                    "path",
                    "",
                )
            )
        ):

            folder_candidates = discover(
                params[
                    "path"
                ],
                directories=True,
            )

            directories = [
                item
                for item in folder_candidates
                if item.is_directory
            ]

            if directories:

                params[
                    "path"
                ] = directories[
                    0
                ].path

        return {
            "resolved":
                params
                !=
                dict(
                    parameters
                    or
                    {}
                ),

            "parameters":
                params,

            "candidates":
                [
                    {
                        "path":
                            item.path,

                        "name":
                            item.name,

                        "score":
                            item.score,
                    }
                    for item in (
                        source_candidates
                        +
                        destination_candidates
                    )[:8]
                ],
        }

    ############################################################
    # FILE & FOLDER DISCOVERY CONTEXT
    ############################################################

    def _build_filesystem_context(
        self
    ):

        goal = str(
            self.current_goal or ""
        ).strip()

        if not goal:
            return []

        lower = goal.lower()

        file_terms = (
            "file",
            "folder",
            "directory",
            "pdf",
            "document",
            "spreadsheet",
            "excel",
            "word",
            "photo",
            "image",
            "video",
            "notes",
            "download",
            "desktop",
            "downloads",
        )

        if not any(
            term in lower
            for term in file_terms
        ):

            return []

        ########################################################
        # Search the user's common working locations first.
        ########################################################

        home = Path.home()

        roots = [
            home / "Desktop",
            home / "Documents",
            home / "Downloads",
        ]

        existing_roots = [
            root
            for root in roots
            if root.exists()
            and root.is_dir()
        ]

        ########################################################
        # Query the intelligence layer using the original goal.
        #
        # It ranks candidates; it does not modify anything.
        ########################################################

        candidates = []

        for root in existing_roots:

            try:

                results = (
                    self.file_intelligence.search(
                        root=root,
                        query=goal,
                        max_results=8,
                        recursive=True,
                    )
                )

                candidates.extend(
                    results
                )

            except Exception as exc:

                print(
                    "[ComputerAgent] "
                    "File discovery warning:",
                    exc
                )

        ########################################################
        # De-duplicate by absolute path.
        ########################################################

        unique = {}

        for candidate in candidates:

            unique[
                candidate.path
            ] = candidate

        ranked = sorted(
            unique.values(),
            key=lambda item: item.score,
            reverse=True,
        )[:8]

        return [
            {
                "path":
                    item.path,

                "name":
                    item.name,

                "is_file":
                    item.is_file,

                "is_directory":
                    item.is_directory,

                "extension":
                    item.extension,

                "score":
                    item.score,

                "reasons":
                    item.reasons,
            }

            for item in ranked
        ]

    ############################################################
    # COMPACT CONTEXT
    ############################################################

    def _build_context(
        self
    ):

        ########################################################
        # Keep the full history internally, but only expose a
        # compact working context to the local vision model.
        ########################################################

        try:

            history = list(
                self.state.history[
                    -self.MAX_HISTORY:
                ]
            )

        except Exception:

            history = []

        ########################################################
        # Recent failures
        ########################################################

        failures = list(
            self.failed_actions[
                -3:
            ]
        )

        ########################################################
        # Recent successful actions
        ########################################################

        completed = list(
            self.completed_actions[
                -5:
            ]
        )

        ########################################################
        # Recent action attempts
        ########################################################

        recent_actions = list(
            self.recent_actions
        )[-5:]

        ########################################################
        # Current stage
        ########################################################

        try:

            current_stage = (
                self.state.currentStage()
                or ""
            )

        except Exception:

            current_stage = ""

        ########################################################
        # Important variables only
        ########################################################

        variables = getattr(
            self.state,
            "variables",
            {}
        )

        if not isinstance(
            variables,
            dict
        ):

            variables = {}

        compact_variables = {}

        for key, value in list(
            variables.items()
        )[-10:]:

            try:

                json.dumps(
                    value,
                    default=str
                )

                compact_variables[
                    str(key)
                ] = value

            except Exception:

                compact_variables[
                    str(key)
                ] = str(value)

        ########################################################
        # FILESYSTEM DISCOVERY
        ########################################################

        filesystem_candidates = (
            self._build_filesystem_context()
        )

        ########################################################
        # BROWSER STATE
        ########################################################

        browser_context = (
            self._build_browser_context()
        )

        ########################################################
        # COMPACT MODEL CONTEXT
        ########################################################

        return {

            "goal":
                self.current_goal,

            "stage":
                current_stage,

            "stage_objective":
                current_stage,

            "step":
                getattr(
                    self.state,
                    "step",
                    0
                ),

            "recent_history":
                history,

            "recent_actions":
                recent_actions,

            "completed_actions":
                completed,

            "failed_actions":
                failures,

            "last_failure":
                self.last_failure,

            "previous_action":
                self.last_action,

            "previous_expected_outcome":
                self.last_expected_outcome,

            "previous_action_step":
                self.last_action_step,

            "previous_executor_result":
                self.last_action_result,

            "previous_action_verified":
                self.last_action_verified,

            "blocked_action_signature":
                self.blocked_action_signature,

            "recovery":
                self.recovery.model_context(),

            "variables":
                compact_variables,

            "filesystem_candidates":
                filesystem_candidates,

            "browser":
                browser_context,
        }

        ############################################################
    # PROMPT
    ############################################################

    ############################################################
    # BROWSER CONTEXT
    ############################################################

    def _build_browser_context(
        self
    ):

        goal = str(
            self.current_goal or ""
        ).strip()

        lower = goal.lower()

        state = {}

        try:
            state = (
                self.browser_intelligence.current_state()
            )
        except Exception:
            state = {}

        intent = "none"
        browser = ""
        query = ""
        engine = ""

        ########################################################
        # Explicit browser selection
        ########################################################

        browser_match = re.search(
            r"\b(?:on|using|in)\s+"
            r"(chrome|google chrome|edge|microsoft edge|"
            r"firefox|mozilla firefox|opera)\b",
            lower,
        )

        if browser_match:
            browser = (
                self.browser_intelligence.normalize_browser(
                    browser_match.group(1)
                )
            )

        ########################################################
        # Open-site intent
        ########################################################

        site_match = re.search(
            r"\b(?:open|go to|visit|launch)\s+"
            r"(youtube|youtube\.com|google|google\.com|gmail|"
            r"github|reddit|instagram|spotify)\b",
            lower,
        )

        if site_match:
            intent = "open_site"

        ########################################################
        # Search-on-site intent
        ########################################################

        youtube_search = re.search(
            r"\b(?:search|find)\s+(.+?)\s+"
            r"(?:on|in)\s+youtube\b",
            lower,
        )

        if youtube_search:
            intent = "search"
            query = youtube_search.group(1).strip()
            engine = "youtube"

        else:
            generic_search = re.search(
                r"\bsearch\s+(?:for\s+)?(.+?)"
                r"(?:\s+on\s+(google|bing))?\s*$",
                lower,
            )

            if generic_search:
                intent = "search"
                query = generic_search.group(1).strip()
                engine = (
                    generic_search.group(2)
                    or
                    "google"
                )

        return {
            "intent": intent,
            "browser": browser,
            "query": query,
            "engine": engine,
            "state": state,
        }

    def _build_prompt(
        self,
        goal,
        step,
        context
    ):

        ########################################################
        # AVAILABLE TOOLS
        ########################################################

        tools = (
            self.tools.available()
        )

        tool_text = "\n".join(
            f"- {tool}"
            for tool in tools
        )

        ########################################################
        # COMPACT CONTEXT
        ########################################################

        try:

            context_text = json.dumps(
                context,
                ensure_ascii=False,
                separators=(
                    ",",
                    ":"
                ),
                default=str
            )

        except Exception:

            context_text = str(
                context
            )

        ########################################################
        # HARD CONTEXT LIMIT
        ########################################################

        MAX_CONTEXT_CHARS = 6000

        if len(
            context_text
        ) > MAX_CONTEXT_CHARS:

            context_text = (
                context_text[
                    -MAX_CONTEXT_CHARS:
                ]
            )

        ########################################################
        # UNIVERSAL COMPUTER REASONING PROMPT
        ########################################################

        return f"""
You are JARVIS, a universal autonomous computer
intelligence operating a Windows computer.

Your job is to accomplish the user's ENTIRE objective
using the computer.

You are not a scripted workflow engine.

You must reason from the CURRENT SCREEN and adapt
to whatever application or interface is actually visible.

============================================================
USER MISSION
============================================================

{goal}

============================================================
CURRENT STEP
============================================================

{step}

============================================================
CURRENT MISSION OBJECTIVE
============================================================

The planner provides the current mission objective.
Treat this as the outcome that must become true before
moving to the next planner stage.

CURRENT MISSION OBJECTIVE:

{context.get("stage_objective", "")}

============================================================
BROWSER INTELLIGENCE
============================================================

The working context may contain browser state and browser intent.

Use these capabilities directly when appropriate:

- OPEN_URL for a known website or URL.
- SEARCH_WEB for a web search.
- Use engine "youtube" when the request explicitly targets YouTube.
- Respect an explicitly requested browser such as Chrome, Edge,
  Firefox, or Opera.
- Do not reinterpret "open YouTube on Opera" as OPEN_APP with the
  whole phrase as the application name.
- Do not invent URLs or search results.
- Browser process launch is not proof that the page loaded.
- The next screenshot is still the source of truth.
- If the browser is not foreground before keyboard interaction,
  use FOCUS_WINDOW or the browser focus capability.

============================================================

============================================================
FILESYSTEM DISCOVERY
============================================================

The working context may contain filesystem_candidates.

These are ranked candidates discovered from common user
locations. They are hints for locating the user's intended
file or folder.

IMPORTANT:
- A candidate is NOT proof that it is the correct target.
- Confirm the visible/current computer state before acting.
- Do not invent a path that is not present in the context or
  visible on screen.
- Use the candidate path to guide filesystem reasoning when
  appropriate.
- Actual filesystem changes must still be performed through
  the available executor actions.


- This is an objective, not a fixed procedure.
- Do not blindly follow the wording as a sequence of clicks.
- Decide HOW to achieve it from the current screen.
- Once the objective is visibly achieved, mark the stage complete.
- If one strategy fails, preserve the objective and choose another strategy.
- Never let a failed action replace the actual objective.

============================================================
CURRENT WORKING MEMORY
============================================================

{context_text}

============================================================
RECOVERY CONSTRAINTS
============================================================

The working memory may include a RECOVERY section.
Treat it as a hard constraint.

- Do not select a blocked tool.
- Do not select a failed exact action signature.
- If the previous route failed semantically, choose a genuinely
  different capability or route to accomplish the same objective.
- If a tool is marked unsupported, do not attempt that tool again
  during this task.
- Changing only the coordinates while keeping the same failed
  route is NOT sufficient when the route itself failed.

============================================================
THE COMPUTER SCREEN IS THE SOURCE OF TRUTH
============================================================

The screenshot represents the actual current state
of the computer.

Never assume that an action worked merely because
the executor reported that the input was sent.

For example:

A keyboard executor saying:

    "Ctrl+S was pressed"

does NOT mean:

    "The file was successfully saved."

You must inspect the resulting screen and determine
whether the intended outcome actually occurred.

============================================================
ACTION OUTCOME REASONING
============================================================

The Python kernel independently verifies the previous action
from the CURRENT screenshot before this reasoning prompt is
built. That verification is included in the working memory.

Treat the following fields as authoritative when present:

- previous_action_verified
- previous_expected_outcome
- previous_action
- previous_executor_result

Do NOT replace a kernel verification result with a guess based
on execution logs or your own assumptions.

If previous_action_verified is false, DO NOT select the same
action again. Choose an alternative route.

Your job is to use the verified computer state to decide the
next action.

Every CONTINUE decision MUST provide:

    "expected_outcome"

describing what should visibly or observably happen after
the selected action.

Before selecting an action, reason about:

1. CURRENT STATE
   What is actually visible right now?

2. CURRENT OBJECTIVE
   What part of the user's mission is unfinished?

3. INTENDED ACTION
   What computer operation should move the task forward?

4. EXPECTED OUTCOME
   What visible or observable change should occur
   if the action works?

5. OBSERVED OUTCOME
   After the previous action, did that expected change
   actually occur?

6. RECOVERY
   If the expected outcome did not occur, DO NOT blindly
   repeat the same action.

   Instead:

   - inspect the current screen
   - determine why the action may not have worked
   - identify another available route
   - execute that alternative
   - verify again

============================================================
CRITICAL RULE
============================================================

EXECUTOR SUCCESS IS NOT TASK SUCCESS.

An executor reporting success only means that the
requested input was sent to the operating system.

Only the resulting computer state can establish
whether the action actually achieved its purpose.

============================================================
FAILED ACTIONS
============================================================

If an action appears to have failed semantically, record that
reasoning in your decision.

The kernel will block an immediately repeated action after a
semantic failure. Therefore, when an action did not achieve
its expected outcome, select a DIFFERENT capability or route
that can achieve the same unfinished objective.

Do not repeat the same keyboard shortcut, click, command, or
other input merely because its executor reported success.


Example:

If:

    expected = save interface appears

but:

    observed = no save interface

then:

DO NOT repeat the same action merely because the
keyboard/mouse executor returned success.

Instead choose another strategy based on the
current visible interface.

============================================================
NO APPLICATION-SPECIFIC KNOWLEDGE
============================================================

Do NOT assume a particular workflow because the
application is:

- Notepad
- Chrome
- Edge
- VS Code
- File Explorer
- Calculator
- Word
- Excel
- or any other application.

Do not use hardcoded application workflows.

The same reasoning must work across unfamiliar
applications.

Use the screen to determine what is possible.

============================================================
MISSION TRACKING
============================================================

Always distinguish:

COMPLETED
from
CURRENT
from
REMAINING

Never restart an operation that is already visibly
completed.

Never declare the entire mission complete because
only one stage succeeded.

Continue until the user's ENTIRE objective is achieved.

============================================================
ONE ACTION PER OBSERVATION
============================================================

Return exactly ONE computer action.

After the action executes, the system will provide
a new screenshot.

Use that new observation to decide what to do next.

Do not blindly chain multiple visual actions.

============================================================
RECOVERY RULES
============================================================

If the previous action did not achieve its expected
outcome:

1. Do not blindly repeat it.

2. Inspect the new screenshot.

3. Determine the current UI state.

4. Consider another capability.

5. Choose the best alternative.

6. Verify the result.

Possible causes include:

- wrong target
- wrong window
- lost focus
- application loading
- modal dialog
- unexpected UI state
- invalid parameter
- unsupported operation
- visual ambiguity
- action accepted but objective not achieved

============================================================
GENERAL COMPUTER CAPABILITIES
============================================================

You may use any available capability appropriate
to the current situation.

Examples include:

OPEN_APP
CLOSE_APP
OPEN_URL
SEARCH_WEB
TYPE_TEXT
PRESS_KEY
HOTKEY
MOUSE_MOVE
LEFT_CLICK
RIGHT_CLICK
DOUBLE_CLICK
SCROLL_UP
SCROLL_DOWN
FOCUS_WINDOW
CLOSE_WINDOW
MINIMIZE_WINDOW
MAXIMIZE_WINDOW
COPY
MOVE
RENAME
CREATE_FILE
CREATE_FOLDER
RUN_COMMAND
RUN_PYTHON
WAIT
OCR_SCREEN
OCR_IMAGE
LOCATE_TEXT
CLICK_TEXT
CLICK_TYPE_ENTER
READ_CLIPBOARD
WRITE_CLIPBOARD

These are capabilities, not workflows.

============================================================
WAIT
============================================================

Use WAIT when the computer needs time to:

- launch an application
- load a page
- open a dialog
- complete an operation
- update the interface

Do not repeatedly perform the same action when the
computer may simply need time.

============================================================
SAFETY
============================================================

Never autonomously perform destructive system operations
such as:

- shutdown
- restart
- formatting drives
- destroying system data
- disabling security systems

Follow the kernel policy.

============================================================
AVAILABLE TOOLS
============================================================

{tool_text}

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

For another action:

{{
    "status": "CONTINUE",
    "reason": "Explain the current state, the unfinished objective, and why this action is the best next action.",
    "message": "",
    "expected_outcome": "What visible or observable result should happen after this action.",
    "actions": [
        {{
            "tool": "TOOL_NAME",
            "parameters": {{}}
        }}
    ]
}}

For completion:

{{
    "status": "DONE",
    "reason": "Visible evidence proves that the ENTIRE user mission is complete.",
    "message": "Task completed, sir.",
    "expected_outcome": "",
    "actions": []
}}

For blocked or unsafe:

{{
    "status": "BLOCKED",
    "reason": "Explain why the task cannot safely continue.",
    "message": "I could not safely complete that task, sir.",
    "expected_outcome": "",
    "actions": []
}}

JSON ONLY.
""".strip()

    ############################################################
    # COMPLETE TASK
    ############################################################

    def _complete_task(
        self,
        goal,
        step,
        message
    ):

        try:

            self.memory.record(
                {
                    "type":
                        "TASK_COMPLETED",

                    "goal":
                        goal,

                    "step":
                        step,

                    "message":
                        message
                }
            )

        except Exception:

            pass

        try:

            self.state.complete()

        except Exception:

            pass

        print()

        print(
            "=" * 78
        )

        print(
            "[ComputerAgent] TASK COMPLETED"
        )

        print(
            f"[ComputerAgent] {message}"
        )

        print(
            "=" * 78
        )

    ############################################################
    # SAFE RESULT
    ############################################################

    @staticmethod
    def _safe_result(
        result
    ):

        if result is None:

            return "completed"

        if isinstance(
            result,
            (
                str,
                int,
                float,
                bool
            )
        ):

            return result

        try:

            json.dumps(
                result
            )

            return result

        except Exception:

            return str(
                result
            )