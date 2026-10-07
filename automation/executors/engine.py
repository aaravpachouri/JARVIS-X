
from automation.executors.app_executor import AppExecutor
from automation.executors.browser_executor import BrowserExecutor
from automation.executors.filesystem_executor import FilesystemExecutor
from automation.executors.mouse_executor import MouseExecutor
from automation.executors.keyboard_executor import KeyboardExecutor
from automation.executors.window_executor import WindowExecutor
from automation.executors.clipboard_executor import ClipboardExecutor
from automation.executors.screenshot_executor import ScreenshotExecutor
from automation.executors.ocr_executor import OCRExecutor
from automation.executors.terminal_executor import TerminalExecutor
from automation.executors.wait_executor import WaitExecutor
from automation.executors.vision_executor import VisionExecutor

from core.actions import ActionType


class AutomationEngine:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        self.app = AppExecutor()

        self.browser = BrowserExecutor()

        self.filesystem = FilesystemExecutor()

        self.mouse = MouseExecutor()

        self.keyboard = KeyboardExecutor()

        self.window = WindowExecutor()

        self.clipboard = ClipboardExecutor()

        self.screenshot = ScreenshotExecutor()

        self.ocr = OCRExecutor()

        self.terminal = TerminalExecutor()

        self.wait = WaitExecutor()

        self.vision = VisionExecutor()

        ##################################################
        # ROUTES
        ##################################################

        self.routes = {

            ##################################################
            # APPLICATIONS
            ##################################################

            ActionType.OPEN_APP:
                self.app,

            ActionType.CLOSE_APP:
                self.app,

            ##################################################
            # WEB
            ##################################################

            ActionType.OPEN_URL:
                self.browser,

            ActionType.SEARCH_WEB:
                self.browser,

            ##################################################
            # FILE SYSTEM
            ##################################################

            ActionType.CREATE_FILE:
                self.filesystem,

            ActionType.DELETE_FILE:
                self.filesystem,

            ActionType.CREATE_FOLDER:
                self.filesystem,

            ActionType.DELETE_FOLDER:
                self.filesystem,

            ActionType.COPY:
                self.filesystem,

            ActionType.MOVE:
                self.filesystem,

            ActionType.RENAME:
                self.filesystem,

            ##################################################
            # MOUSE
            ##################################################

            ActionType.MOUSE_MOVE:
                self.mouse,

            ActionType.MOUSE_MOVE_CENTER:
                self.mouse,

            ActionType.LEFT_CLICK:
                self.mouse,

            ActionType.RIGHT_CLICK:
                self.mouse,

            ActionType.DOUBLE_CLICK:
                self.mouse,

            ActionType.SCROLL_UP:
                self.mouse,

            ActionType.SCROLL_DOWN:
                self.mouse,

            ActionType.DRAG:
                self.mouse,

            ##################################################
            # KEYBOARD
            ##################################################

            ActionType.TYPE_TEXT:
                self.keyboard,

            ActionType.PRESS_KEY:
                self.keyboard,

            ActionType.HOTKEY:
                self.keyboard,

            ActionType.HOLD_KEY:
                self.keyboard,

            ActionType.RELEASE_KEY:
                self.keyboard,

            ##################################################
            # WINDOWS
            ##################################################

            ActionType.FOCUS_WINDOW:
                self.window,

            ActionType.CLOSE_WINDOW:
                self.window,

            ActionType.MINIMIZE_WINDOW:
                self.window,

            ActionType.MAXIMIZE_WINDOW:
                self.window,

            ActionType.RESTORE_WINDOW:
                self.window,

            ActionType.MOVE_WINDOW:
                self.window,

            ActionType.RESIZE_WINDOW:
                self.window,

            ##################################################
            # CLIPBOARD
            ##################################################

            ActionType.READ_CLIPBOARD:
                self.clipboard,

            ActionType.WRITE_CLIPBOARD:
                self.clipboard,

            ActionType.CLEAR_CLIPBOARD:
                self.clipboard,

            ##################################################
            # SCREENSHOT
            ##################################################

            ActionType.TAKE_SCREENSHOT:
                self.screenshot,

            ActionType.TAKE_REGION_SCREENSHOT:
                self.screenshot,

            ActionType.TAKE_WINDOW_SCREENSHOT:
                self.screenshot,

            ActionType.SAVE_SCREENSHOT:
                self.screenshot,

            ##################################################
            # OCR
            ##################################################

            ActionType.OCR_SCREEN:
                self.ocr,

            ActionType.OCR_IMAGE:
                self.ocr,

            ##################################################
            # VISION
            ##################################################

            ActionType.LOCATE_TEXT:
                self.vision,

            ActionType.CLICK_TEXT:
                self.vision,

            ActionType.CLICK_TYPE_ENTER:
                self.vision,

            ActionType.CLICK_FIRST_VIDEO:
                self.vision,

            ##################################################
            # TERMINAL
            ##################################################

            ActionType.RUN_COMMAND:
                self.terminal,

            ActionType.RUN_PYTHON:
                self.terminal,

            ##################################################
            # CONTROL
            ##################################################

            ActionType.WAIT:
                self.wait,
        }

    ##################################################
    # EXECUTE
    ##################################################

    def execute(
        self,
        actions
    ):

        if actions is None:

            return []

        if not isinstance(
            actions,
            list
        ):

            actions = [
                actions
            ]

        results = []

        for action in actions:

            results.append(
                self.executeAction(
                    action
                )
            )

        return results

    ##################################################
    # EXECUTE ACTION
    ##################################################

    def executeAction(
        self,
        action
    ):

        if action is None:

            return False

        executor = (
            self.routes.get(
                action.action
            )
        )

        if executor is None:

            print(
                "[Engine] Unsupported action:",
                action.action
            )

            return False

        try:

            print(
                f"[Engine] Executing: "
                f"{action.action.name}"
            )

            if action.parameters:

                print(
                    f"[Engine] Parameters: "
                    f"{action.parameters}"
                )

            result = executor.execute(
                action
            )

            return result

        except Exception as exc:

            print(
                f"[Engine] Action failed: "
                f"{action.action.name}"
            )

            print(
                f"[Engine] Error: {exc}"
            )

            return False