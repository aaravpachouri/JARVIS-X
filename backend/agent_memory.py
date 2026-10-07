import json


class AgentMemory:
    """
    JARVIS X
    TASK MEMORY LAYER

    AgentMemory does not execute computer actions.

    Its job is to provide the reasoning/execution system with
    a clean interface to the current AgentState.

    It preserves:
        - context()
        - remember()
        - record()
        - artifact()
        - recent()
        - records()
        - get()
        - snapshot()

    It additionally exposes:
        - set_action()
        - set_result()
        - set_action_result()
        - recent_records()
        - current_stage()
        - stages()
    """

    # ==================================================
    # INITIALIZATION
    # ==================================================

    def __init__(
        self,
        state
    ):
        self.state = state

    # ==================================================
    # FULL CONTEXT
    # ==================================================

    def context(
        self
    ):
        """
        Return the complete current task state as JSON.

        This is intended to be supplied to the local AI
        reasoning layer.
        """

        return json.dumps(
            self.state.snapshot(),
            ensure_ascii=False,
            indent=2,
            default=str
        )

    # ==================================================
    # REMEMBER
    # ==================================================

    def remember(
        self,
        key,
        value
    ):
        """
        Store information discovered during execution.
        """

        if hasattr(
            self.state,
            "remember"
        ):
            self.state.remember(
                key,
                value
            )
            return

        # Compatibility fallback.
        self.state.variables[
            str(key)
        ] = value

    # ==================================================
    # GET
    # ==================================================

    def get(
        self,
        key,
        default=None
    ):
        """
        Retrieve a remembered variable.
        """

        key = str(
            key
        )

        if hasattr(
            self.state,
            "get_variable"
        ):
            return self.state.get_variable(
                key,
                default
            )

        return self.state.variables.get(
            key,
            default
        )

    # ==================================================
    # RECORD
    # ==================================================

    def record(
        self,
        data
    ):
        """
        Store a structured execution/data record.
        """

        self.state.add_record(
            data
        )

    # ==================================================
    # ARTIFACT
    # ==================================================

    def artifact(
        self,
        path
    ):
        """
        Register a generated file/artifact.
        """

        self.state.add_artifact(
            str(path or "")
        )

    # ==================================================
    # RECENT HISTORY
    # ==================================================

    def recent(
        self,
        count=10
    ):
        """
        Return recent execution history.
        """

        try:
            count = max(
                1,
                int(count)
            )
        except Exception:
            count = 10

        if hasattr(
            self.state,
            "recent_history"
        ):
            return self.state.recent_history(
                count
            )

        return self.state.history[
            -count:
        ]

    # ==================================================
    # RECORDS
    # ==================================================

    def records(
        self
    ):
        """
        Return all currently stored records.
        """

        return list(
            self.state.records
        )

    # ==================================================

    def recent_records(
        self,
        count=20
    ):
        """
        Return only recent records.
        """

        try:
            count = max(
                1,
                int(count)
            )
        except Exception:
            count = 20

        if hasattr(
            self.state,
            "recent_records"
        ):
            return self.state.recent_records(
                count
            )

        return self.state.records[
            -count:
        ]

    # ==================================================
    # ACTION MEMORY
    # ==================================================

    def set_action(
        self,
        action
    ):
        """
        Store the latest action selected by the planner.
        """

        if hasattr(
            self.state,
            "set_action"
        ):
            self.state.set_action(
                action
            )
        else:
            self.state.last_action = action

    # ==================================================

    def set_result(
        self,
        result
    ):
        """
        Store the latest execution result.
        """

        if hasattr(
            self.state,
            "set_result"
        ):
            self.state.set_result(
                result
            )
        else:
            self.state.last_result = result

    # ==================================================

    def set_action_result(
        self,
        action,
        result
    ):
        """
        Store an action and its corresponding result together.
        """

        if hasattr(
            self.state,
            "set_action_result"
        ):
            self.state.set_action_result(
                action,
                result
            )
            return

        self.set_action(
            action
        )

        self.set_result(
            result
        )

    # ==================================================
    # STAGES
    # ==================================================

    def stages(
        self
    ):
        """
        Return the current task's planned stages.
        """

        return list(
            getattr(
                self.state,
                "stages",
                []
            )
        )

    # ==================================================

    def current_stage(
        self
    ):
        """
        Return the currently active stage name.
        """

        if hasattr(
            self.state,
            "currentStage"
        ):
            return self.state.currentStage()

        return ""

    # ==================================================
    # SNAPSHOT
    # ==================================================

    def snapshot(
        self
    ):
        """
        Return the raw structured state.

        Useful when another component needs a dictionary
        instead of JSON.
        """

        return self.state.snapshot()