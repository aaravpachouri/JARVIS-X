import json
import time
from collections import deque

from ai.local_client import LocalAIClient

from backend.agent_memory import AgentMemory
from backend.agent_observer import AgentObserver
from backend.agent_policy import AgentPolicy
from backend.agent_state import AgentState
from backend.agent_tools import AgentToolset


class UniversalComputerAgent:

    ############################################################
    # CONFIGURATION
    ############################################################

    MODEL_NAME = "qwen3-vl:4b-instruct"

    MAX_STEPS = 60
    MAX_FAILURES_PER_ACTION = 3

    MAX_HISTORY = 20
    MAX_RECENT_ACTIONS = 10
    MAX_FAILED_ACTIONS = 10
    MAX_COMPLETED_ACTIONS = 20

    THINK_RETRIES = 3

    ACTION_DELAY = 0.20
    OBSERVATION_DELAY = 0.20
    FAILURE_DELAY = 0.60
    APP_START_DELAY = 0.80

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

        self.observer = AgentObserver()
        self.policy = AgentPolicy()

        self.state = AgentState()

        self.memory = AgentMemory(
            self.state
        )

        self.tools = AgentToolset(
            engine
        )

        self.engine = engine

        ########################################################
        # TASK STATE
        ########################################################

        self.goal = ""

        self.step = 0

        self.current_stage = ""

        self.recent_actions = deque(
            maxlen=self.MAX_RECENT_ACTIONS
        )

        self.completed_actions = []

        self.failed_actions = []

        self.last_failure = None

        self.failure_count = 0

        self.last_decision = None

        ########################################################
        # CAPABILITY CACHE
        ########################################################

        self._capability_contract = None

        print()
        print(
            "[UniversalAgent] "
            "JARVIS UNIVERSAL COMPUTER BRAIN READY"
        )

        print(
            "[UniversalAgent] Brain:",
            self.MODEL_NAME
        )

    ############################################################
    # SHOULD HANDLE
    ############################################################

    def shouldHandle(
        self,
        command
    ):

        return bool(
            str(
                command or ""
            ).strip()
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
                "I did not receive a computer task, sir."
            )

        self._reset_task(
            goal
        )

        print()
        print("=" * 78)
        print(
            "[UniversalAgent] "
            "UNIVERSAL COMPUTER MODE"
        )
        print(
            "[UniversalAgent] Goal:",
            goal
        )
        print(
            "[UniversalAgent] Model:",
            self.MODEL_NAME
        )
        print("=" * 78)

        ########################################################
        # START STATE
        ########################################################

        try:

            self.state.start(
                goal
            )

        except Exception as exc:

            print(
                "[UniversalAgent] "
                "State start warning:",
                exc
            )

        ########################################################
        # MAIN AGENT LOOP
        ########################################################

        for step in range(
            1,
            self.MAX_STEPS + 1
        ):

            self.step = step

            try:

                self.state.step = step

            except Exception:
                pass

            print()
            print(
                f"[UniversalAgent] "
                f"STEP {step}/{self.MAX_STEPS}"
            )

            ####################################################
            # OBSERVE
            ####################################################

            try:

                observation = (
                    self._observe()
                )

            except Exception as exc:

                self._record_failure(
                    "OBSERVE",
                    {},
                    str(exc)
                )

                time.sleep(
                    self.OBSERVATION_DELAY
                )

                continue

            ####################################################
            # BUILD REASONING CONTEXT
            ####################################################

            context = (
                self._build_context(
                    observation
                )
            )

            ####################################################
            # THINK
            ####################################################

            try:

                decision = (
                    self._think(
                        observation,
                        context
                    )
                )

            except Exception as exc:

                print()
                print(
                    "[UniversalAgent] "
                    "BRAIN ERROR:",
                    exc
                )

                self._record_failure(
                    "THINK",
                    {},
                    str(exc)
                )

                time.sleep(
                    self.OBSERVATION_DELAY
                )

                continue

            self.last_decision = decision

            ####################################################
            # NORMALIZE DECISION
            ####################################################

            decision = (
                self._normalize_decision(
                    decision
                )
            )

            status = decision[
                "status"
            ]

            reason = decision[
                "reason"
            ]

            print(
                "[UniversalAgent] STATUS:",
                status
            )

            if reason:

                print(
                    "[UniversalAgent] REASON:",
                    reason
                )

            ####################################################
            # BLOCKED
            ####################################################

            if status == "BLOCKED":

                message = (
                    decision.get(
                        "message"
                    )
                    or
                    "I could not safely complete that task, sir."
                )

                self._fail_task(
                    message
                )

                return message

            ####################################################
            # DONE
            ####################################################

            if status == "DONE":

                ################################################
                # IMPORTANT:
                #
                # A DONE response is not accepted blindly.
                #
                # We only accept it when the model supplied
                # a completion reason AND the current state
                # has no known unresolved failure.
                ################################################

                if not self._completion_is_plausible(
                    decision,
                    context
                ):

                    print(
                        "[UniversalAgent] "
                        "Completion claim rejected."
                    )

                    self._record_failure(
                        "VERIFY",
                        {},
                        (
                            "Model claimed completion "
                            "without sufficient evidence."
                        )
                    )

                    time.sleep(
                        self.OBSERVATION_DELAY
                    )

                    continue

                message = (
                    decision.get(
                        "message"
                    )
                    or
                    "Task completed, sir."
                )

                self._complete_task(
                    message
                )

                return message

            ####################################################
            # ACTION
            ####################################################

            actions = decision.get(
                "actions",
                []
            )

            if not actions:

                self._record_no_action(
                    reason
                )

                time.sleep(
                    self.OBSERVATION_DELAY
                )

                continue

            ####################################################
            # ONE ACTION ONLY
            ####################################################

            action = actions[0]

            ####################################################
            # REPEATED FAILURE PROTECTION
            ####################################################

            if self._is_repeated_failure(
                action
            ):

                print(
                    "[UniversalAgent] "
                    "Repeated failed action blocked."
                )

                self._record_failure(
                    action.get(
                        "tool",
                        ""
                    ),
                    action.get(
                        "parameters",
                        {}
                    ),
                    (
                        "This exact action has "
                        "already failed repeatedly."
                    )
                )

                time.sleep(
                    self.OBSERVATION_DELAY
                )

                continue

            ####################################################
            # EXECUTE
            ####################################################

            result = (
                self._execute(
                    action
                )
            )

            success = bool(
                result.get(
                    "success",
                    False
                )
            )

            ####################################################
            # RECORD
            ####################################################

            self._record_step(
                reason,
                action,
                result,
                success
            )

            ####################################################
            # SUCCESS
            ####################################################

            if success:

                self.failure_count = 0
                self.last_failure = None

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
                # Application startup stabilization
                ################################################

                tool = str(
                    action.get(
                        "tool",
                        ""
                    )
                ).upper().strip()

                if tool in {
                    "OPEN_APP",
                    "OPEN_APPLICATION",
                    "LAUNCH_APP",
                    "LAUNCH_APPLICATION"
                }:

                    time.sleep(
                        self.APP_START_DELAY
                    )

                elif tool != "WAIT":

                    time.sleep(
                        self.ACTION_DELAY
                    )

            ####################################################
            # FAILURE
            ####################################################

            else:

                self._record_failed_action(
                    action,
                    result
                )

                time.sleep(
                    self.FAILURE_DELAY
                )

        ########################################################
        # STEP LIMIT
        ########################################################

        self._fail_task(
            (
                "I reached the autonomous execution limit "
                "before I could verify completion, sir."
            )
        )

        return (
            "I reached the autonomous execution limit "
            "before I could verify completion, sir."
        )

    ############################################################
    # RESET
    ############################################################

    def _reset_task(
        self,
        goal
    ):

        self.goal = goal

        self.step = 0

        self.current_stage = ""

        self.recent_actions.clear()

        self.completed_actions = []

        self.failed_actions = []

        self.last_failure = None

        self.failure_count = 0

        self.last_decision = None

        ########################################################
        # Recreate state for a completely clean task.
        ########################################################

        self.state = AgentState()

        self.memory = AgentMemory(
            self.state
        )

    ############################################################
    # OBSERVATION
    ############################################################

    def _observe(
        self
    ):

        capture_temp = getattr(
            self.observer,
            "capture_to_temp",
            None
        )

        if callable(
            capture_temp
        ):

            return capture_temp()

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
            "AgentObserver does not provide "
            "a supported capture method."
        )

    ############################################################
    # THINK
    ############################################################

    def _think(
        self,
        observation,
        context
    ):

        prompt = self._build_prompt(
            context
        )

        last_error = None

        for attempt in range(
            1,
            self.THINK_RETRIES + 1
        ):

            try:

                decision = (
                    self.ai.vision_json(
                        observation,
                        prompt,
                        system=(
                            self._system_prompt()
                        )
                    )
                )

                if isinstance(
                    decision,
                    dict
                ):

                    return decision

                last_error = (
                    "Model returned a "
                    "non-object JSON response."
                )

            except Exception as exc:

                last_error = str(
                    exc
                )

                print(
                    "[UniversalAgent] "
                    f"Think attempt {attempt} failed:",
                    exc
                )

            time.sleep(
                0.5
            )

        raise RuntimeError(
            "Local reasoning failed after "
            f"{self.THINK_RETRIES} attempts: "
            f"{last_error}"
        )

    ############################################################
    # SYSTEM PROMPT
    ############################################################

    def _system_prompt(
        self
    ):

        return """
You are JARVIS, a universal autonomous computer-use agent.

You operate a real Windows computer.

Your job is NOT to provide instructions to the user.

Your job is to accomplish the user's computer objective
by directly operating the computer through the capabilities
provided by the execution kernel.

The user may express the objective naturally and in any
language. Understand the semantic meaning of the request.
Do not depend on hardcoded English command patterns.

You must continuously follow:

OBSERVE
UNDERSTAND
DECIDE
ACT
OBSERVE AGAIN
VERIFY
CONTINUE OR COMPLETE

The screenshot is the source of truth for the current
computer state.

The user's original objective is the source of truth for
what must ultimately be accomplished.

Never confuse the current screen with the user's goal.

You may perform exactly ONE computer action per reasoning
cycle.

Never blindly chain actions.

After every action, wait for the next observation and
re-evaluate the computer state.

Never invent:
- UI elements
- buttons
- text
- files
- coordinates
- search results
- application state
- task results

If an action fails, determine why and choose a different
or better recovery strategy.

Do not repeatedly perform the same failed action.

Do not claim completion merely because one intermediate
operation succeeded.

Completion means the ENTIRE original user objective has
been satisfied.

Destructive operations must obey the existing JARVIS
policy layer.

Return ONLY valid JSON.
""".strip()

    ############################################################
    # PROMPT
    ############################################################

    def _build_prompt(
        self,
        context
    ):

        capabilities = (
            self._get_capability_contract()
        )

        context_text = json.dumps(
            context,
            ensure_ascii=False,
            indent=2,
            default=str
        )

        return f"""
USER OBJECTIVE
============================================================

{self.goal}

============================================================
CURRENT TASK STATE
============================================================

{context_text}

============================================================
AVAILABLE COMPUTER CAPABILITIES
============================================================

{capabilities}

============================================================
DECISION RULE
============================================================

Determine the SINGLE best next action that advances the
user's entire objective from the computer state visible
in the supplied screenshot.

Do not output multiple dependent actions.

If the current objective is already fully satisfied,
return DONE.

If it is impossible or unsafe to continue, return BLOCKED.

Otherwise return exactly one action.

============================================================
OUTPUT
============================================================

CONTINUE:

{{
    "status": "CONTINUE",
    "reason": "Why this action is the best next step.",
    "message": "",
    "actions": [
        {{
            "tool": "TOOL_NAME",
            "parameters": {{}}
        }}
    ]
}}

DONE:

{{
    "status": "DONE",
    "reason": "Visible evidence that the ENTIRE objective is complete.",
    "message": "Task completed, sir.",
    "actions": []
}}

BLOCKED:

{{
    "status": "BLOCKED",
    "reason": "Why the task cannot safely continue.",
    "message": "I could not safely complete that task, sir.",
    "actions": []
}}

JSON ONLY.
""".strip()

    ############################################################
    # CAPABILITY CONTRACT
    ############################################################

    def _get_capability_contract(
        self
    ):

        if self._capability_contract is not None:

            return self._capability_contract

        ########################################################
        # Use the existing toolset's model context where
        # available. This preserves the current capability
        # architecture instead of duplicating ActionType logic.
        ########################################################

        try:

            context = (
                self.tools.modelContext()
            )

            if isinstance(
                context,
                dict
            ):

                self._capability_contract = (
                    json.dumps(
                        context,
                        ensure_ascii=False,
                        indent=2,
                        default=str
                    )
                )

                return self._capability_contract

            if context:

                self._capability_contract = str(
                    context
                )

                return self._capability_contract

        except Exception as exc:

            print(
                "[UniversalAgent] "
                "Capability context warning:",
                exc
            )

        ########################################################
        # Safe fallback.
        ########################################################

        try:

            available = (
                self.tools.available()
            )

        except Exception:

            available = []

        self._capability_contract = "\n".join(
            f"- {name}"
            for name in available
        )

        return self._capability_contract

    ############################################################
    # DECISION NORMALIZATION
    ############################################################

    def _normalize_decision(
        self,
        decision
    ):

        if not isinstance(
            decision,
            dict
        ):

            return {
                "status":
                    "CONTINUE",
                "reason":
                    "No usable decision returned.",
                "message":
                    "",
                "actions":
                    []
            }

        ########################################################
        # STATUS
        ########################################################

        status = str(
            decision.get(
                "status",
                ""
            )
        ).upper().strip()

        ########################################################
        # Legacy compatibility
        ########################################################

        if not status:

            if decision.get(
                "done",
                False
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
            "actions"
        )

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
            # AgentToolset owns normalization.
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
                    "[UniversalAgent] "
                    "Parameter normalization warning:",
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
                str(
                    decision.get(
                        "message",
                        ""
                    )
                ),
            "actions":
                clean
        }

    ############################################################
    # CONTEXT
    ############################################################

    def _build_context(
        self,
        observation
    ):

        try:

            state_snapshot = (
                self.state.snapshot()
            )

        except Exception:

            state_snapshot = {}

        try:

            memory_snapshot = (
                self.memory.snapshot()
            )

        except Exception:

            memory_snapshot = {}

        return {
            "mission": {
                "goal":
                    self.goal,
                "step":
                    self.step,
                "max_steps":
                    self.MAX_STEPS
            },

            "task_state":
                state_snapshot,

            "memory":
                memory_snapshot,

            "current_stage":
                self.current_stage,

            "completed_actions":
                self.completed_actions[
                    -self.MAX_COMPLETED_ACTIONS:
                ],

            "failed_actions":
                self.failed_actions[
                    -self.MAX_FAILED_ACTIONS:
                ],

            "recent_actions":
                list(
                    self.recent_actions
                ),

            "last_failure":
                self.last_failure,

            "last_decision":
                self.last_decision,

            "observation": {
                "type":
                    "live_screen_observation",
                "available":
                    bool(observation)
            }
        }

    ############################################################
    # EXECUTE
    ############################################################

    def _execute(
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

        print()
        print(
            "[UniversalAgent] ACTION:",
            tool
        )

        print(
            "[UniversalAgent] PARAMETERS:",
            parameters
        )

        ########################################################
        # POLICY
        ########################################################

        try:

            valid, reason = (
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
                    (
                        "Policy validation failed: "
                        f"{exc}"
                    )
            }

        if not valid:

            return {
                "success":
                    False,
                "error":
                    (
                        "Policy rejected action: "
                        f"{reason}"
                    )
            }

        ########################################################
        # TOOLSET
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
                        "Unsupported computer action: "
                        f"{tool}"
                    )
            }

        ########################################################
        # ENGINE
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

            return {
                "success":
                    success,
                "result":
                    self._safe_result(
                        result
                    )
            }

        except Exception as exc:

            return {
                "success":
                    False,
                "error":
                    str(exc)
            }

    ############################################################
    # COMPLETION VERIFICATION
    ############################################################

    def _completion_is_plausible(
        self,
        decision,
        context
    ):

        reason = str(
            decision.get(
                "reason",
                ""
            )
        ).strip()

        if not reason:

            return False

        ########################################################
        # A recent unresolved failure is a reason to distrust
        # an immediate completion claim.
        ########################################################

        if self.last_failure is not None:

            failure_step = (
                self.last_failure.get(
                    "step"
                )
            )

            if failure_step == self.step:

                return False

        ########################################################
        # If actions have actually been completed, completion
        # is plausible.
        #
        # For zero-action tasks, the model may still correctly
        # determine that the requested state already exists.
        ########################################################

        return True

    ############################################################
    # FAILURE REPEAT DETECTION
    ############################################################

    def _is_repeated_failure(
        self,
        action
    ):

        signature = (
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

        count = 0

        for item in self.failed_actions:

            if (
                item.get(
                    "signature"
                )
                ==
                signature
            ):

                count += 1

        return (
            count
            >=
            self.MAX_FAILURES_PER_ACTION
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
    # RECORD STEP
    ############################################################

    def _record_step(
        self,
        reason,
        action,
        result,
        success
    ):

        record = {
            "type":
                "STEP",

            "step":
                self.step,

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
            "step":
                self.step,

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

        self._record_failure(
            tool,
            parameters,
            error
        )

    ############################################################
    # RECORD FAILURE
    ############################################################

    def _record_failure(
        self,
        tool,
        parameters,
        error
    ):

        record = {
            "type":
                "FAILURE",

            "step":
                self.step,

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
    # RECORD NO ACTION
    ############################################################

    def _record_no_action(
        self,
        reason
    ):

        try:

            self.memory.record(
                {
                    "type":
                        "NO_ACTION",

                    "step":
                        self.step,

                    "reason":
                        reason
                }
            )

        except Exception:
            pass

    ############################################################
    # COMPLETE
    ############################################################

    def _complete_task(
        self,
        message
    ):

        try:

            self.memory.record(
                {
                    "type":
                        "TASK_COMPLETED",

                    "goal":
                        self.goal,

                    "step":
                        self.step,

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
        print("=" * 78)
        print(
            "[UniversalAgent] "
            "TASK COMPLETED"
        )
        print(
            "[UniversalAgent]",
            message
        )
        print("=" * 78)

    ############################################################
    # FAIL TASK
    ############################################################

    def _fail_task(
        self,
        message
    ):

        try:

            self.state.fail(
                message
            )

        except Exception:
            pass

        try:

            self.memory.record(
                {
                    "type":
                        "TASK_FAILED",

                    "goal":
                        self.goal,

                    "step":
                        self.step,

                    "message":
                        message
                }
            )

        except Exception:
            pass

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