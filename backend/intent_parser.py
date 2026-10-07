from enum import Enum, auto


class Intent(Enum):

    ##################################################
    # APPLICATIONS
    ##################################################

    OPEN_APP = auto()
    CLOSE_APP = auto()

    ##################################################
    # WEB
    ##################################################

    SEARCH_WEB = auto()
    OPEN_URL = auto()

    ##################################################
    # FILE SYSTEM
    ##################################################

    CREATE_FOLDER = auto()
    CREATE_FILE = auto()

    DELETE_FOLDER = auto()
    DELETE_FILE = auto()

    COPY = auto()
    MOVE = auto()
    RENAME = auto()

    ##################################################
    # MOUSE
    ##################################################

    MOUSE_MOVE = auto()
    MOUSE_MOVE_CENTER = auto()

    LEFT_CLICK = auto()
    RIGHT_CLICK = auto()
    DOUBLE_CLICK = auto()

    SCROLL_UP = auto()
    SCROLL_DOWN = auto()

    DRAG = auto()

    ##################################################
    # KEYBOARD
    ##################################################

    TYPE_TEXT = auto()

    PRESS_KEY = auto()

    HOTKEY = auto()

    HOLD_KEY = auto()

    RELEASE_KEY = auto()

    ##################################################
    # WINDOW
    ##################################################

    FOCUS_WINDOW = auto()

    CLOSE_WINDOW = auto()

    MINIMIZE_WINDOW = auto()

    MAXIMIZE_WINDOW = auto()

    RESTORE_WINDOW = auto()

    MOVE_WINDOW = auto()

    RESIZE_WINDOW = auto()

    ##################################################
    # CLIPBOARD
    ##################################################

    READ_CLIPBOARD = auto()

    WRITE_CLIPBOARD = auto()

    CLEAR_CLIPBOARD = auto()

    ##################################################
    # SCREENSHOT
    ##################################################

    TAKE_SCREENSHOT = auto()

    TAKE_REGION_SCREENSHOT = auto()

    TAKE_WINDOW_SCREENSHOT = auto()

    SAVE_SCREENSHOT = auto()

    ##################################################
    # OCR
    ##################################################

    OCR_SCREEN = auto()

    OCR_IMAGE = auto()

    ##################################################
    # TERMINAL
    ##################################################

    RUN_COMMAND = auto()

    RUN_PYTHON = auto()

    ##################################################

    UNKNOWN = auto()


class IntentParser:

    ##################################################

    def __init__(self):

        self.website_keywords = {

            "google",
            "youtube",
            "gmail",
            "github",
            "chatgpt",
            "facebook",
            "instagram",
            "linkedin",
            "twitter",
            "x",
            "reddit",
            "stackoverflow",
            "amazon",
            "netflix",
            "spotify"

        }

    ##################################################

    def parse(self, command):

        text = command.lower().strip()

        ##################################################
        # OPEN
        ##################################################

        if text.startswith(("open ", "launch ", "start ")):

            target = text.split(" ", 1)[1].strip()

            ##################################################
            # WEBSITE
            ##################################################

            if (

                target.startswith(("http://", "https://"))

                or "." in target

                or target in self.website_keywords

            ):

                return Intent.OPEN_URL

            ##################################################
            # APPLICATION
            ##################################################

            return Intent.OPEN_APP

        ##################################################
        # SEARCH
        ##################################################

        if text.startswith(("search ", "google ")):

            return Intent.SEARCH_WEB

        ##################################################
        # FILE SYSTEM
        ##################################################

        if any(

            phrase in text

            for phrase in (

                "create folder",

                "make folder",

                "create a folder",

                "make a folder"

            )

        ):

            return Intent.CREATE_FOLDER

        ##################################################

        if any(

            phrase in text

            for phrase in (

                "create file",

                "make file",

                "new file"

            )

        ):

            return Intent.CREATE_FILE

        ##################################################
        # MOUSE
        ##################################################

        if text in (

            "move mouse to center",

            "center mouse",

            "move to center"

        ):

            return Intent.MOUSE_MOVE_CENTER

        if text.startswith("move mouse to "):

            return Intent.MOUSE_MOVE

        if text == "click":

            return Intent.LEFT_CLICK

        if text == "right click":

            return Intent.RIGHT_CLICK

        if text == "double click":

            return Intent.DOUBLE_CLICK

        if text == "scroll up":

            return Intent.SCROLL_UP

        if text == "scroll down":

            return Intent.SCROLL_DOWN

        if text.startswith("drag"):

            return Intent.DRAG

        ##################################################
        # KEYBOARD
        ##################################################

        if text.startswith("type "):

            return Intent.TYPE_TEXT

        if text.startswith("press "):

            return Intent.PRESS_KEY

        if text.startswith("hotkey "):

            return Intent.HOTKEY

        if text.startswith("hold "):

            return Intent.HOLD_KEY

        if text.startswith("release "):

            return Intent.RELEASE_KEY

        ##################################################
        # WINDOW
        ##################################################

        if text.startswith(("focus ", "activate ")):

            return Intent.FOCUS_WINDOW

        if text.startswith("close window"):

            return Intent.CLOSE_WINDOW

        if text.startswith("minimize"):

            return Intent.MINIMIZE_WINDOW

        if text.startswith("maximize"):

            return Intent.MAXIMIZE_WINDOW

        if text.startswith("restore"):

            return Intent.RESTORE_WINDOW

        if text.startswith("move window"):

            return Intent.MOVE_WINDOW

        if text.startswith("resize window"):

            return Intent.RESIZE_WINDOW

        ##################################################
        # CLIPBOARD
        ##################################################

        if text in (

            "clipboard",

            "read clipboard",

            "show clipboard"

        ):

            return Intent.READ_CLIPBOARD

        if text.startswith(("copy ", "write clipboard ")):

            return Intent.WRITE_CLIPBOARD

        if text == "clear clipboard":

            return Intent.CLEAR_CLIPBOARD

        ##################################################
        # SCREENSHOT
        ##################################################

        if text in (

            "take screenshot",

            "capture screen",

            "screenshot"

        ):

            return Intent.TAKE_SCREENSHOT

        if text.startswith(("save screenshot", "save screen")):

            return Intent.SAVE_SCREENSHOT

        if text.startswith(("take region screenshot", "capture region")):

            return Intent.TAKE_REGION_SCREENSHOT

        if text.startswith(("take window screenshot", "capture window")):

            return Intent.TAKE_WINDOW_SCREENSHOT

        ##################################################
        # OCR
        ##################################################

        if text in (

            "read screen",

            "ocr screen"

        ):

            return Intent.OCR_SCREEN

        if text.startswith(("read image ", "ocr image ")):

            return Intent.OCR_IMAGE

        ##################################################
        # TERMINAL
        ##################################################

        if text.startswith(("run ", "execute ")):

            return Intent.RUN_COMMAND

        if text.startswith("python "):

            return Intent.RUN_PYTHON

        ##################################################

        return Intent.UNKNOWN