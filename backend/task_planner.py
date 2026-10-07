import re


class TaskPlanner:

    """
    JARVIS X
    OUTCOME-ORIENTED GENERIC TASK PLANNER

    This planner does NOT execute computer actions.

    Its job is to convert a user's complete natural-language
    objective into a sequence of meaningful mission stages.

    IMPORTANT:

    - No application-specific workflows.
    - No hardcoded Calculator workflow.
    - No hardcoded Notepad workflow.
    - No hardcoded browser workflow.
    - No coordinate logic.
    - No executor logic.

    The planner describes WHAT must become true.

    ComputerUseAgent remains responsible for deciding HOW
    to make those outcomes true using the current computer
    state.
    """

    ############################################################
    # CONFIGURATION
    ############################################################

    MAX_STAGES = 12

    ############################################################
    # INITIALIZATION
    ############################################################

    def __init__(
        self
    ):

        self.last_goal = ""

        self.last_plan = []

    ############################################################
    # PLAN
    ############################################################

    def plan(
        self,
        goal
    ):
        """
        Convert the user's complete objective into a list
        of generic outcome-oriented mission stages.
        """

        goal = str(
            goal or ""
        ).strip()

        self.last_goal = goal

        self.last_plan = []

        if not goal:

            return []

        ########################################################
        # NORMALIZE
        ########################################################

        text = self._normalize_goal(
            goal
        )

        ########################################################
        # SPLIT INTO NATURAL MISSION UNITS
        ########################################################

        parts = (
            self._split_sequence(
                text
            )
        )

        ########################################################
        # CLEAN
        ########################################################

        cleaned = []

        for part in parts:

            part = str(
                part or ""
            ).strip(
                " ,.;"
            )

            if not part:

                continue

            cleaned.append(
                part
            )

        ########################################################
        # FALLBACK
        ########################################################

        if not cleaned:

            cleaned = [
                goal
            ]

        ########################################################
        # LIMIT
        ########################################################

        cleaned = cleaned[
            :self.MAX_STAGES
        ]

        ########################################################
        # BUILD OUTCOME-ORIENTED STAGES
        ########################################################

        result = []

        for part in cleaned:

            stage = (
                self._build_stage(
                    part
                )
            )

            if stage:

                result.append(
                    stage
                )

        ########################################################
        # FINAL FALLBACK
        ########################################################

        if not result:

            result = [
                self._build_stage(
                    goal
                )
            ]

        self.last_plan = list(
            result
        )

        return list(
            result
        )

    ############################################################
    # NORMALIZE GOAL
    ############################################################

    @staticmethod
    def _normalize_goal(
        goal
    ):

        text = str(
            goal or ""
        ).strip()

        if not text:

            return ""

        ########################################################
        # Normalize whitespace without altering user meaning.
        ########################################################

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text

    ############################################################
    # SPLIT SEQUENCE
    ############################################################

    def _split_sequence(
        self,
        goal
    ):
        """
        Split a natural-language mission into meaningful
        sequential objectives.

        The original wording is preserved as much as possible.
        """

        text = str(
            goal or ""
        ).strip()

        if not text:

            return []

        ########################################################
        # Strong explicit sequence connectors
        ########################################################

        parts = re.split(
            r"\s+(?:"
            r"and then"
            r"|then"
            r"|after that"
            r"|afterwards"
            r"|followed by"
            r"|next"
            r"|once that is done"
            r"|once done"
            r")\s+",
            text,
            flags=re.IGNORECASE
        )

        ########################################################
        # If explicit sequencing did not separate the mission,
        # detect action-chain "and".
        ########################################################

        if len(parts) == 1:

            parts = re.split(
                r"\s+and\s+(?="
                r"open\s+|"
                r"launch\s+|"
                r"start\s+|"
                r"close\s+|"
                r"quit\s+|"
                r"type\s+|"
                r"write\s+|"
                r"enter\s+|"
                r"click\s+|"
                r"double\s+click\s+|"
                r"right\s+click\s+|"
                r"search\s+|"
                r"find\s+|"
                r"look\s+for\s+|"
                r"create\s+|"
                r"make\s+|"
                r"save\s+|"
                r"download\s+|"
                r"upload\s+|"
                r"copy\s+|"
                r"move\s+|"
                r"rename\s+|"
                r"scroll\s+|"
                r"press\s+|"
                r"calculate\s+|"
                r"compute\s+|"
                r"check\s+|"
                r"verify\s+|"
                r"use\s+|"
                r"send\s+|"
                r"read\s+|"
                r"open\s+"
                r")",
                text,
                flags=re.IGNORECASE
            )

        ########################################################
        # Clean accidental empty entries.
        ########################################################

        return [
            part.strip()
            for part in parts
            if str(
                part or ""
            ).strip()
        ]

    ############################################################
    # BUILD STAGE
    ############################################################

    def _build_stage(
        self,
        stage
    ):
        """
        Convert one user objective into a generic
        outcome-oriented stage description.

        The wording intentionally focuses on the required
        outcome rather than a fixed action sequence.
        """

        original = str(
            stage or ""
        ).strip()

        if not original:

            return ""

        lower = original.lower()

        category = (
            self._classify_stage(
                lower
            )
        )

        ########################################################
        # Outcome wording
        ########################################################

        if category == "research":

            return (
                "Research/Resolve: "
                f"{original} "
                "| Outcome: obtain and verify the information "
                "required by this stage."
            )

        if category == "creation":

            return (
                "Create/Produce: "
                f"{original} "
                "| Outcome: the requested content or artifact "
                "exists in the required state."
            )

        if category == "file":

            return (
                "File/Data Operation: "
                f"{original} "
                "| Outcome: the requested file or data state "
                "exists and is verified."
            )

        if category == "verification":

            return (
                "Verify: "
                f"{original} "
                "| Outcome: the requested condition is visibly "
                "or observably confirmed."
            )

        if category == "transfer":

            return (
                "Transfer/Use Result: "
                f"{original} "
                "| Outcome: the required result has been "
                "successfully transferred or used."
            )

        ########################################################
        # DEFAULT
        ########################################################

        return (
            "Mission Objective: "
            f"{original} "
            "| Outcome: the objective described in this stage "
            "is visibly or observably achieved."
        )

    ############################################################
    # CLASSIFY STAGE
    ############################################################

    @staticmethod
    def _classify_stage(
        text
    ):
        """
        Generic semantic classification only.

        This does NOT decide how the computer should execute
        the stage.
        """

        text = str(
            text or ""
        ).lower()

        ########################################################
        # RESEARCH / INFORMATION
        ########################################################

        if TaskPlanner._contains_any(
            text,
            (
                "research",
                "search",
                "find",
                "look for",
                "look up",
                "google",
                "calculate",
                "compute",
                "determine",
                "figure out",
                "work out",
            )
        ):

            return "research"

        ########################################################
        # FILE / DATA OPERATIONS
        ########################################################

        if TaskPlanner._contains_any(
            text,
            (
                "save",
                "download",
                "upload",
                "copy",
                "move",
                "rename",
                "delete",
                "organize",
                "file",
                "folder",
            )
        ):

            return "file"

        ########################################################
        # TRANSFER / USING A RESULT
        ########################################################

        if TaskPlanner._contains_any(
            text,
            (
                "use the result",
                "use that result",
                "put the result",
                "type the result",
                "enter the result",
                "send the result",
                "transfer",
                "paste the result",
            )
        ):

            return "transfer"

        ########################################################
        # VERIFICATION
        ########################################################

        if TaskPlanner._contains_any(
            text,
            (
                "check",
                "verify",
                "confirm",
                "make sure",
                "ensure",
                "validate",
            )
        ):

            return "verification"

        ########################################################
        # CREATION
        ########################################################

        if TaskPlanner._contains_any(
            text,
            (
                "create",
                "make",
                "write",
                "type",
                "enter",
                "compose",
                "produce",
                "generate",
            )
        ):

            return "creation"

        ########################################################
        # DEFAULT
        ########################################################

        return "execute"

    ############################################################
    # CONTAINS ANY
    ############################################################

    @staticmethod
    def _contains_any(
        text,
        words
    ):

        text = str(
            text or ""
        ).lower()

        return any(
            word in text
            for word in words
        )

    ############################################################
    # CURRENT PLAN
    ############################################################

    def current_plan(
        self
    ):

        return list(
            self.last_plan
        )

    ############################################################
    # LAST GOAL
    ############################################################

    def current_goal(
        self
    ):

        return self.last_goal

    ############################################################
    # PLAN COUNT
    ############################################################

    def stage_count(
        self
    ):

        return len(
            self.last_plan
        )

    ############################################################
    # RESET
    ############################################################

    def reset(
        self
    ):

        self.last_goal = ""

        self.last_plan = []

    ############################################################
    # REPRESENTATION
    ############################################################

    def __repr__(
        self
    ):

        return (
            "<TaskPlanner "
            f"stages={len(self.last_plan)}>"
        )