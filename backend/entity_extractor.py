import re

from backend.intent_parser import Intent


class EntityExtractor:

    ##################################################

    def __init__(self):

        pass

    ##################################################

    def extract(self, intent, command):

        text = command.lower().strip()

        ##################################################
        # APPLICATIONS
        ##################################################

        if intent == Intent.OPEN_APP:

            return {

                "app": re.sub(

                    r"^(open|launch|start)\s+",

                    "",

                    text

                ).strip()

            }

        ##################################################
        # SEARCH WEB
        ##################################################

        if intent == Intent.SEARCH_WEB:

            return {

                "query": re.sub(

                    r"^(search|google)\s+",

                    "",

                    text

                ).strip()

            }

        ##################################################
        # OPEN URL
        ##################################################

        if intent == Intent.OPEN_URL:

            url = re.sub(

                r"^(open|launch|start)\s+",

                "",

                command,

                flags=re.IGNORECASE

            ).strip()

            if not url.startswith(

                ("http://", "https://")

            ):

                if "." not in url:

                    url += ".com"

                url = "https://" + url

            return {

                "url": url

            }

        ##################################################
        # FILE SYSTEM
        ##################################################

        if intent == Intent.CREATE_FOLDER:

            patterns = (

                r"create folder (.+)",

                r"create a folder (.+)",

                r"make folder (.+)",

                r"make a folder (.+)",

                r"create folder called (.+)",

                r"create folder named (.+)",

                r"make folder called (.+)",

                r"make folder named (.+)"

            )

            for pattern in patterns:

                match = re.search(

                    pattern,

                    text

                )

                if match:

                    return {

                        "name": match.group(1).strip()

                    }

            return {}

        ##################################################
        # MOUSE
        ##################################################

        if intent in (

            Intent.MOUSE_MOVE,

            Intent.DRAG

        ):

            numbers = re.findall(

                r"\d+",

                text

            )

            if len(numbers) >= 2:

                return {

                    "x": int(numbers[0]),

                    "y": int(numbers[1])

                }

            return {}

        ##################################################

        if intent in (

            Intent.MOUSE_MOVE_CENTER,

            Intent.LEFT_CLICK,

            Intent.RIGHT_CLICK,

            Intent.DOUBLE_CLICK,

            Intent.SCROLL_UP,

            Intent.SCROLL_DOWN

        ):

            return {}

        ##################################################
        # KEYBOARD
        ##################################################

        if intent == Intent.TYPE_TEXT:

            return {

                "text": command[5:].strip()

            }

        ##################################################

        if intent == Intent.PRESS_KEY:

            return {

                "key": command[6:].strip().lower()

            }

        ##################################################

        if intent == Intent.HOTKEY:

            return {

                "keys": [

                    key.strip().lower()

                    for key in command[7:].split("+")

                ]

            }

        ##################################################

        if intent == Intent.HOLD_KEY:

            return {

                "key": command[5:].strip().lower()

            }

        ##################################################

        if intent == Intent.RELEASE_KEY:

            return {

                "key": command[8:].strip().lower()

            }

        ##################################################
        # WINDOW
        ##################################################

        if intent in (

            Intent.FOCUS_WINDOW,

            Intent.CLOSE_WINDOW,

            Intent.MINIMIZE_WINDOW,

            Intent.MAXIMIZE_WINDOW,

            Intent.RESTORE_WINDOW

        ):

            prefixes = {

                Intent.FOCUS_WINDOW: r"^(focus|activate)\s+",

                Intent.CLOSE_WINDOW: r"^close window\s+",

                Intent.MINIMIZE_WINDOW: r"^minimize\s+",

                Intent.MAXIMIZE_WINDOW: r"^maximize\s+",

                Intent.RESTORE_WINDOW: r"^restore\s+"

            }

            return {

                "window": re.sub(

                    prefixes[intent],

                    "",

                    command,

                    flags=re.IGNORECASE

                ).strip()

            }

        ##################################################

        if intent == Intent.MOVE_WINDOW:

            numbers = re.findall(

                r"\d+",

                command

            )

            if len(numbers) >= 2:

                return {

                    "window": re.sub(

                        r"\d+",

                        "",

                        re.sub(

                            r"^move window\s+",

                            "",

                            command,

                            flags=re.IGNORECASE

                        )

                    ).strip(),

                    "x": int(numbers[0]),

                    "y": int(numbers[1])

                }

            return {}

        ##################################################

        if intent == Intent.RESIZE_WINDOW:

            numbers = re.findall(

                r"\d+",

                command

            )

            if len(numbers) >= 2:

                return {

                    "window": re.sub(

                        r"\d+",

                        "",

                        re.sub(

                            r"^resize window\s+",

                            "",

                            command,

                            flags=re.IGNORECASE

                        )

                    ).strip(),

                    "width": int(numbers[0]),

                    "height": int(numbers[1])

                }

            return {}

        ##################################################
        # CLIPBOARD
        ##################################################

        if intent == Intent.READ_CLIPBOARD:

            return {}

        ##################################################

        if intent == Intent.WRITE_CLIPBOARD:

            return {

                "text": re.sub(

                    r"^(copy|write clipboard)\s+",

                    "",

                    command,

                    flags=re.IGNORECASE

                ).strip()

            }

        ##################################################

        if intent == Intent.CLEAR_CLIPBOARD:

            return {}

        ##################################################
        # SCREENSHOT
        ##################################################

        if intent in (

            Intent.TAKE_SCREENSHOT,

            Intent.TAKE_REGION_SCREENSHOT,

            Intent.TAKE_WINDOW_SCREENSHOT

        ):

            return {}

        ##################################################

        if intent == Intent.SAVE_SCREENSHOT:

            match = re.search(

                r"save screenshot(?: as)? (.+)",

                text

            )

            if match:

                return {

                    "filename": match.group(1).strip()

                }

            return {}

        ##################################################
        # OCR
        ##################################################

        if intent == Intent.OCR_SCREEN:

            return {

                "image": "desktop.png"

            }

        ##################################################

        if intent == Intent.OCR_IMAGE:

            image = re.sub(

                r"^(read image|ocr image)\s+",

                "",

                command,

                flags=re.IGNORECASE

            )

            return {

                "image": image.strip()

            }

        ##################################################
        # TERMINAL
        ##################################################

        if intent == Intent.RUN_COMMAND:

            return {

                "command": re.sub(

                    r"^(run|execute)\s+",

                    "",

                    command,

                    flags=re.IGNORECASE

                ).strip()

            }

        ##################################################

        if intent == Intent.RUN_PYTHON:

            return {

                "script": command[7:].strip()

            }

        ##################################################

        return {}