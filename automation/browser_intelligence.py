from __future__ import annotations

import os
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus, urlparse


############################################################
# BROWSER INTELLIGENCE
############################################################

class BrowserIntelligence:

    """
    Deterministic browser capability layer for JARVIS X.

    Responsibilities:
        - identify common installed browsers
        - normalize browser names
        - open URLs
        - build/search web URLs
        - inspect the current foreground browser
        - best-effort focus a browser window

    This class does NOT decide whether a user request is a
    computer task. AIBrain / ComputerUseAgent still owns that.

    It also does NOT claim that a page visibly loaded. The
    ComputerUseAgent remains responsible for screenshot-based
    semantic verification.
    """

    BROWSER_ALIASES = {

        "chrome": (
            "chrome.exe",
            "Google Chrome",
        ),

        "google chrome": (
            "chrome.exe",
            "Google Chrome",
        ),

        "edge": (
            "msedge.exe",
            "Microsoft Edge",
        ),

        "microsoft edge": (
            "msedge.exe",
            "Microsoft Edge",
        ),

        "firefox": (
            "firefox.exe",
            "Mozilla Firefox",
        ),

        "mozilla firefox": (
            "firefox.exe",
            "Mozilla Firefox",
        ),

        "opera": (
            "opera.exe",
            "Opera",
        ),
    }

    DEFAULT_BROWSER_ORDER = (
        "chrome",
        "edge",
        "firefox",
        "opera",
    )

    SEARCH_ENGINES = {
        "google": "https://www.google.com/search?q={query}",
        "bing": "https://www.bing.com/search?q={query}",
        "youtube": "https://www.youtube.com/results?search_query={query}",
    }

    ########################################################
    # INITIALIZATION
    ########################################################

    def __init__(
        self,
        preferred_browser: Optional[str] = None,
    ):

        self.preferred_browser = (
            self.normalize_browser(
                preferred_browser
            )
            if preferred_browser
            else None
        )

        self.last_browser = ""

        self.last_url = ""

        self.last_process = None

    ########################################################
    # NORMALIZATION
    ########################################################

    @staticmethod
    def normalize_browser(
        browser: Optional[str],
    ) -> str:

        text = str(
            browser or ""
        ).strip().lower()

        aliases = {
            "google chrome": "chrome",
            "chrome browser": "chrome",
            "microsoft edge": "edge",
            "edge browser": "edge",
            "mozilla firefox": "firefox",
            "firefox browser": "firefox",
        }

        return aliases.get(
            text,
            text,
        )

    ########################################################
    # URL NORMALIZATION
    ########################################################

    @staticmethod
    def normalize_url(
        url: str,
    ) -> str:

        text = str(
            url or ""
        ).strip()

        if not text:
            return ""

        ####################################################
        # Common shortcuts
        ####################################################

        shortcuts = {
            "youtube": "https://www.youtube.com",
            "youtube.com": "https://www.youtube.com",
            "google": "https://www.google.com",
            "google.com": "https://www.google.com",
            "gmail": "https://mail.google.com",
            "gmail.com": "https://mail.google.com",
            "github": "https://github.com",
            "github.com": "https://github.com",
            "reddit": "https://www.reddit.com",
            "reddit.com": "https://www.reddit.com",
            "instagram": "https://www.instagram.com",
            "instagram.com": "https://www.instagram.com",
            "spotify": "https://open.spotify.com",
        }

        shortcut = shortcuts.get(
            text.lower()
        )

        if shortcut:
            return shortcut

        ####################################################
        # Already complete URL
        ####################################################

        parsed = urlparse(
            text
        )

        if parsed.scheme in {
            "http",
            "https",
        }:

            return text

        ####################################################
        # www.example.com / example.com
        ####################################################

        if (
            text.lower().startswith(
                "www."
            )
            or
            "." in text
        ):

            return (
                "https://"
                +
                text
            )

        ####################################################
        # Fallback to a search rather than pretending a natural
        # phrase is a valid URL.
        ####################################################

        return (
            "https://www.google.com/search?q="
            +
            quote_plus(
                text
            )
        )

    ########################################################
    # BROWSER RESOLUTION
    ########################################################

    def resolve_browser(
        self,
        browser: Optional[str] = None,
    ) -> Optional[str]:

        requested = self.normalize_browser(
            browser
            or
            self.preferred_browser
            or
            ""
        )

        names = []

        if requested:
            names.append(
                requested
            )

        for name in self.DEFAULT_BROWSER_ORDER:

            if name not in names:
                names.append(
                    name
                )

        for name in names:

            entry = self.BROWSER_ALIASES.get(
                name
            )

            if not entry:
                continue

            executable = entry[0]

            resolved = (
                self._find_executable(
                    executable
                )
            )

            if resolved:
                return resolved

        return None

    @staticmethod
    def _find_executable(
        executable: str,
    ) -> Optional[str]:

        ####################################################
        # PATH
        ####################################################

        try:

            from shutil import which

            resolved = which(
                executable
            )

            if resolved:
                return str(
                    Path(
                        resolved
                    ).resolve()
                )

        except Exception:
            pass

        ####################################################
        # Common Windows locations
        ####################################################

        if os.name != "nt":
            return None

        program_files = [
            os.environ.get(
                "ProgramFiles",
                r"C:\Program Files"
            ),

            os.environ.get(
                "ProgramFiles(x86)",
                r"C:\Program Files (x86)"
            ),

            os.environ.get(
                "LOCALAPPDATA",
                ""
            ),

        ]

        possible_locations = {

            "chrome.exe": (
                r"Google\Chrome\Application\chrome.exe",
                r"Google\Chrome\Application\chrome.exe",
            ),

            "msedge.exe": (
                r"Microsoft\Edge\Application\msedge.exe",
            ),

            "firefox.exe": (
                r"Mozilla Firefox\firefox.exe",
            ),

            "opera.exe": (
                r"Programs\Opera\opera.exe",
                r"Programs\Opera GX\opera.exe",
            ),
        }

        for root in program_files:

            if not root:
                continue

            for relative in possible_locations.get(
                executable,
                ()
            ):

                candidate = (
                    Path(root)
                    /
                    relative
                )

                if candidate.exists():

                    return str(
                        candidate.resolve()
                    )

        ####################################################
        # Registry / shell resolution can be handled by
        # Windows webbrowser when no direct executable was found.
        ####################################################

        return None

    ########################################################
    # BROWSER SELECTION
    ########################################################

    def select_browser(
        self,
        browser: Optional[str] = None,
    ) -> str:

        requested = self.normalize_browser(
            browser
        )

        if requested:

            resolved = self.resolve_browser(
                requested
            )

            if resolved:
                return requested

        if self.preferred_browser:

            resolved = self.resolve_browser(
                self.preferred_browser
            )

            if resolved:
                return self.preferred_browser

        resolved = self.resolve_browser()

        if resolved:

            executable = Path(
                resolved
            ).name.lower()

            for name, aliases in (
                self.BROWSER_ALIASES.items()
            ):

                if executable == aliases[0].lower():

                    return name

        return "default"

    ########################################################
    # OPEN URL
    ########################################################

    def open_url(
        self,
        url: str,
        browser: Optional[str] = None,
    ) -> bool:

        normalized = self.normalize_url(
            url
        )

        if not normalized:
            return False

        selected = self.select_browser(
            browser
        )

        print()
        print(
            "[BrowserIntelligence] "
            f"Opening: {normalized}"
        )

        print(
            "[BrowserIntelligence] "
            f"Browser: {selected}"
        )

        try:

            executable = self.resolve_browser(
                selected
            )

            ################################################
            # Preferred path: launch the selected browser
            # directly with the URL.
            ################################################

            if executable:

                process = subprocess.Popen(
                    [
                        executable,
                        normalized,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    close_fds=True,
                )

                self.last_process = process
                self.last_browser = selected
                self.last_url = normalized

                time.sleep(
                    0.15
                )

                return True

            ################################################
            # Fallback to the Windows/default browser.
            ################################################

            success = webbrowser.open(
                normalized,
                new=2,
            )

            if success:

                self.last_browser = "default"
                self.last_url = normalized

            return bool(
                success
            )

        except Exception as exc:

            print(
                "[BrowserIntelligence] "
                f"Open failed: {exc}"
            )

            return False

    ########################################################
    # SEARCH
    ########################################################

    def search(
        self,
        query: str,
        engine: str = "google",
        browser: Optional[str] = None,
    ) -> bool:

        text = str(
            query or ""
        ).strip()

        if not text:
            return False

        search_engine = str(
            engine or "google"
        ).strip().lower()

        template = self.SEARCH_ENGINES.get(
            search_engine
        )

        if template is None:

            search_engine = "google"

            template = (
                self.SEARCH_ENGINES[
                    search_engine
                ]
            )

        url = template.format(
            query=quote_plus(
                text
            )
        )

        print(
            "[BrowserIntelligence] "
            f"Searching {search_engine}: {text}"
        )

        return self.open_url(
            url,
            browser=browser,
        )

    ########################################################
    # YOUTUBE SEARCH
    ########################################################

    def search_youtube(
        self,
        query: str,
        browser: Optional[str] = None,
    ) -> bool:

        return self.search(
            query,
            engine="youtube",
            browser=browser,
        )

    ########################################################
    # FOREGROUND WINDOW
    ########################################################

    @staticmethod
    def get_foreground_window():

        if os.name != "nt":
            return None

        try:

            import ctypes

            user32 = ctypes.windll.user32

            hwnd = (
                user32.GetForegroundWindow()
            )

            if not hwnd:
                return None

            length = (
                user32.GetWindowTextLengthW(
                    hwnd
                )
            )

            buffer = (
                ctypes.create_unicode_buffer(
                    max(
                        1,
                        length + 1,
                    )
                )
            )

            user32.GetWindowTextW(
                hwnd,
                buffer,
                length + 1,
            )

            pid = ctypes.c_ulong()

            user32.GetWindowThreadProcessId(
                hwnd,
                ctypes.byref(
                    pid
                )
            )

            return {
                "hwnd": int(hwnd),
                "pid": int(pid.value),
                "title": str(
                    buffer.value or ""
                ).strip(),
            }

        except Exception:
            return None

    ########################################################
    # BROWSER FOREGROUND CHECK
    ########################################################

    def is_browser_foreground(
        self,
        browser: Optional[str] = None,
    ) -> bool:

        selected = self.normalize_browser(
            browser
            or
            self.last_browser
        )

        if selected == "default":
            selected = ""

        state = (
            self.get_foreground_window()
            or
            {}
        )

        title = str(
            state.get(
                "title",
                "",
            )
            or ""
        ).lower()

        if not title:
            return False

        if selected == "chrome":
            return (
                "chrome"
                in
                title
            )

        if selected == "edge":
            return (
                "edge"
                in
                title
            )

        if selected == "firefox":
            return (
                "firefox"
                in
                title
            )

        if selected == "opera":
            return (
                "opera"
                in
                title
            )

        browser_tokens = (
            "chrome",
            "edge",
            "firefox",
            "opera",
        )

        return any(
            token in title
            for token in browser_tokens
        )

    ########################################################
    # CURRENT STATE
    ########################################################

    def current_state(
        self,
    ) -> dict:

        foreground = (
            self.get_foreground_window()
            or
            {}
        )

        return {
            "browser":
                self.last_browser,

            "last_url":
                self.last_url,

            "foreground":
                foreground,

            "browser_foreground":
                self.is_browser_foreground(),
        }

    ########################################################
    # FOCUS BROWSER
    ########################################################

    def focus(
        self,
        browser: Optional[str] = None,
    ) -> bool:

        if os.name != "nt":
            return False

        selected = self.normalize_browser(
            browser
            or
            self.last_browser
        )

        state = (
            self.get_foreground_window()
            or
            {}
        )

        if not state:
            return False

        title = str(
            state.get(
                "title",
                "",
            )
            or ""
        ).lower()

        tokens = {

            "chrome": (
                "chrome",
            ),

            "edge": (
                "edge",
            ),

            "firefox": (
                "firefox",
            ),

            "opera": (
                "opera",
            ),
        }

        if selected not in tokens:
            return False

        ####################################################
        # If already foreground, we're done.
        ####################################################

        if any(
            token in title
            for token in tokens[selected]
        ):

            return True

        ####################################################
        # Best-effort browser process focus.
        ####################################################

        try:

            process_name = {
                "chrome": "chrome.exe",
                "edge": "msedge.exe",
                "firefox": "firefox.exe",
                "opera": "opera.exe",
            }[selected]

            result = subprocess.run(
                [
                    "tasklist",
                    "/FI",
                    f"IMAGENAME eq {process_name}",
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
                return False

            parts = line.split(
                '","'
            )

            if len(parts) < 2:
                return False

            pid_text = (
                parts[1]
                .strip('"')
            )

            pid = int(
                pid_text
            )

            return self._focus_pid(
                pid
            )

        except Exception:

            return False

    ########################################################
    # WINDOWS FOCUS HELPER
    ########################################################

    @staticmethod
    def _focus_pid(
        pid: int,
    ) -> bool:

        if os.name != "nt":
            return False

        try:

            import ctypes

            user32 = ctypes.windll.user32

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

                process_id = ctypes.c_ulong()

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
                5,
            )

            user32.SetForegroundWindow(
                hwnd
            )

            return True

        except Exception:

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
            dict
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

        if action_name == "OPEN_URL":

            url = (
                parameters.get(
                    "url",
                    ""
                )
            )

            browser = (
                parameters.get(
                    "browser"
                )
            )

            return self.open_url(
                url,
                browser=browser,
            )

        if action_name == "SEARCH_WEB":

            query = (
                parameters.get(
                    "query",
                    parameters.get(
                        "text",
                        ""
                    )
                )
            )

            engine = (
                parameters.get(
                    "engine",
                    "google"
                )
            )

            browser = (
                parameters.get(
                    "browser"
                )
            )

            return self.search(
                query,
                engine=engine,
                browser=browser,
            )

        print(
            "[BrowserIntelligence] "
            f"Unsupported action: {action_name}"
        )

        return False


############################################################
# STANDALONE HELPERS
############################################################

def open_url(
    url: str,
    browser: Optional[str] = None,
) -> bool:

    return BrowserIntelligence().open_url(
        url,
        browser=browser,
    )


def search_web(
    query: str,
    engine: str = "google",
    browser: Optional[str] = None,
) -> bool:

    return BrowserIntelligence().search(
        query,
        engine=engine,
        browser=browser,
    )