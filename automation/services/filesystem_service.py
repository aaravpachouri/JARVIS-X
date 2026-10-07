import os

from pathlib import Path

from automation.services.environment_service import EnvironmentService


class FilesystemService:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        self.env = EnvironmentService()

        self.skip_directories = {
            ".venv",
            "node_modules",
            "__pycache__",
            ".git",
            "AppData",
            "site-packages",
        }

    ##################################################
    # COMMON ROOTS
    ##################################################

    def roots(self):

        roots = [

            self.env.desktop(),

            self.env.documents(),

            self.env.downloads(),

            self.env.pictures(),

            self.env.videos(),

            self.env.music(),

            self.env.userProfile(),

        ]

        result = []

        for root in roots:

            if root and root.exists():

                if root not in result:

                    result.append(root)

        return result

    ##################################################
    # NORMALIZE SEARCH NAME
    ##################################################

    def normalizeName(self, name):

        name = str(name).strip().lower()

        ##################################################
        # REMOVE COMMON WORDS
        ##################################################

        prefixes = [

            "my ",
            "the ",
            "a ",
            "an ",

        ]

        for prefix in prefixes:

            if name.startswith(prefix):

                name = name[len(prefix):]

        ##################################################
        # REMOVE FILE/FOLDER WORDS
        ##################################################

        suffixes = [

            " folder",
            " file",

        ]

        for suffix in suffixes:

            if name.endswith(suffix):

                name = name[:-len(suffix)]

        return name.strip()

    ##################################################
    # OPEN PATH
    ##################################################

    def openPath(self, path):

        path = Path(path)

        if not path.exists():

            return False

        try:

            os.startfile(
                str(path)
            )

            print(
                f"[FILE] Opened: {path}"
            )

            return True

        except Exception as e:

            print(
                f"[FILE] Failed to open "
                f"{path}: {e}"
            )

            return False

    ##################################################
    # CHECK DIRECT PATH
    ##################################################

    def directPath(self, name):

        try:

            path = Path(name)

            if path.exists():

                return path

        except Exception:

            pass

        return None

    ##################################################
    # MATCH NAME
    ##################################################

    def matches(self, item, target):

        item_name = item.name.lower().strip()

        target = target.lower().strip()

        ##################################################
        # EXACT
        ##################################################

        if item_name == target:

            return True

        ##################################################
        # TARGET WITHOUT EXTENSION
        ##################################################

        if item.is_file():

            if item.stem.lower() == target:

                return True

        ##################################################
        # PARTIAL MATCH
        ##################################################

        if target in item_name:

            return True

        return False

    ##################################################
    # FIND
    ##################################################

    def find(self, name):

        target = self.normalizeName(
            name
        )

        if not target:

            return None

        print(
            f"[FILE] Searching for: {target}"
        )

        ##################################################
        # DIRECT PATH
        ##################################################

        direct = self.directPath(
            name
        )

        if direct:

            return direct

        ##################################################
        # ROOTS
        ##################################################

        roots = self.roots()

        ##################################################
        # PASS 1
        # FAST SHALLOW SEARCH
        ##################################################

        for root in roots:

            try:

                for item in root.iterdir():

                    if self.matches(
                        item,
                        target
                    ):

                        print(
                            f"[FILE] Found: {item}"
                        )

                        return item

            except Exception:

                continue

        ##################################################
        # PASS 2
        # LIMITED RECURSIVE SEARCH
        ##################################################

        for root in roots:

            try:

                for current_root, dirs, files in os.walk(
                    root
                ):

                    ##################################################
                    # REMOVE HEAVY / IRRELEVANT DIRECTORIES
                    ##################################################

                    dirs[:] = [

                        d for d in dirs

                        if d not in self.skip_directories

                    ]

                    ##################################################
                    # CHECK DIRECTORIES
                    ##################################################

                    for directory in dirs:

                        path = Path(
                            current_root
                        ) / directory

                        if self.matches(
                            path,
                            target
                        ):

                            print(
                                f"[FILE] Found: {path}"
                            )

                            return path

                    ##################################################
                    # CHECK FILES
                    ##################################################

                    for filename in files:

                        path = Path(
                            current_root
                        ) / filename

                        if self.matches(
                            path,
                            target
                        ):

                            print(
                                f"[FILE] Found: {path}"
                            )

                            return path

            except Exception:

                continue

        ##################################################
        # NOT FOUND
        ##################################################

        print(
            f"[FILE] Not found: {target}"
        )

        return None

    ##################################################
    # FIND AND OPEN
    ##################################################

    def findAndOpen(self, name):

        result = self.find(
            name
        )

        if result is None:

            return False

        return self.openPath(
            result
        )
        
    