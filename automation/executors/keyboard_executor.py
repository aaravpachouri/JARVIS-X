import time

import pyautogui


class KeyboardExecutor:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        pyautogui.PAUSE = 0.03

        pyautogui.FAILSAFE = True

        self.key_aliases = {

            "return": "enter",
            "escape": "esc",
            "control": "ctrl",
            "ctrl": "ctrl",
            "shift": "shift",
            "windows": "win",
            "super": "win",
            "spacebar": "space",

            "left arrow": "left",
            "right arrow": "right",
            "up arrow": "up",
            "down arrow": "down",
        }

    ##################################################
    # NORMALIZE KEY
    ##################################################

    def normalizeKey(
        self,
        key
    ):

        key = str(
            key or ""
        ).strip().lower()

        return self.key_aliases.get(
            key,
            key
        )

    ##################################################
    # EXECUTE
    ##################################################

    def execute(
        self,
        action
    ):

        if action is None:
            return False

        parameters = (
            action.parameters
            or {}
        )

        name = (
            action.action.name
        )

        ##################################################
        # TYPE TEXT
        ##################################################

        if name == "TYPE_TEXT":

            text = str(
                parameters.get(
                    "text",
                    ""
                )
            )

            if not text:
                return False

            print(
                f"[Keyboard] Typing: {text}"
            )

            return self.typeText(
                text
            )

        ##################################################
        # PRESS KEY
        ##################################################

        if name == "PRESS_KEY":

            key = parameters.get(
                "key"
            )

            if key is None:
                return False

            return self.pressKey(
                key
            )

        ##################################################
        # HOTKEY
        ##################################################

        if name == "HOTKEY":

            keys = parameters.get(
                "keys",
                []
            )

            if isinstance(
                keys,
                str
            ):

                keys = [
                    key.strip()
                    for key in keys.split(
                        "+"
                    )
                ]

            if not keys:
                return False

            return self.hotkey(
                keys
            )

        ##################################################
        # HOLD
        ##################################################

        if name == "HOLD_KEY":

            key = parameters.get(
                "key"
            )

            if key is None:
                return False

            pyautogui.keyDown(
                self.normalizeKey(
                    key
                )
            )

            return True

        ##################################################
        # RELEASE
        ##################################################

        if name == "RELEASE_KEY":

            key = parameters.get(
                "key"
            )

            if key is None:
                return False

            pyautogui.keyUp(
                self.normalizeKey(
                    key
                )
            )

            return True

        return False

    ##################################################
    # TYPE TEXT
    ##################################################

    def typeText(
        self,
        text
    ):

        try:

            ##################################################
            # CLIPBOARD PASTE
            #
            # Much more reliable than individual key presses
            # for long text and symbols such as *.
            ##################################################

            try:

                import pyperclip

                old_clipboard = None

                try:
                    old_clipboard = pyperclip.paste()
                except Exception:
                    pass

                pyperclip.copy(
                    text
                )

                pyautogui.hotkey(
                    "ctrl",
                    "v"
                )

                time.sleep(
                    0.08
                )

                if old_clipboard is not None:

                    try:
                        pyperclip.copy(
                            old_clipboard
                        )
                    except Exception:
                        pass

                return True

            except Exception:

                ##################################################
                # FALLBACK
                ##################################################

                pyautogui.write(
                    text,
                    interval=0.01
                )

                return True

        except Exception as exc:

            print(
                f"[Keyboard] Type failed: {exc}"
            )

            return False

    ##################################################
    # PRESS KEY
    ##################################################

    def pressKey(
        self,
        key
    ):

        key = str(
            key
        ).strip()

        if not key:
            return False

        ##################################################
        # PRINTABLE CHARACTER
        #
        # pyautogui.press("*") is unreliable on Windows.
        ##################################################

        if len(key) == 1:

            try:

                pyautogui.write(
                    key
                )

                return True

            except Exception:
                pass

        key = self.normalizeKey(
            key
        )

        try:

            print(
                f"[Keyboard] Pressing: {key}"
            )

            pyautogui.press(
                key
            )

            return True

        except Exception as exc:

            print(
                f"[Keyboard] Key failed: "
                f"{key}: {exc}"
            )

            return False

    ##################################################
    # HOTKEY
    ##################################################

    def hotkey(
        self,
        keys
    ):

        normalized = [

            self.normalizeKey(
                key
            )

            for key in keys
        ]

        try:

            print(
                f"[Keyboard] Hotkey: "
                f"{normalized}"
            )

            pyautogui.hotkey(
                *normalized
            )

            return True

        except Exception as exc:

            print(
                f"[Keyboard] Hotkey failed: "
                f"{exc}"
            )

            return False