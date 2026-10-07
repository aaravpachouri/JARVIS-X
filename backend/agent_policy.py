class AgentPolicy:

    """
    JARVIS X
    COMPUTER ACTION SAFETY / VALIDATION POLICY

    The AI may decide WHAT should happen.

    This class decides whether the requested computer action
    is permitted to reach the executor.

    IMPORTANT:

    - AutomationEngine is the source of truth for executable
      computer capabilities.
    - This policy is responsible for safety and permission.
    - The policy does NOT create or execute actions.
    - High-risk operations remain blocked independently.
    """

    ############################################################
    # INTERNAL AGENT OPERATIONS
    ############################################################

    INTERNAL_ACTIONS = {
        "RECORD",
        "REMEMBER",
        "CREATE_SPREADSHEET",
        "APPEND_SPREADSHEET",
        "FINISH",
    }

    ############################################################
    # HIGH-RISK ACTIONS
    ############################################################

    HIGH_RISK = {
        "DELETE_FILE",
        "DELETE_FOLDER",
        "SHUTDOWN",
        "RESTART",
        "SLEEP",
    }

    ############################################################
    # ACTION ALIASES
    ############################################################

    ACTION_ALIASES = {

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

        "KEYBOARD_PRESS":
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
            "WAIT",
    }

    ############################################################
    # INITIALIZATION
    ############################################################

    def __init__(
        self,
        engine=None
    ):

        self.engine = engine

        ########################################################
        # The executable capability set is deliberately derived
        # from the engine.
        #
        # This prevents AgentPolicy from becoming another
        # hardcoded list of capabilities.
        ########################################################

        self.refresh()

    ############################################################
    # REFRESH
    ############################################################

    def refresh(
        self
    ):

        self.SAFE_ACTIONS = (
            self._build_executable_actions()
        )

        return set(
            self.SAFE_ACTIONS
        )

    ############################################################
    # BUILD EXECUTABLE ACTIONS
    ############################################################

    def _build_executable_actions(
        self
    ):

        actions = set()

        ########################################################
        # The AutomationEngine is the source of truth.
        ########################################################

        if self.engine is not None:

            routes = getattr(
                self.engine,
                "routes",
                {}
            )

            if isinstance(
                routes,
                dict
            ):

                for action_type in routes.keys():

                    name = getattr(
                        action_type,
                        "name",
                        None
                    )

                    if name:

                        actions.add(
                            str(
                                name
                            ).upper().strip()
                        )

        ########################################################
        # Internal agent operations do not travel through the
        # AutomationEngine. ComputerUseAgent handles them
        # directly.
        ########################################################

        actions.update(
            self.INTERNAL_ACTIONS
        )

        ########################################################
        # High-risk actions are never added as safe actions.
        ########################################################

        actions.difference_update(
            self.HIGH_RISK
        )

        return actions

    ############################################################
    # NORMALIZE TOOL
    ############################################################

    def normalize_tool(
        self,
        tool
    ):

        name = str(
            tool or ""
        ).upper().strip()

        return self.ACTION_ALIASES.get(
            name,
            name
        )

    ############################################################
    # VALIDATE
    ############################################################

    def validate(
        self,
        tool,
        parameters
    ):

        tool = (
            self.normalize_tool(
                tool
            )
        )

        ########################################################
        # PARAMETER TYPE
        ########################################################

        if not isinstance(
            parameters,
            dict
        ):

            return (
                False,
                "parameters must be an object"
            )

        ########################################################
        # HIGH-RISK ACTION
        ########################################################

        if tool in self.HIGH_RISK:

            return (
                False,
                "high-risk action requires explicit confirmation"
            )

        ########################################################
        # UNKNOWN / NON-EXECUTABLE ACTION
        ########################################################

        if tool not in self.SAFE_ACTIONS:

            return (
                False,
                f"unsupported computer action: {tool}"
            )

        ########################################################
        # VALID
        ########################################################

        return (
            True,
            "ok"
        )

    ############################################################
    # SANITIZE
    ############################################################

    def sanitize(
        self,
        actions
    ):

        clean = []

        if not isinstance(
            actions,
            list
        ):

            return clean

        for item in actions:

            normalized = (
                self.sanitize_action(
                    item
                )
            )

            if normalized is not None:

                clean.append(
                    normalized
                )

        return clean

    ############################################################
    # SANITIZE ONE ACTION
    ############################################################

    def sanitize_action(
        self,
        action
    ):

        if not isinstance(
            action,
            dict
        ):

            return None

        tool = (
            self.normalize_tool(
                action.get(
                    "tool",
                    ""
                )
            )
        )

        parameters = action.get(
            "parameters",
            {}
        )

        if not isinstance(
            parameters,
            dict
        ):

            parameters = {}

        valid, _ = (
            self.validate(
                tool,
                parameters
            )
        )

        if not valid:

            return None

        return {
            "tool":
                tool,

            "parameters":
                dict(
                    parameters
                )
        }

    ############################################################
    # IS SAFE
    ############################################################

    def is_safe(
        self,
        tool,
        parameters=None
    ):

        if parameters is None:

            parameters = {}

        valid, _ = (
            self.validate(
                tool,
                parameters
            )
        )

        return valid

    ############################################################
    # IS HIGH RISK
    ############################################################

    def is_high_risk(
        self,
        tool
    ):

        tool = (
            self.normalize_tool(
                tool
            )
        )

        return (
            tool in self.HIGH_RISK
        )

    ############################################################
    # REASON
    ############################################################

    def reason(
        self,
        tool,
        parameters=None
    ):

        if parameters is None:

            parameters = {}

        _, reason = (
            self.validate(
                tool,
                parameters
            )
        )

        return reason

    ############################################################
    # AVAILABLE SAFE ACTIONS
    ############################################################

    def available(
        self
    ):

        return sorted(
            self.SAFE_ACTIONS
        )