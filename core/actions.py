from enum import Enum, auto
from dataclasses import dataclass


##################################################
# ACTION
##################################################

@dataclass
class Action:

    action: "ActionType"

    parameters: dict


##################################################
# ACTION TYPES
##################################################

class ActionType(Enum):

    ##################################################
    # APPLICATIONS
    ##################################################

    OPEN_APP = auto()

    CLOSE_APP = auto()

    ##################################################
    # WEB
    ##################################################

    OPEN_URL = auto()

    SEARCH_WEB = auto()

    ##################################################
    # FILE SYSTEM
    ##################################################

    CREATE_FILE = auto()

    DELETE_FILE = auto()

    CREATE_FOLDER = auto()

    DELETE_FOLDER = auto()

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
    # VISION AUTOMATION
    ##################################################

    LOCATE_TEXT = auto()

    CLICK_TEXT = auto()

    CLICK_TYPE_ENTER = auto()
    
    CLICK_FIRST_VIDEO = auto()

    ##################################################
    # TERMINAL
    ##################################################

    RUN_COMMAND = auto()

    RUN_PYTHON = auto()

    ##################################################
    # SYSTEM
    ##################################################

    VOLUME = auto()

    BRIGHTNESS = auto()

    SHUTDOWN = auto()

    RESTART = auto()

    SLEEP = auto()

    ##################################################
    # AI
    ##################################################

    ASK_AI = auto()

    ##################################################
    # CONTROL
    ##################################################

    WAIT = auto()

    NOTIFY = auto()

    ##################################################
    # UNKNOWN
    ##################################################

    UNKNOWN = auto()