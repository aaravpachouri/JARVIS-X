from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional


############################################################
# APPLICATION EXECUTOR
############################################################

class AppExecutor:

    """
    Reliable Windows application launcher.

    Responsibilities:
        - normalize application names
        - resolve known applications
        - launch applications
        - give applications a short startup window
        - best-effort focus the launched process
        - close applications when a process handle is available

    The computer agent still performs semantic verification from
    the next screenshot. This executor only reports whether the
    launch request itself was accepted.
    """

    APP_ALIASES = {

        "notepad": [
            "notepad.exe",
        ],

        "calculator": [
            "calc.exe",
            "calculator.exe",
        ],

        "chrome": [
            "chrome.exe",
        ],

        "google chrome": [
            "chrome.exe",
        ],

        "edge": [
            "msedge.exe",
        ],

        "microsoft edge": [
            "msedge.exe",
        ],

        "firefox": [
            "firefox.exe",
        ],

        "opera": [
            "opera.exe",
            "launcher.exe",
        ],

        "vscode": [
            "code.exe",
        ],

        "vs code": [
            "code.exe",
        ],

        "visual studio code": [
            "code.exe",
        ],

        "explorer": [
            "explorer.exe",
        ],

        "file explorer": [
            "explorer.exe",
        ],

        "paint": [
            "mspaint.exe",
        ],

        "wordpad": [
            "write.exe",
        ],
    }

    STARTUP_DELAY = 0.35

    MAX_STARTUP_WAIT = 3.0

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(self):

        self.last_process = None

        self.last_application = ""

        self.last_executable = ""

        self.last_foreground_state = {}

    ########################################################
    # NORMALIZE
    ########################################################

    @staticmethod
    def normalize(
        name,
    ) -> str:

        text = str(
            name or ""
        ).strip().lower()

        if text.endswith(
            ".exe"
        ):

            text = text[:-4]

        return text.strip()

    ########################################################
    # RESOLVE
    ########################################################

    def resolve(
        self,
        name,
    ) -> Optional[str]:

        key = self.normalize(
            name
        )

        if not key:
            return None

        candidates = (
            self.APP_ALIASES.get(
                key,
                []
            )
        )

        system_root = os.environ.get(
            "SystemRoot",
            r"C:\Windows"
        )

        system32 = (
            Path(system_root)
            / "System32"
        )

        ####################################################
        # Known Windows/system executables
        ####################################################

        for executable in candidates:

            system_candidate = (
                system32
                / executable
            )

            if system_candidate.exists():

                return str(
                    system_candidate
                )

        ####################################################
        # PATH lookup
        ####################################################

        for executable in candidates:

            resolved = shutil.which(
                executable
            )

            if resolved:

                return str(
                    Path(
                        resolved
                    ).resolve()
                )

        ####################################################
        # Direct executable name
        ####################################################

        resolved = shutil.which(
            key
        )

        if resolved:

            return str(
                Path(
                    resolved
                ).resolve()
            )

        ####################################################
        # Full path supplied by caller
        ####################################################

        path = Path(
            str(name)
        ).expanduser()

        try:

            if path.exists() and path.is_file():

                return str(
                    path.resolve()
                )

        except OSError:

            pass

        return None

    ########################################################
    # OPEN
    ########################################################

    def open(
        self,
        application,
    ) -> bool:

        name = str(
            application or ""
        ).strip()

        if not name:

            print(
                "[AppExecutor] "
                "No application supplied."
            )

            return False

        normalized = self.normalize(
            name
        )

        print(
            "[AppExecutor] "
            f"Opening application: {normalized}"
        )

        executable = self.resolve(
            name
        )

        if executable is None:

            print(
                "[AppExecutor] "
                f"Application not found: {normalized}"
            )

            return False

        print(
            "[AppExecutor] "
            f"Resolved application: "
            f"{normalized} -> {executable}"
        )

        try:

            process = subprocess.Popen(
                [executable],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                close_fds=True,
            )

            self.last_process = process

            self.last_application = (
                normalized
            )

            self.last_executable = (
                executable
            )

            print(
                "[AppExecutor] "
                f"Launched: {normalized}"
            )

        except Exception as exc:

            print(
                "[AppExecutor] "
                f"Launch failed: {exc}"
            )

            return False

        ####################################################
        # Startup stabilization.
        #
        # Do NOT loop indefinitely. The next computer-agent
        # observation remains the authority for semantic success.
        ####################################################

        deadline = (
            time.monotonic()
            +
            self.MAX_STARTUP_WAIT
        )

        time.sleep(
            self.STARTUP_DELAY
        )

        while (
            time.monotonic()
            <
            deadline
        ):

            try:

                if process.poll() is not None:

                    # Process exited very quickly. That is not
                    # necessarily a failure, but there is no
                    # live process left to focus.
                    break

            except Exception:

                break

            focused = (
                self._focus_process(
                    process.pid
                )
            )

            if focused:

                break

            # The launched executable may spawn a different GUI
            # process. Try the higher-level application focus path.
            if self.focus_application(
                normalized
            ):

                break

            time.sleep(
                0.10
            )

        # Do not claim focus as a hard failure here. The next
        # ComputerAgent observation remains the semantic authority.
        self.last_foreground_state = (
            self.get_foreground_state()
        )

        return True

    ########################################################
    # WINDOW STATE
    ########################################################

    @staticmethod
    def get_foreground_window():
        """
        Return basic information about the current foreground
        window on Windows.

        Returns:
            {
                "hwnd": int,
                "pid": int,
                "title": str,
            }

        Returns None when unavailable.
        """

        if os.name != "nt":
            return None

        try:
            import ctypes

            user32 = ctypes.windll.user32

            hwnd = user32.GetForegroundWindow()

            if not hwnd:
                return None

            length = user32.GetWindowTextLengthW(
                hwnd
            )

            buffer = ctypes.create_unicode_buffer(
                max(1, length + 1)
            )

            user32.GetWindowTextW(
                hwnd,
                buffer,
                length + 1,
            )

            pid = ctypes.c_ulong()

            user32.GetWindowThreadProcessId(
                hwnd,
                ctypes.byref(pid),
            )

            return {
                "hwnd": int(hwnd),
                "pid": int(pid.value),
                "title": str(buffer.value or "").strip(),
            }

        except Exception:
            return None

    @staticmethod
    def get_process_name(
        pid: int,
    ) -> str:

        if os.name != "nt":
            return ""

        try:
            result = subprocess.run(
                [
                    "tasklist",
                    "/FI",
                    f"PID eq {int(pid)}",
                    "/FO",
                    "CSV",
                    "/NH",
                ],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )

            line = (
                result.stdout
                or ""
            ).strip()

            if not line:
                return ""

            # CSV format:
            # "IMAGE","PID",...
            first = line.split(
                '","',
                1
            )[0].strip(
                '"'
            )

            return first.strip()

        except Exception:
            return ""

    def get_foreground_state(
        self,
    ) -> dict:

        state = (
            self.get_foreground_window()
            or {}
        )

        pid = int(
            state.get(
                "pid",
                0,
            )
            or 0
        )

        process_name = (
            self.get_process_name(
                pid
            )
            if pid
            else ""
        )

        return {
            "hwnd": int(
                state.get(
                    "hwnd",
                    0,
                )
                or 0
            ),
            "pid": pid,
            "title": str(
                state.get(
                    "title",
                    "",
                )
                or ""
            ),
            "process_name": process_name,
        }

    def is_application_foreground(
        self,
        application=None,
    ) -> bool:

        target = self.normalize(
            application
            or
            self.last_application
            or ""
        )

        if not target:
            return False

        state = (
            self.get_foreground_state()
        )

        process_name = self.normalize(
            Path(
                state.get(
                    "process_name",
                    "",
                )
            ).stem
        )

        title = str(
            state.get(
                "title",
                "",
            )
            or ""
        ).lower()

        if process_name == target:
            return True

        # Aliases can map to the same foreground executable.
        resolved = self.resolve(
            target
        )

        if resolved:

            expected_executable = self.normalize(
                Path(
                    resolved
                ).stem
            )

            if process_name == expected_executable:
                return True

        # Some Windows apps expose a useful window title even
        # when the foreground process name differs.
        aliases = {
            "calculator": (
                "calculator",
                "calc",
            ),
            "notepad": (
                "notepad",
            ),
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
            "vscode": (
                "visual studio code",
                "vs code",
            ),
            "explorer": (
                "file explorer",
                "explorer",
            ),
        }

        title_tokens = aliases.get(
            target,
            (target,),
        )

        return any(
            token in title
            for token in title_tokens
        )

    def wait_until_foreground(
        self,
        application=None,
        timeout: float = 3.0,
        interval: float = 0.10,
    ) -> bool:

        target = (
            application
            or
            self.last_application
        )

        deadline = (
            time.monotonic()
            +
            max(
                0.1,
                float(timeout),
            )
        )

        while (
            time.monotonic()
            <
            deadline
        ):

            if self.is_application_foreground(
                target
            ):

                return True

            time.sleep(
                max(
                    0.03,
                    float(interval),
                )
            )

        return False

    def focus_application(
        self,
        application=None,
    ) -> bool:

        target = self.normalize(
            application
            or
            self.last_application
            or ""
        )

        if not target:
            return False

        ####################################################
        # First use the most recent process.
        ####################################################

        process = self.last_process

        if process is not None:

            try:

                pid = process.pid

                if self._focus_process(
                    pid
                ):

                    if self.wait_until_foreground(
                        target,
                        timeout=1.0,
                    ):

                        return True

            except Exception:
                pass

        ####################################################
        # If the original process spawned a different GUI
        # process, enumerate all top-level windows and focus a
        # window whose process matches the resolved executable.
        ####################################################

        if os.name != "nt":
            return False

        resolved = self.resolve(
            target
        )

        expected_name = ""

        if resolved:

            expected_name = self.normalize(
                Path(
                    resolved
                ).stem
            )

        if not expected_name:
            expected_name = target

        try:

            import ctypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            found = {
                "hwnd": None,
            }

            @ctypes.WINFUNCTYPE(
                ctypes.c_bool,
                ctypes.c_void_p,
                ctypes.c_void_p,
            )
            def callback(
                hwnd,
                _lparam,
            ):

                if not user32.IsWindowVisible(
                    hwnd
                ):
                    return True

                length = user32.GetWindowTextLengthW(
                    hwnd
                )

                title_buffer = ctypes.create_unicode_buffer(
                    max(
                        1,
                        length + 1,
                    )
                )

                user32.GetWindowTextW(
                    hwnd,
                    title_buffer,
                    length + 1,
                )

                pid = ctypes.c_ulong()

                user32.GetWindowThreadProcessId(
                    hwnd,
                    ctypes.byref(pid),
                )

                if not pid.value:
                    return True

                process_name = self.normalize(
                    Path(
                        self.get_process_name(
                            int(pid.value)
                        )
                    ).stem
                )

                title = str(
                    title_buffer.value
                    or ""
                ).lower()

                match = (
                    process_name
                    ==
                    expected_name
                )

                if not match:

                    if expected_name == "calc":

                        match = (
                            "calculator"
                            in
                            title
                        )

                    elif expected_name == "notepad":

                        match = (
                            "notepad"
                            in
                            title
                        )

                if match:

                    found[
                        "hwnd"
                    ] = hwnd

                    return False

                return True

            user32.EnumWindows(
                callback,
                0,
            )

            hwnd = found[
                "hwnd"
            ]

            if not hwnd:
                return False

            user32.ShowWindow(
                hwnd,
                5,
            )

            user32.SetForegroundWindow(
                hwnd
            )

            return self.wait_until_foreground(
                target,
                timeout=1.5,
            )

        except Exception:

            return False

    ########################################################
    # CLOSE
    ########################################################

    def close(
        self,
        application=None,
    ) -> bool:

        target = str(
            application
            or
            self.last_application
            or ""
        ).strip()

        if not target:

            return False

        ####################################################
        # Prefer the last launched process when it matches.
        ####################################################

        process = self.last_process

        if (
            process is not None
            and
            self.normalize(
                target
            )
            ==
            self.last_application
        ):

            try:

                if process.poll() is None:

                    process.terminate()

                    return True

            except Exception:
                pass

        ####################################################
        # Generic Windows close-by-image fallback.
        #
        # This is intentionally limited to the normalized
        # application name.
        ####################################################

        executable = self.resolve(
            target
        )

        if executable is None:

            return False

        executable_name = (
            Path(
                executable
            ).name
        )

        try:

            result = subprocess.run(
                [
                    "taskkill",
                    "/IM",
                    executable_name,
                    "/T",
                    "/F",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            return (
                result.returncode == 0
            )

        except Exception as exc:

            print(
                "[AppExecutor] "
                f"Close failed: {exc}"
            )

            return False

    ########################################################
    # EXECUTE
    ########################################################

    def execute(
        self,
        action,
    ) -> bool:

        if action is None:

            return False

        parameters = getattr(
            action,
            "parameters",
            {}
        )

        if not isinstance(
            parameters,
            dict,
        ):

            parameters = {}

        action_name = str(
            getattr(
                getattr(
                    action,
                    "action",
                    None,
                ),
                "name",
                getattr(
                    action,
                    "action",
                    "",
                ),
            )
            or ""
        ).upper().strip()

        if action_name == "OPEN_APP":

            application = (
                parameters.get(
                    "app",
                    parameters.get(
                        "app_name",
                        parameters.get(
                            "application",
                            "",
                        )
                    )
                )
            )

            return self.open(
                application
            )

        if action_name == "CLOSE_APP":

            application = (
                parameters.get(
                    "app",
                    parameters.get(
                        "app_name",
                        parameters.get(
                            "application",
                            "",
                        )
                    )
                )
            )

            return self.close(
                application
            )

        print(
            "[AppExecutor] "
            f"Unsupported action: {action_name}"
        )

        return False

    ########################################################
    # FOCUS PROCESS
    ########################################################

    @staticmethod
    def _focus_process(
        pid: int,
    ) -> bool:

        """
        Best-effort Windows foreground activation.

        Uses only stdlib ctypes and gracefully returns False on
        non-Windows platforms or when a window is not available yet.
        """

        if os.name != "nt":

            return False

        try:

            import ctypes

            user32 = ctypes.windll.user32

            found = {
                "hwnd": None,
            }

            PROCESS_ID = ctypes.c_ulong

            @ctypes.WINFUNCTYPE(
                ctypes.c_bool,
                ctypes.c_void_p,
                ctypes.c_void_p,
            )
            def callback(
                hwnd,
                _lparam,
            ):

                if not user32.IsWindowVisible(
                    hwnd
                ):

                    return True

                process_id = PROCESS_ID()

                user32.GetWindowThreadProcessId(
                    hwnd,
                    ctypes.byref(
                        process_id
                    )
                )

                if int(
                    process_id.value
                ) == int(pid):

                    found[
                        "hwnd"
                    ] = hwnd

                    return False

                return True

            user32.EnumWindows(
                callback,
                0,
            )

            hwnd = found[
                "hwnd"
            ]

            if not hwnd:

                return False

            user32.ShowWindow(
                hwnd,
                5,  # SW_SHOW
            )

            user32.SetForegroundWindow(
                hwnd
            )

            return True

        except Exception:

            return False