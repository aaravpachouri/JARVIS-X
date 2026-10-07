import re
from urllib.parse import quote_plus

from core.actions import Action, ActionType


class LocalRouter:

    def route(self, command):

        text = str(command or "").strip()
        lower = text.lower()

        if not text:
            return []

                # -----------------------------------------------
        # OPEN APPLICATION
        # -----------------------------------------------

        match = re.fullmatch(
            r"(?:jarvis\s+)?open\s+(.+)",
            lower
        )

        if match:

            target = match.group(1).strip()

            # Do NOT consume multi-step commands.
            multi_step_markers = (
                " and ",
                " then ",
                " after that ",
            )

            if not any(
                marker in target
                for marker in multi_step_markers
            ):

                known_apps = {
                    "chrome": "chrome",
                    "google chrome": "chrome",
                    "edge": "msedge",
                    "microsoft edge": "msedge",
                    "notepad": "notepad",
                    "calculator": "calc",
                    "calc": "calc",
                    "file explorer": "explorer",
                    "explorer": "explorer",
                    "vscode": "code",
                    "vs code": "code",
                }

                app = known_apps.get(
                    target
                )

                if app:

                    return [
                        Action(
                            action=ActionType.OPEN_APP,
                            parameters={
                                "app": app
                            }
                        )
                    ]

        # -----------------------------------------------
        # OPEN WEBSITE
        # -----------------------------------------------

        sites = {
            "youtube":
                "https://www.youtube.com",

            "google":
                "https://www.google.com",

            "gmail":
                "https://mail.google.com",

            "whatsapp":
                "https://web.whatsapp.com",

            "instagram":
                "https://www.instagram.com",

            "facebook":
                "https://www.facebook.com",

            "amazon":
                "https://www.amazon.in",

            "flipkart":
                "https://www.flipkart.com",
        }

        for name, url in sites.items():

            if re.fullmatch(
                rf"(?:jarvis\s+)?open\s+{re.escape(name)}",
                lower
            ):

                return [
                    Action(
                        action=ActionType.OPEN_URL,
                        parameters={
                            "url": url
                        }
                    )
                ]

        # -----------------------------------------------
        # GOOGLE SEARCH
        # -----------------------------------------------

        match = re.fullmatch(
            r"(?:jarvis\s+)?(?:search\s+google\s+for|google\s+search|search\s+for)\s+(.+)",
            lower
        )

        if match:

            query = match.group(1).strip()

            url = (
                "https://www.google.com/search?q="
                + quote_plus(query)
            )

            return [
                Action(
                    action=ActionType.OPEN_URL,
                    parameters={
                        "url": url
                    }
                )
            ]

        # -----------------------------------------------
        # YOUTUBE SEARCH
        # -----------------------------------------------

        match = re.fullmatch(
            r"(?:jarvis\s+)?(?:youtube\s+)?search\s+(.+)",
            lower
        )

        if (
            match
            and (
                "youtube" in lower
                or lower.startswith("search ")
            )
        ):

            query = match.group(1).strip()

            url = (
                "https://www.youtube.com/results?search_query="
                + quote_plus(query)
            )

            return [
                Action(
                    action=ActionType.OPEN_URL,
                    parameters={
                        "url": url
                    }
                )
            ]

        # -----------------------------------------------
        # TYPE TEXT
        # -----------------------------------------------

        match = re.fullmatch(
            r"(?:jarvis\s+)?type\s+(.+)",
            text,
            flags=re.I
        )

        if match:

            return [
                Action(
                    action=ActionType.TYPE_TEXT,
                    parameters={
                        "text":
                            match.group(1)
                    }
                )
            ]

        # -----------------------------------------------
        # PRESS KEY
        # -----------------------------------------------

        match = re.fullmatch(
            r"(?:jarvis\s+)?press\s+(.+)",
            lower
        )

        if match:

            return [
                Action(
                    action=ActionType.PRESS_KEY,
                    parameters={
                        "key":
                            match.group(1)
                    }
                )
            ]

        # -----------------------------------------------
        # VOLUME
        # -----------------------------------------------

        if "volume up" in lower:

            return [
                Action(
                    action=ActionType.PRESS_KEY,
                    parameters={
                        "key": "volumeup"
                    }
                )
            ]

        if "volume down" in lower:

            return [
                Action(
                    action=ActionType.PRESS_KEY,
                    parameters={
                        "key": "volumedown"
                    }
                )
            ]

        if (
            "mute" in lower
            or "unmute" in lower
        ):

            return [
                Action(
                    action=ActionType.PRESS_KEY,
                    parameters={
                        "key": "volumemute"
                    }
                )
            ]

        # -----------------------------------------------
        # MEDIA
        # -----------------------------------------------

        if lower in (
            "play",
            "play video",
            "play the video"
        ):

            return [
                Action(
                    action=ActionType.PRESS_KEY,
                    parameters={
                        "key": "space"
                    }
                )
            ]

        if lower in (
            "pause",
            "pause video",
            "pause the video"
        ):

            return [
                Action(
                    action=ActionType.PRESS_KEY,
                    parameters={
                        "key": "space"
                    }
                )
            ]

        if "fullscreen" in lower:

            return [
                Action(
                    action=ActionType.PRESS_KEY,
                    parameters={
                        "key": "f"
                    }
                )
            ]

        # -----------------------------------------------
        # SCROLL
        # -----------------------------------------------

        if (
            "scroll down" in lower
            or "scroll lower" in lower
        ):

            return [
                Action(
                    action=ActionType.SCROLL_DOWN,
                    parameters={}
                )
            ]

        if (
            "scroll up" in lower
            or "scroll higher" in lower
        ):

            return [
                Action(
                    action=ActionType.SCROLL_UP,
                    parameters={}
                )
            ]

        # -----------------------------------------------
        # GO BACK
        # -----------------------------------------------

        if lower in (
            "go back",
            "back",
            "go back one page"
        ):

            return [
                Action(
                    action=ActionType.HOTKEY,
                    parameters={
                        "keys": [
                            "alt",
                            "left"
                        ]
                    }
                )
            ]

        # -----------------------------------------------
        # SCREENSHOT
        # -----------------------------------------------

        if (
            "take a screenshot" in lower
            or lower == "screenshot"
        ):

            return [
                Action(
                    action=ActionType.TAKE_SCREENSHOT,
                    parameters={}
                )
            ]

        # -----------------------------------------------
        # NOTHING MATCHED
        # -----------------------------------------------

        return []