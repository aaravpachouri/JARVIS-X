import os
import shutil
import subprocess
import time
import ctypes
from pathlib import Path

from automation.services.environment_service import EnvironmentService
from automation.services.filesystem_service import FilesystemService


class AppService:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        self.env = EnvironmentService()
        self.files = FilesystemService()

        self.aliases = {

            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",

            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",

            "firefox": "firefox.exe",

            "notepad": "notepad.exe",

            "calculator": "calc.exe",
            "calc": "calc.exe",

            "paint": "mspaint.exe",

            "cmd": "cmd.exe",

            "powershell": "powershell.exe",

            "terminal": "wt.exe",

            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",

            "task manager": "taskmgr.exe",

            "vscode": "Code.exe",
            "vs code": "Code.exe",
            "visual studio code": "Code.exe",

            "steam": "steam.exe",
            "discord": "discord.exe",
            "spotify": "spotify.exe",
            "whatsapp": "WhatsApp.exe",
            "blender": "blender.exe",
        }

        self.window_titles = {

            "chrome": (
                "chrome",
                "google chrome",
            ),

            "edge": (
                "edge",
                "microsoft edge",
            ),

            "firefox": (
                "firefox",
            ),

            "notepad": (
                "notepad",
            ),

            "calculator": (
                "calculator",
            ),

            "calc": (
                "calculator",
            ),

            "paint": (
                "paint",
            ),

            "explorer": (
                "file explorer",
            ),

            "file explorer": (
                "file explorer",
            ),

            "task manager": (
                "task manager",
            ),

            "vscode": (
                "visual studio code",
                "vs code",
            ),

            "vs code": (
                "visual studio code",
                "vs code",
            ),

            "terminal": (
                "terminal",
            ),

            "powershell": (
                "powershell",
            ),
        }

    ##################################################
    # NORMALIZE
    ##################################################

    def normalize(self, value):

        return (
            str(value or "")
            .strip()
            .lower()
        )

    ##################################################
    # EXECUTABLE NAME
    ##################################################

    def executableName(self, app):

        app = self.normalize(app)

        return self.aliases.get(
            app,
            app
        )

    ##################################################
    # DIRECT PATH
    ##################################################

    def _checkPath(self, path):

        if not path:
            return None

        try:

            path = Path(path)

            if path.is_file():
                return path

        except Exception:
            pass

        return None

    ##################################################
    # WINDOWS PATH
    ##################################################

    def _searchPath(self, executable):

        try:

            result = shutil.which(
                executable
            )

            if result:
                return Path(result)

        except Exception:
            pass

        return None

    ##################################################
    # CHROME
    ##################################################

    def _findChrome(self):

        local = os.environ.get(
            "LOCALAPPDATA",
            ""
        )

        program_files = os.environ.get(
            "PROGRAMFILES",
            ""
        )

        program_files_x86 = os.environ.get(
            "PROGRAMFILES(X86)",
            ""
        )

        candidates = [

            Path(local)
            / "Google"
            / "Chrome"
            / "Application"
            / "chrome.exe",

            Path(program_files)
            / "Google"
            / "Chrome"
            / "Application"
            / "chrome.exe",

            Path(program_files_x86)
            / "Google"
            / "Chrome"
            / "Application"
            / "chrome.exe",
        ]

        for candidate in candidates:

            result = self._checkPath(
                candidate
            )

            if result:
                return result

        return None

    ##################################################
    # COMMON LOCATIONS
    ##################################################

    def _searchCommonLocations(
        self,
        executable
    ):

        roots = [

            self.env.programFiles(),
            self.env.programFilesX86(),
            self.env.localAppData(),
            self.env.appData(),
        ]

        for root in roots:

            try:

                if not root:
                    continue

                root = Path(root)

                if not root.exists():
                    continue

                for match in root.rglob(
                    executable
                ):

                    if match.is_file():
                        return match

            except Exception:
                continue

        return None

    ##################################################
    # FIND EXECUTABLE
    ##################################################

    def findExecutable(self, app):

        app = self.normalize(app)

        if not app:
            return None

        ##################################################
        # DIRECT PATH
        ##################################################

        direct = self._checkPath(app)

        if direct:
            return direct

        ##################################################
        # ALIAS
        ##################################################

        executable = self.executableName(
            app
        )

        ##################################################
        # WINDOWS PATH
        ##################################################

        result = self._searchPath(
            executable
        )

        if result:
            return result

        ##################################################
        # CHROME
        ##################################################

        if executable.lower() == "chrome.exe":

            result = self._findChrome()

            if result:
                return result

        ##################################################
        # COMMON LOCATIONS
        ##################################################

        result = self._searchCommonLocations(
            executable
        )

        if result:
            return result

        return None

    ##################################################
    # ENUMERATE WINDOWS
    ##################################################

    def _getWindows(self):

        user32 = ctypes.windll.user32

        windows = []

        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_void_p,
            ctypes.c_void_p
        )

        def callback(
            hwnd,
            lparam
        ):

            try:

                if not user32.IsWindowVisible(
                    hwnd
                ):
                    return True

                length = user32.GetWindowTextLengthW(
                    hwnd
                )

                if length <= 0:
                    return True

                buffer = ctypes.create_unicode_buffer(
                    length + 1
                )

                user32.GetWindowTextW(
                    hwnd,
                    buffer,
                    length + 1
                )

                title = buffer.value.strip()

                if title:

                    windows.append(
                        (
                            hwnd,
                            title
                        )
                    )

            except Exception:
                pass

            return True

        user32.EnumWindows(
            EnumWindowsProc(callback),
            0
        )

        return windows

    ##################################################
    # FOCUS WINDOW BY TITLE
    ##################################################

    def _focusByTitle(
        self,
        app
    ):

        app = self.normalize(
            app
        )

        keywords = self.window_titles.get(
            app,
            (
                app,
            )
        )

        user32 = ctypes.windll.user32

        for hwnd, title in self._getWindows():

            title_lower = title.lower()

            if any(
                keyword in title_lower
                for keyword in keywords
            ):

                try:

                    if user32.IsIconic(
                        hwnd
                    ):

                        user32.ShowWindow(
                            hwnd,
                            9
                        )

                    user32.SetForegroundWindow(
                        hwnd
                    )

                    time.sleep(
                        0.15
                    )

                    foreground = (
                        user32.GetForegroundWindow()
                    )

                    if foreground == hwnd:

                        print(
                            f"[APP] Focused: {title}"
                        )

                        return True

                except Exception:
                    continue

        return False

    ##################################################
    # FOCUS BY PROCESS
    ##################################################

    def _focusByProcess(
        self,
        pid
    ):

        if not pid:
            return False

        user32 = ctypes.windll.user32

        found = []

        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_void_p,
            ctypes.c_void_p
        )

        def callback(
            hwnd,
            lparam
        ):

            try:

                if not user32.IsWindowVisible(
                    hwnd
                ):
                    return True

                process_id = ctypes.c_ulong()

                user32.GetWindowThreadProcessId(
                    hwnd,
                    ctypes.byref(
                        process_id
                    )
                )

                if process_id.value == pid:

                    found.append(
                        hwnd
                    )

            except Exception:
                pass

            return True

        user32.EnumWindows(
            EnumWindowsProc(callback),
            0
        )

        for hwnd in found:

            try:

                user32.ShowWindow(
                    hwnd,
                    9
                )

                user32.SetForegroundWindow(
                    hwnd
                )

                time.sleep(
                    0.15
                )

                if (
                    user32.GetForegroundWindow()
                    == hwnd
                ):

                    return True

            except Exception:
                continue

        return False

    ##################################################
    # OPEN
    ##################################################

    def open(
        self,
        app
    ):

        app = str(
            app or ""
        ).strip()

        if not app:

            print(
                "[APP] Empty application."
            )

            return False

        ##################################################
        # APPLICATION RESOLUTION FIRST
        ##################################################

        executable = self.findExecutable(
            app
        )

        if executable:

            print(
                f"[APP] Resolved: "
                f"{app} -> {executable}"
            )

            try:

                process = subprocess.Popen(
                    [str(executable)]
                )

                print(
                    f"[APP] Launched: {app}"
                )

                ##################################################
                # WAIT FOR WINDOW
                ##################################################

                focused = False

                for _ in range(40):

                    time.sleep(
                        0.15
                    )

                    ##################################################
                    # FIRST TRY PROCESS
                    ##################################################

                    if self._focusByProcess(
                        process.pid
                    ):

                        focused = True
                        break

                    ##################################################
                    # THEN TITLE
                    #
                    # Important for Windows Store/UWP applications
                    # such as Calculator.
                    ##################################################

                    if self._focusByTitle(
                        app
                    ):

                        focused = True
                        break

                if focused:

                    print(
                        f"[APP] Ready: {app}"
                    )

                    return True

                ##################################################
                # PROCESS MAY ALREADY EXIST
                ##################################################

                if self._focusByTitle(
                    app
                ):

                    print(
                        f"[APP] Existing window focused: {app}"
                    )

                    return True

                print(
                    f"[APP] Could not verify "
                    f"foreground window: {app}"
                )

                return False

            except Exception as exc:

                print(
                    f"[APP] Launch failed: "
                    f"{app}: {exc}"
                )

                return False

        ##################################################
        # IMPORTANT
        #
        # DO NOT SEARCH FILESYSTEM FOR AN APPLICATION
        # BEFORE REACHING THIS POINT.
        ##################################################

        print(
            f"[APP] Executable not found: {app}"
        )

        ##################################################
        # FILE FALLBACK ONLY AFTER APPLICATION RESOLUTION
        ##################################################

        try:

            result = self.files.find(
                app
            )

            if result:

                print(
                    f"[APP] Opening filesystem "
                    f"target: {result}"
                )

                return self.files.openPath(
                    result
                )

        except Exception as exc:

            print(
                f"[APP] Filesystem fallback failed: "
                f"{exc}"
            )

        return False

    ##################################################
    # CLOSE
    ##################################################

    def close(
        self,
        app
    ):

        executable = self.executableName(
            app
        )

        try:

            result = subprocess.run(
                [
                    "taskkill",
                    "/F",
                    "/IM",
                    executable
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            if result.returncode == 0:

                print(
                    f"[APP] Closed: {app}"
                )

                return True

        except Exception as exc:

            print(
                f"[APP] Close failed: {exc}"
            )

        return False

    ##################################################
    # RUNNING
    ##################################################

    def isRunning(
        self,
        app
    ):

        executable = self.executableName(
            app
        )

        try:

            output = subprocess.check_output(
                [
                    "tasklist",
                    "/FI",
                    f"IMAGENAME eq {executable}"
                ],
                text=True,
                errors="ignore"
            )

            return (
                executable.lower()
                in output.lower()
            )

        except Exception:

            return False