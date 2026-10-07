import json
from pydoc import text
import re

from ai.client import AIClient
from ai.prompts import SYSTEM_PROMPT
from ai.schema import Action, AIResponse
from ai.validator import AIValidator

from backend.intent.local_intent import LocalIntentEngine


class AIRouter:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        ##################################################
        # GEMINI
        ##################################################

        self.ai = AIClient()

        ##################################################
        # VALIDATOR
        ##################################################

        self.validator = AIValidator()

        ##################################################
        # LOCAL INTENT ENGINE
        ##################################################

        self.localIntent = LocalIntentEngine()

        print(
            "[Router] Local intent engine loaded."
        )

        ##################################################
    # MAIN ROUTER
    ##################################################

    def route(self, command):

        command = str(
            command
        ).strip()

        if not command:

            return AIResponse()

        ##################################################
        # LOCAL COMMAND ROUTER
        #
        # FIRST PRIORITY
        #
        # These commands never touch Gemini.
        ##################################################

        try:

            from ai.local_router import LocalRouter

            if not hasattr(
                self,
                "localRouter"
            ):

                self.localRouter = LocalRouter()

            local_actions = (
                self.localRouter.route(
                    command
                )
            )

        except Exception as e:

            print(
                f"[LocalRouter] Error: {e}"
            )

            local_actions = []

        ##################################################
        # LOCAL ROUTER MATCHED
        ##################################################

        if local_actions:

            print(
                "[Router] LOCAL COMMAND ROUTER"
            )

            response = AIResponse(
                local=True
            )

            for action in local_actions:

                try:

                    tool_name = (
                        action.action.name
                    )

                except Exception:

                    tool_name = str(
                        action.action
                    )

                response.actions.append(
                    Action(
                        tool=tool_name,
                        parameters=(
                            action.parameters
                            or {}
                        )
                    )
                )

            return self.validator.validate(
                response
            )

        ##################################################
        # LOCAL INTENT
        ##################################################

        local_response = self.localRoute(
            command
        )

        if local_response is not None:

            print(
                "[Router] LOCAL INTENT"
            )

            return local_response

        ##################################################
        # EXISTING FAST PATH
        ##################################################

        fast_response = self.fastRoute(
            command
        )

        if fast_response is not None:

            print(
                "[Router] FAST PATH"
            )

            return self.validator.validate(
                fast_response
            )

        ##################################################
        # GEMINI
        #
        # FALLBACK ONLY
        ##################################################

        print(
            "[Router] GEMINI FALLBACK"
        )

        prompt = f"""
{SYSTEM_PROMPT}

User Request:

{command}
"""

        reply = self.ai.chat(
            prompt
        )

        ##################################################
        # PARSE
        ##################################################

        try:

            data = json.loads(
                reply
            )

        except Exception:

            print()
            print("=" * 60)
            print("INVALID AI RESPONSE")
            print("=" * 60)
            print(reply)
            print("=" * 60)

            return AIResponse()

        ##################################################
        # BUILD RESPONSE
        ##################################################

        response = AIResponse()

        for item in data.get(
            "actions",
            []
        ):

            response.actions.append(
                Action(
                    tool=item.get(
                        "tool",
                        ""
                    ),
                    parameters=item.get(
                        "parameters",
                        {}
                    )
                )
            )

        ##################################################
        # VALIDATE
        ##################################################

        return self.validator.validate(
            response
        )
    ##################################################
    # LOCAL ROUTER
    ##################################################

    def localRoute(
        self,
        command
    ):

        result = self.localIntent.predict(
            command,
            minimum_confidence=0.72
        )

        ##################################################
        # UNKNOWN
        ##################################################

        if result is None:

            return None

        intent = str(
            result.intent
        )

        ##################################################
        # CONVERSATION
        ##################################################

        if intent == "GREETING":

            return AIResponse(
                text="Hello, sir.",
                local=True
            )

        if intent == "STATUS":

            return AIResponse(
                text=(
                    "I'm operating perfectly, sir. "
                    "Thank you for asking."
                ),
                local=True
            )

        if intent == "PRESENCE":

            if self._containsAny(
                command,
                (
                    "listening",
                    "hear me"
                )
            ):

                text = (
                    "I'm listening, sir."
                )

            elif self._containsAny(
                command,
                (
                    "ready",
                    "awake"
                )
            ):

                text = (
                    "Always ready, sir."
                )

            else:

                text = (
                    "Always, sir."
                )

            return AIResponse(
                text=text,
                local=True
            )

        if intent == "IDENTITY":

            return AIResponse(
                text=(
                    "I am JARVIS, "
                    "your personal AI assistant."
                ),
                local=True
            )

        if intent == "CAPABILITIES":

            return AIResponse(
                text=(
                    "I can control applications, "
                    "browse the web, manage files, "
                    "interact with your computer, "
                    "read your screen, and assist "
                    "you with tasks, sir."
                ),
                local=True
            )

        if intent == "THANKS":

            return AIResponse(
                text=(
                    "You're welcome, sir."
                ),
                local=True
            )

        if intent == "GOODBYE":

            return AIResponse(
                text=(
                    "Very well, sir."
                ),
                local=True
            )

        if intent == "HELP":

            return AIResponse(
                text=(
                    "Certainly, sir. "
                    "Tell me what you need."
                ),
                local=True
            )

        ##################################################
        # TIME
        ##################################################

        if intent == "TIME":

            from datetime import datetime

            current_time = datetime.now().strftime(
                "%I:%M %p"
            )

            return AIResponse(
                text=(
                    f"The current time is "
                    f"{current_time}, sir."
                ),
                local=True
            )

        ##################################################
        # DATE
        ##################################################

        if intent == "DATE":

            from datetime import datetime

            current_date = datetime.now().strftime(
                "%A, %d %B %Y"
            )

            return AIResponse(
                text=(
                    f"Today is "
                    f"{current_date}, sir."
                ),
                local=True
            )

        ##################################################
        # AUTOMATION INTENTS
        #
        # IMPORTANT:
        # We only use the classifier as an additional
        # recognition layer.
        #
        # The existing fast router remains responsible
        # for extracting parameters.
        ##################################################

        automation_intents = {

            "OPEN_APP",
            "CLOSE_APP",
            "OPEN_URL",
            "SEARCH_WEB",

            "TAKE_SCREENSHOT",
            "OCR_SCREEN",

            "READ_CLIPBOARD",
            "CLEAR_CLIPBOARD",

            "PRESS_KEY",
            "HOTKEY",

            "LEFT_CLICK",
            "RIGHT_CLICK",
            "DOUBLE_CLICK",

            "SCROLL_UP",
            "SCROLL_DOWN",

            "CREATE_FOLDER",
            "CREATE_FILE",

            "DELETE_FILE",
            "DELETE_FOLDER",

            "RUN_COMMAND",
            "RUN_PYTHON",
        }

        if intent in automation_intents:

            return None

        ##################################################
        # UNKNOWN LOCAL INTENT
        ##################################################

        return None

    ##################################################
    # TEXT MATCH HELPER
    ##################################################

    def _containsAny(
        self,
        text,
        words
    ):

        text = str(
            text
        ).lower()

        return any(
            word in text
            for word in words
        )

    ##################################################
    # MULTI-STEP SPLITTER
    ##################################################

    def splitMultiStep(
        self,
        text
    ):

        text = re.sub(
            r"\s+and then\s+",
            "|||",
            text
        )

        text = re.sub(
            r"\s+then\s+",
            "|||",
            text
        )

        text = re.sub(
            r"\s+after that\s+",
            "|||",
            text
        )

        ##################################################
        # AND ONLY WHEN STARTING AN ACTION
        ##################################################

        text = re.sub(
            r"\s+and\s+(?="
            r"open\s+|"
            r"launch\s+|"
            r"start\s+|"
            r"search\s+|"
            r"google\s+|"
            r"click\b|"
            r"right\s+click\b|"
            r"double\s+click\b|"
            r"type\s+|"
            r"press\s+|"
            r"hotkey\s+|"
            r"take\s+|"
            r"capture\s+|"
            r"scroll\s+|"
            r"move\s+mouse\s+|"
            r"create\s+|"
            r"make\s+|"
            r"read\s+clipboard\b|"
            r"clear\s+clipboard\b"
            r")",
            "|||",
            text
        )

        parts = [

            part.strip()

            for part in text.split(
                "|||"
            )

            if part.strip()
        ]

        return parts

    ##################################################
    # FAST ROUTER
    ##################################################

    def fastRoute(self, command):

        text = command.lower().strip()

               ##################################################
        # GENERIC OPEN COMMAND
        ##################################################

        open_match = re.search(
            r"\b(?:"
            r"open|"
            r"opening|"
            r"launch|"
            r"launching|"
            r"start|"
            r"starting|"
            r"visit|"
            r"visiting|"
            r"go to|"
            r"going to|"
            r"bring up|"
            r"bringing up|"
            r"load|"
            r"loading"
            r")\b\s+(.+)",
            text,
            re.IGNORECASE
        )

        if open_match:

            target = open_match.group(1).strip()

            ##################################################
            # REMOVE JARVIS FROM COMMAND
            ##################################################

            target = re.sub(
                r"^(?:hey\s+)?jarvis[\s,]*",
                "",
                target,
                flags=re.IGNORECASE
            ).strip()

            ##################################################
            # REMOVE CONVERSATIONAL PREFIXES
            ##################################################

            target = re.sub(
                r"^(?:"
                r"please\s+|"
                r"can you\s+|"
                r"could you\s+|"
                r"would you\s+|"
                r"will you\s+|"
                r"can u\s+|"
                r"could u\s+|"
                r"would u\s+|"
                r"i want you to\s+|"
                r"i'd like you to\s+|"
                r"i would like you to\s+|"
                r"would you mind\s+|"
                r"do you mind\s+"
                r")+",
                "",
                target,
                flags=re.IGNORECASE
            ).strip()

            ##################################################
            # REMOVE "PLEASE"
            ##################################################

            target = re.sub(
                r"^(?:please\s+)+",
                "",
                target,
                flags=re.IGNORECASE
            ).strip()

            ##################################################
            # REMOVE POLITE ENDINGS
            ##################################################

            target = re.sub(
                r"\s+(?:"
                r"please|"
                r"for me|"
                r"for me please|"
                r"if you can|"
                r"when you can"
                r")$",
                "",
                target,
                flags=re.IGNORECASE
            ).strip()

            ##################################################
            # REMOVE "MY" / "THE"
            ##################################################

            target = re.sub(
                r"^(?:my|the)\s+",
                "",
                target,
                flags=re.IGNORECASE
            ).strip()

            if not target:
                return None

            ##################################################
            # KNOWN WEBSITES
            ##################################################

            websites = {

                "youtube":
                    "https://youtube.com",

                "google":
                    "https://google.com",

                "instagram":
                    "https://instagram.com",

                "facebook":
                    "https://facebook.com",

                "github":
                    "https://github.com",

                "reddit":
                    "https://reddit.com",

                "gmail":
                    "https://gmail.com",

                "twitter":
                    "https://twitter.com",

                "x":
                    "https://x.com",

                "google drive":
                    "https://drive.google.com",

                "google docs":
                    "https://docs.google.com",

            }

            target_lower = target.lower().strip()

            ##################################################
            # WEBSITE
            ##################################################

            if target_lower in websites:

                return AIResponse(
                    actions=[
                        Action(
                            tool="OPEN_URL",
                            parameters={
                                "url":
                                    websites[target_lower]
                            }
                        )
                    ]
                )

            ##################################################
            # DIRECT URL
            ##################################################

            if re.match(
                r"^(?:https?://|www\.)",
                target,
                re.IGNORECASE
            ):

                url = target

                if url.lower().startswith("www."):
                    url = "https://" + url

                return AIResponse(
                    actions=[
                        Action(
                            tool="OPEN_URL",
                            parameters={
                                "url": url
                            }
                        )
                    ]
                )

            ##################################################
            # DOMAIN
            ##################################################

            if re.match(
                r"^[\w-]+\.[a-zA-Z]{2,}(?:/.*)?$",
                target
            ):

                return AIResponse(
                    actions=[
                        Action(
                            tool="OPEN_URL",
                            parameters={
                                "url":
                                    "https://" + target
                            }
                        )
                    ]
                )

            ##################################################
            # EVERYTHING ELSE
            #
            # AppService handles the target.
            ##################################################

            return AIResponse(
                actions=[
                    Action(
                        tool="OPEN_APP",
                        parameters={
                            "app": target
                        }
                    )
                ]
            )

            ##################################################
            # REMOVE EVERYTHING AFTER THE TARGET
            ##################################################

            target = re.sub(
                r"\s+(?:please|"
                r"for me|"
                r"for me please)$",
                "",
                target,
                flags=re.IGNORECASE
            ).strip()

            ##################################################
            # REMOVE COMMON FILLER BEFORE TARGET
            ##################################################

            target = re.sub(
                r"^(?:"
                r"the\s+|"
                r"my\s+"
                r")",
                "",
                target,
                flags=re.IGNORECASE
            ).strip()

            ##################################################
            # WEBSITE SHORTCUTS
            ##################################################

            websites = {

                "youtube":
                    "https://youtube.com",

                "google":
                    "https://google.com",

                "instagram":
                    "https://instagram.com",

                "facebook":
                    "https://facebook.com",

                "github":
                    "https://github.com",

                "reddit":
                    "https://reddit.com",

                "gmail":
                    "https://gmail.com",

                "twitter":
                    "https://twitter.com",

                "x":
                    "https://x.com",

                "google drive":
                    "https://drive.google.com",

                "google docs":
                    "https://docs.google.com",

            }

            target_lower = target.lower()

            ##################################################
            # KNOWN WEBSITE
            ##################################################

            if target_lower in websites:

                return AIResponse(
                    actions=[
                        Action(
                            tool="OPEN_URL",
                            parameters={
                                "url":
                                    websites[target_lower]
                            }
                        )
                    ]
                )

            ##################################################
            # DIRECT URL
            ##################################################

            if re.match(
                r"^(https?://|www\.)",
                target,
                re.IGNORECASE
            ):

                url = target

                if url.lower().startswith("www."):

                    url = "https://" + url

                return AIResponse(
                    actions=[
                        Action(
                            tool="OPEN_URL",
                            parameters={
                                "url": url
                            }
                        )
                    ]
                )

            ##################################################
            # DOMAIN
            ##################################################

            if re.match(
                r"^[\w-]+\.[a-zA-Z]{2,}(?:/.*)?$",
                target
            ):

                return AIResponse(
                    actions=[
                        Action(
                            tool="OPEN_URL",
                            parameters={
                                "url":
                                    "https://" + target
                            }
                        )
                    ]
                )

            ##################################################
            # EVERYTHING ELSE = APPLICATION / FILE / FOLDER
            ##################################################

            return AIResponse(
                actions=[
                    Action(
                        tool="OPEN_APP",
                        parameters={
                            "app": target
                        }
                    )
                ]
            )
        ##################################################
        # MULTI STEP
        ##################################################

        multi_parts = self.splitMultiStep(
            text
        )

        if len(multi_parts) > 1:

            actions = []

            for part in multi_parts:

                action = self.fastSingleCommand(
                    part
                )

                if action is None:

                    return None

                actions.append(
                    action
                )

            return AIResponse(
                actions=actions
            )

        ##################################################
        # SINGLE
        ##################################################

        action = self.fastSingleCommand(
            text
        )

        if action is None:

            return None

        return AIResponse(
            actions=[action]
        )

    ##################################################
    # SINGLE FAST COMMAND
    ##################################################

    def fastSingleCommand(
        self,
        text
    ):

    

               ##################################################
        # YOUTUBE
        ##################################################

        youtube_pattern = re.fullmatch(
            r"(?:"
            r"open|"
            r"go to|"
            r"visit|"
            r"launch|"
            r"start"
            r")\s+"
            r"youtube"
            r"(?:\s+please)?",
            text
        )

        if youtube_pattern:

            return Action(
                tool="OPEN_URL",
                parameters={
                    "url":
                        "https://youtube.com"
                }
            )
        ##################################################
        # SEARCH
        ##################################################

        match = re.fullmatch(
            r"(?:search|google)"
            r"(?:\s+for)?\s+(.+)",
            text
        )

        if match:

            return Action(
                tool="SEARCH_WEB",
                parameters={
                    "query":
                        match.group(1).strip()
                }
            )

        ##################################################
        # OPEN APP
        ##################################################

        match = re.fullmatch(
            r"(?:open|launch|start)\s+(.+)",
            text
        )

        if match:

            return Action(
                tool="OPEN_APP",
                parameters={
                    "app":
                        match.group(1).strip()
                }
            )

        ##################################################
        # MOUSE
        ##################################################

        if text == "click":

            return Action(
                tool="LEFT_CLICK",
                parameters={}
            )

        if text == "right click":

            return Action(
                tool="RIGHT_CLICK",
                parameters={}
            )

        if text == "double click":

            return Action(
                tool="DOUBLE_CLICK",
                parameters={}
            )

        if text == "scroll up":

            return Action(
                tool="SCROLL_UP",
                parameters={}
            )

        if text == "scroll down":

            return Action(
                tool="SCROLL_DOWN",
                parameters={}
            )

        if text in (
            "move mouse to center",
            "center mouse",
            "move to center"
        ):

            return Action(
                tool="MOUSE_MOVE_CENTER",
                parameters={}
            )

        ##################################################
        # MOUSE COORDINATES
        ##################################################

        match = re.fullmatch(
            r"move mouse to\s+(\d+)\s+(\d+)",
            text
        )

        if match:

            return Action(
                tool="MOUSE_MOVE",
                parameters={
                    "x": int(match.group(1)),
                    "y": int(match.group(2))
                }
            )

        ##################################################
        # TYPE
        ##################################################

        match = re.fullmatch(
            r"type\s+(.+)",
            text,
            re.IGNORECASE
        )

        if match:

            return Action(
                tool="TYPE_TEXT",
                parameters={
                    "text":
                        match.group(1)
                }
            )

        ##################################################
        # PRESS
        ##################################################

        match = re.fullmatch(
            r"press\s+(.+)",
            text
        )

        if match:

            return Action(
                tool="PRESS_KEY",
                parameters={
                    "key":
                        match.group(1).strip()
                }
            )

        ##################################################
        # HOTKEY
        ##################################################

        match = re.fullmatch(
            r"hotkey\s+(.+)",
            text
        )

        if match:

            keys = [

                key.strip()

                for key in
                match.group(1).split("+")
            ]

            return Action(
                tool="HOTKEY",
                parameters={
                    "keys": keys
                }
            )

        ##################################################
        # SCREENSHOT
        ##################################################

        if text in (
    "take screenshot",
    "take a screenshot",
    "capture screen",
    "capture my screen",
    "screenshot",
    "take a screen capture",
):

            return Action(
                tool="TAKE_SCREENSHOT",
                parameters={}
            )

        ##################################################
        # CLIPBOARD
        ##################################################

        if text in (
            "read clipboard",
            "show clipboard",
            "clipboard"
        ):

            return Action(
                tool="READ_CLIPBOARD",
                parameters={}
            )

        if text == "clear clipboard":

            return Action(
                tool="CLEAR_CLIPBOARD",
                parameters={}
            )

        ##################################################
        # CREATE FOLDER
        ##################################################

        match = re.fullmatch(
            r"(?:create|make)"
            r"(?: a)? folder"
            r"(?: called| named)?\s+(.+)",
            text
        )

        if match:

            return Action(
                tool="CREATE_FOLDER",
                parameters={
                    "name":
                        match.group(1).strip()
                }
            )

        ##################################################
        # NOTHING
        ##################################################

        return None