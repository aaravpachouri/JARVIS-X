from core.actions import Action
from core.actions import ActionType

from backend.command_normalizer import CommandNormalizer
from backend.intent_parser import IntentParser, Intent
from backend.entity_extractor import EntityExtractor


class Planner:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        self.normalizer = CommandNormalizer()

        self.intentParser = IntentParser()

        self.entityExtractor = EntityExtractor()

        ##################################################
        # INTENT -> ACTION MAP
        ##################################################

        self.actionMap = {

            ##################################################
            # APPLICATIONS
            ##################################################

            Intent.OPEN_APP:
                ActionType.OPEN_APP,

            Intent.CLOSE_APP:
                ActionType.CLOSE_APP,

            ##################################################
            # WEB
            ##################################################

            Intent.SEARCH_WEB:
                ActionType.SEARCH_WEB,

            Intent.OPEN_URL:
                ActionType.OPEN_URL,

            ##################################################
            # FILE SYSTEM
            ##################################################

            Intent.CREATE_FOLDER:
                ActionType.CREATE_FOLDER,

            Intent.CREATE_FILE:
                ActionType.CREATE_FILE,

            Intent.DELETE_FOLDER:
                ActionType.DELETE_FOLDER,

            Intent.DELETE_FILE:
                ActionType.DELETE_FILE,

            Intent.COPY:
                ActionType.COPY,

            Intent.MOVE:
                ActionType.MOVE,

            Intent.RENAME:
                ActionType.RENAME,

            ##################################################
            # MOUSE
            ##################################################

            Intent.MOUSE_MOVE:
                ActionType.MOUSE_MOVE,

            Intent.MOUSE_MOVE_CENTER:
                ActionType.MOUSE_MOVE_CENTER,

            Intent.LEFT_CLICK:
                ActionType.LEFT_CLICK,

            Intent.RIGHT_CLICK:
                ActionType.RIGHT_CLICK,

            Intent.DOUBLE_CLICK:
                ActionType.DOUBLE_CLICK,

            Intent.SCROLL_UP:
                ActionType.SCROLL_UP,

            Intent.SCROLL_DOWN:
                ActionType.SCROLL_DOWN,

            Intent.DRAG:
                ActionType.DRAG,

            ##################################################
            # KEYBOARD
            ##################################################

            Intent.TYPE_TEXT:
                ActionType.TYPE_TEXT,

            Intent.PRESS_KEY:
                ActionType.PRESS_KEY,

            Intent.HOTKEY:
                ActionType.HOTKEY,

            Intent.HOLD_KEY:
                ActionType.HOLD_KEY,

            Intent.RELEASE_KEY:
                ActionType.RELEASE_KEY,

            ##################################################
            # WINDOW
            ##################################################

            Intent.FOCUS_WINDOW:
                ActionType.FOCUS_WINDOW,

            Intent.CLOSE_WINDOW:
                ActionType.CLOSE_WINDOW,

            Intent.MINIMIZE_WINDOW:
                ActionType.MINIMIZE_WINDOW,

            Intent.MAXIMIZE_WINDOW:
                ActionType.MAXIMIZE_WINDOW,

            Intent.RESTORE_WINDOW:
                ActionType.RESTORE_WINDOW,

            Intent.MOVE_WINDOW:
                ActionType.MOVE_WINDOW,

            Intent.RESIZE_WINDOW:
                ActionType.RESIZE_WINDOW,

            ##################################################
            # CLIPBOARD
            ##################################################

            Intent.READ_CLIPBOARD:
                ActionType.READ_CLIPBOARD,

            Intent.WRITE_CLIPBOARD:
                ActionType.WRITE_CLIPBOARD,

            Intent.CLEAR_CLIPBOARD:
                ActionType.CLEAR_CLIPBOARD,

            ##################################################
            # SCREENSHOT
            ##################################################

            Intent.TAKE_SCREENSHOT:
                ActionType.TAKE_SCREENSHOT,

            Intent.TAKE_REGION_SCREENSHOT:
                ActionType.TAKE_REGION_SCREENSHOT,

            Intent.TAKE_WINDOW_SCREENSHOT:
                ActionType.TAKE_WINDOW_SCREENSHOT,

            Intent.SAVE_SCREENSHOT:
                ActionType.SAVE_SCREENSHOT,

            ##################################################
            # OCR
            ##################################################

            Intent.OCR_SCREEN:
                ActionType.OCR_SCREEN,

            Intent.OCR_IMAGE:
                ActionType.OCR_IMAGE,

            ##################################################
            # TERMINAL
            ##################################################

            Intent.RUN_COMMAND:
                ActionType.RUN_COMMAND,

            Intent.RUN_PYTHON:
                ActionType.RUN_PYTHON

        }

    ##################################################
    # PLAN
    ##################################################

    def plan(
        self,
        command
    ):

        ##################################################
        # VALIDATE
        ##################################################

        if command is None:

            return []

        command = str(
            command
        ).strip()

        if not command:

            return []

        ##################################################
        # NORMALIZE
        ##################################################

        command = self.normalizer.normalize(
            command
        )

        ##################################################
        # SPECIAL YOUTUBE WORKFLOW
        ##################################################

        workflow = self._youtubeWorkflow(
            command
        )

        if workflow:

            return workflow

        ##################################################
        # MULTI-STEP COMMANDS
        ##################################################

        connectors = (

            " and then ",

            " then ",

            " after that ",

            " and ",

            ","

        )

        for connector in connectors:

            if connector not in command:

                continue

            parts = command.split(
                connector
            )

            actions = []

            for part in parts:

                part = part.strip()

                if not part:

                    continue

                actions.extend(
                    self.plan(
                        part
                    )
                )

            if actions:

                return actions

        ##################################################
        # INTENT
        ##################################################

        intent = self.intentParser.parse(
            command
        )

        ##################################################
        # ENTITIES
        ##################################################

        entities = self.entityExtractor.extract(
            intent,
            command
        )

        ##################################################
        # ACTION TYPE
        ##################################################

        actionType = self.actionMap.get(
            intent,
            ActionType.UNKNOWN
        )

        ##################################################
        # UNKNOWN
        ##################################################

        if actionType == ActionType.UNKNOWN:

            entities = {
                "command": command
            }

        ##################################################
        # RETURN ACTION
        ##################################################

        return [

            Action(

                action=actionType,

                parameters=entities

            )

        ]

    ##################################################
    # YOUTUBE VISUAL WORKFLOW
    ##################################################

    def _youtubeWorkflow(
        self,
        command
    ):

        import re

        ##################################################
        # NORMALIZE LOCAL TEXT
        ##################################################

        text = str(
            command
        ).strip()

        lower = text.lower()

        ##################################################
        # MUST INVOLVE YOUTUBE
        ##################################################

        if "youtube" not in lower:

            return []

        ##################################################
        # DETECT FIRST VIDEO REQUEST
        ##################################################

        play_first = any(

            phrase in lower

            for phrase in [

                "play the first video",

                "play first video",

                "play the first result",

                "play first result",

                "open the first video",

                "open first video",

                "open the first result",

                "open first result",

                "click the first video",

                "click first video",

                "click the first result",

                "click first result"

            ]

        )

        ##################################################
        # SEARCH PATTERNS
        ##################################################

        patterns = [

            ##################################################
            # OPEN YOUTUBE AND SEARCH X
            ##################################################

            (
                r"(?:open|launch|start)"
                r"\s+youtube"
                r"(?:\s+(?:and|then))?"
                r"\s+search"
                r"(?:\s+for)?"
                r"\s+(.+?)"
                r"(?:\s+and\s+(?:play|open|click)"
                r"(?:\s+the)?"
                r"\s+(?:first\s+)?"
                r"(?:video|result))?$"
            ),

            ##################################################
            # SEARCH YOUTUBE FOR X
            ##################################################

            (
                r"search"
                r"\s+youtube"
                r"\s+for"
                r"\s+(.+?)"
                r"(?:\s+and\s+(?:play|open|click)"
                r"(?:\s+the)?"
                r"\s+(?:first\s+)?"
                r"(?:video|result))?$"
            ),

            ##################################################
            # SEARCH X ON YOUTUBE
            ##################################################

            (
                r"search"
                r"(?:\s+for)?"
                r"\s+(.+?)"
                r"\s+on\s+youtube"
                r"(?:\s+and\s+(?:play|open|click)"
                r"(?:\s+the)?"
                r"\s+(?:first\s+)?"
                r"(?:video|result))?$"
            ),

            ##################################################
            # FIND X ON YOUTUBE
            ##################################################

            (
                r"find"
                r"\s+(.+?)"
                r"\s+on\s+youtube"
                r"(?:\s+and\s+(?:play|open|click)"
                r"(?:\s+the)?"
                r"\s+(?:first\s+)?"
                r"(?:video|result))?$"
            ),

            ##################################################
            # LOOK FOR X ON YOUTUBE
            ##################################################

            (
                r"look\s+for"
                r"\s+(.+?)"
                r"\s+on\s+youtube"
                r"(?:\s+and\s+(?:play|open|click)"
                r"(?:\s+the)?"
                r"\s+(?:first\s+)?"
                r"(?:video|result))?$"
            )

        ]

        ##################################################
        # EXTRACT QUERY
        ##################################################

        query = None

        for pattern in patterns:

            match = re.search(
                pattern,
                lower,
                re.IGNORECASE
            )

            if match:

                query = match.group(
                    1
                ).strip()

                break

        ##################################################
        # NO QUERY
        ##################################################

        if not query:

            return []

        ##################################################
        # CLEAN QUERY
        ##################################################

        query = query.strip(
            " .?!"
        )

        ##################################################
        # REMOVE WORKFLOW SUFFIX
        ##################################################

        query = re.sub(

            r"\s+and\s+"
            r"(?:play|open|click)"
            r"(?:\s+the)?"
            r"\s+(?:first\s+)?"
            r"(?:video|result)"
            r"\s*$",

            "",

            query,

            flags=re.IGNORECASE

        ).strip()

        ##################################################
        # VALIDATE QUERY
        ##################################################

        if not query:

            return []

        ##################################################
        # LOG
        ##################################################

        print(
            "[Planner] YouTube visual workflow"
        )

        ##################################################
        # CREATE WORKFLOW
        ##################################################

        actions = [

            ##################################################
            # OPEN YOUTUBE
            ##################################################

            Action(

                action=ActionType.OPEN_URL,

                parameters={

                    "url":
                        "https://youtube.com"

                }

            ),

            ##################################################
            # WAIT FOR YOUTUBE
            ##################################################

            Action(

                action=ActionType.WAIT,

                parameters={

                    "seconds": 6

                }

            ),

            ##################################################
            # FIND SEARCH
            # CLICK SEARCH
            # TYPE QUERY
            # PRESS ENTER
            ##################################################

            Action(

                action=ActionType.CLICK_TYPE_ENTER,

                parameters={

                    "target":
                        "Search",

                    "text":
                        query

                }

            ),

            ##################################################
            # WAIT FOR RESULTS
            ##################################################

            Action(

                action=ActionType.WAIT,

                parameters={

                    "seconds": 5

                }

            )

        ]

        ##################################################
        # PLAY FIRST VIDEO
        ##################################################

        if play_first:

            actions.append(

                Action(

                    action=
                        ActionType.CLICK_FIRST_VIDEO,

                    parameters={}

                )

            )

        ##################################################
        # RETURN
        ##################################################

        return actions