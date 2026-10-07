import time

import pyautogui


class KeyboardController:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        pyautogui.FAILSAFE = True

        pyautogui.PAUSE = 0.10

    ##################################################
    # TYPE
    ##################################################

    def type(self, text, interval=0.03):

        text = str(text)

        print(
            f"[Keyboard] Typing: {text}"
        )

        time.sleep(0.15)

        pyautogui.write(
            text,
            interval=interval
        )

        time.sleep(0.15)

    ##################################################
    # PRESS
    ##################################################

    def press(self, key):

        key = str(
            key
        ).lower()

        print(
            f"[Keyboard] Pressing: {key}"
        )

        time.sleep(0.10)

        pyautogui.press(
            key
        )

        time.sleep(0.15)

    ##################################################
    # HOTKEY
    ##################################################

    def hotkey(self, *keys):

        keys = [
            str(key).lower()
            for key in keys
        ]

        print(
            f"[Keyboard] Hotkey: "
            f"{' + '.join(keys)}"
        )

        time.sleep(0.20)

        pyautogui.hotkey(
            *keys
        )

        time.sleep(0.30)

    ##################################################
    # HOLD
    ##################################################

    def hold(self, key):

        key = str(
            key
        ).lower()

        print(
            f"[Keyboard] Holding: {key}"
        )

        pyautogui.keyDown(
            key
        )

    ##################################################
    # RELEASE
    ##################################################

    def release(self, key):

        key = str(
            key
        ).lower()

        print(
            f"[Keyboard] Releasing: {key}"
        )

        pyautogui.keyUp(
            key
        )

    ##################################################
    # COPY
    ##################################################

    def copy(self):

        self.hotkey(
            "ctrl",
            "c"
        )

    ##################################################
    # PASTE
    ##################################################

    def paste(self):

        self.hotkey(
            "ctrl",
            "v"
        )

    ##################################################
    # CUT
    ##################################################

    def cut(self):

        self.hotkey(
            "ctrl",
            "x"
        )

    ##################################################
    # SAVE
    ##################################################

    def save(self):

        self.hotkey(
            "ctrl",
            "s"
        )

    ##################################################
    # UNDO
    ##################################################

    def undo(self):

        self.hotkey(
            "ctrl",
            "z"
        )

    ##################################################
    # REDO
    ##################################################

    def redo(self):

        self.hotkey(
            "ctrl",
            "y"
        )

    ##################################################
    # SELECT ALL
    ##################################################

    def selectAll(self):

        self.hotkey(
            "ctrl",
            "a"
        )