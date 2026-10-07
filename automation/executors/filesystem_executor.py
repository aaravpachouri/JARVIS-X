from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from core.actions import ActionType

from automation.services.windows_service import WindowsService


class FilesystemExecutor:

    """
    Hardened filesystem executor for JARVIS X.

    Responsibilities:
        - resolve Windows paths through WindowsService
        - create/delete files and folders
        - copy/move/rename filesystem objects
        - validate source/destination state
        - prevent unsafe accidental overwrites
        - return structured execution results

    FileIntelligence remains responsible for discovery/ranking.
    This executor is responsible only for filesystem mutations.
    """

    def __init__(
        self,
    ):

        self.windows = WindowsService()

    ############################################################
    # PUBLIC EXECUTION
    ############################################################

    def execute(
        self,
        action,
    ):

        if action is None:

            return self._failure(
                "No filesystem action supplied."
            )

        action_type = getattr(
            action,
            "action",
            None,
        )

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

        ########################################################
        # CREATE FOLDER
        ########################################################

        if action_type == ActionType.CREATE_FOLDER:

            name = (
                parameters.get(
                    "name",
                    parameters.get(
                        "path",
                        ""
                    )
                )
            )

            return self.createFolder(
                name
            )

        ########################################################
        # DELETE FOLDER
        ########################################################

        if action_type == ActionType.DELETE_FOLDER:

            return self.deleteFolder(
                parameters.get(
                    "path",
                    ""
                )
            )

        ########################################################
        # CREATE FILE
        ########################################################

        if action_type == ActionType.CREATE_FILE:

            return self.createFile(
                parameters.get(
                    "path",
                    ""
                )
            )

        ########################################################
        # DELETE FILE
        ########################################################

        if action_type == ActionType.DELETE_FILE:

            return self.deleteFile(
                parameters.get(
                    "path",
                    ""
                )
            )

        ########################################################
        # COPY
        ########################################################

        if action_type == ActionType.COPY:

            return self.copy(
                parameters.get(
                    "source",
                    ""
                ),
                parameters.get(
                    "destination",
                    ""
                )
            )

        ########################################################
        # MOVE
        ########################################################

        if action_type == ActionType.MOVE:

            return self.move(
                parameters.get(
                    "source",
                    ""
                ),
                parameters.get(
                    "destination",
                    ""
                )
            )

        ########################################################
        # RENAME
        ########################################################

        if action_type == ActionType.RENAME:

            return self.rename(
                parameters.get(
                    "source",
                    ""
                ),
                parameters.get(
                    "new_name",
                    parameters.get(
                        "name",
                        ""
                    )
                )
            )

        ########################################################
        # UNSUPPORTED
        ########################################################

        action_name = getattr(
            action_type,
            "name",
            str(
                action_type
                or
                "UNKNOWN"
            )
        )

        print(
            "[Filesystem] "
            f"Unsupported action: {action_name}"
        )

        return self._failure(
            f"Unsupported filesystem action: {action_name}"
        )

    ############################################################
    # PATH RESOLUTION
    ############################################################

    def _resolve(
        self,
        raw_path,
    ) -> Optional[Path]:

        text = str(
            raw_path
            or
            ""
        ).strip()

        if not text:

            return None

        try:

            path = self.windows.resolvePath(
                text
            )

            if path is None:

                return None

            return Path(
                path
            )

        except Exception as exc:

            print(
                "[Filesystem] "
                f"Path resolution failed: {exc}"
            )

            return None

    ############################################################
    # VALIDATION
    ############################################################

    @staticmethod
    def _valid_name(
        name,
    ) -> bool:

        text = str(
            name
            or
            ""
        ).strip()

        if not text:
            return False

        if text in {
            ".",
            "..",
        }:

            return False

        invalid = {
            "<",
            ">",
            ":",
            '"',
            "/",
            "\\",
            "|",
            "?",
            "*",
        }

        return not any(
            char in text
            for char in invalid
        )

    @staticmethod
    def _same_path(
        first: Path,
        second: Path,
    ) -> bool:

        try:

            return (
                first.resolve()
                ==
                second.resolve()
            )

        except Exception:

            return (
                str(first).lower()
                ==
                str(second).lower()
            )

    @staticmethod
    def _destination_for_source(
        destination: Path,
        source: Path,
    ) -> Path:

        """
        If destination is an existing directory, copy/move the source
        into that directory using the source filename.
        """

        if (
            destination.exists()
            and
            destination.is_dir()
        ):

            return (
                destination
                /
                source.name
            )

        return destination

    ############################################################
    # CREATE FOLDER
    ############################################################

    def createFolder(
        self,
        name,
    ):

        text = str(
            name
            or
            ""
        ).strip()

        if not text:

            return self._failure(
                "Folder name is empty."
            )

        ########################################################
        # Preserve existing project behavior:
        # a simple name is created on Desktop.
        ########################################################

        if (
            "/" not in text
            and
            "\\" not in text
            and
            not Path(text).is_absolute()
        ):

            target_text = (
                f"Desktop/{text}"
            )

        else:

            target_text = text

        path = self._resolve(
            target_text
        )

        if path is None:

            return self._failure(
                "Could not resolve folder path."
            )

        if path.exists():

            if path.is_dir():

                return self._success(
                    "Folder already exists.",
                    path=path,
                    created=False,
                )

            return self._failure(
                (
                    "A file already exists at the "
                    f"requested folder path: {path}"
                )
            )

        try:

            path.mkdir(
                parents=True,
                exist_ok=False,
            )

            print(
                "[Filesystem] Folder created"
            )

            print(
                path
            )

            return self._success(
                "Folder created.",
                path=path,
                created=True,
            )

        except Exception as exc:

            print(
                "[Filesystem] "
                f"Folder creation failed: {exc}"
            )

            return self._failure(
                str(exc)
            )

    ############################################################
    # DELETE FOLDER
    ############################################################

    def deleteFolder(
        self,
        raw_path,
    ):

        path = self._resolve(
            raw_path
        )

        if path is None:

            return self._failure(
                "Folder path is empty or invalid."
            )

        if not path.exists():

            return self._failure(
                f"Folder does not exist: {path}"
            )

        if not path.is_dir():

            return self._failure(
                f"Path is not a folder: {path}"
            )

        try:

            shutil.rmtree(
                path
            )

            print(
                "[Filesystem] Folder deleted"
            )

            return self._success(
                "Folder deleted.",
                path=path,
            )

        except Exception as exc:

            print(
                "[Filesystem] "
                f"Folder deletion failed: {exc}"
            )

            return self._failure(
                str(exc)
            )

    ############################################################
    # CREATE FILE
    ############################################################

    def createFile(
        self,
        raw_path,
    ):

        path = self._resolve(
            raw_path
        )

        if path is None:

            return self._failure(
                "File path is empty or invalid."
            )

        if path.exists():

            if path.is_file():

                return self._success(
                    "File already exists.",
                    path=path,
                    created=False,
                )

            return self._failure(
                f"A directory already exists at: {path}"
            )

        try:

            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            path.touch(
                exist_ok=False
            )

            print(
                "[Filesystem] File created"
            )

            return self._success(
                "File created.",
                path=path,
                created=True,
            )

        except Exception as exc:

            print(
                "[Filesystem] "
                f"File creation failed: {exc}"
            )

            return self._failure(
                str(exc)
            )

    ############################################################
    # DELETE FILE
    ############################################################

    def deleteFile(
        self,
        raw_path,
    ):

        path = self._resolve(
            raw_path
        )

        if path is None:

            return self._failure(
                "File path is empty or invalid."
            )

        if not path.exists():

            return self._failure(
                f"File does not exist: {path}"
            )

        if not path.is_file():

            return self._failure(
                f"Path is not a file: {path}"
            )

        try:

            path.unlink()

            print(
                "[Filesystem] File deleted"
            )

            return self._success(
                "File deleted.",
                path=path,
            )

        except Exception as exc:

            print(
                "[Filesystem] "
                f"File deletion failed: {exc}"
            )

            return self._failure(
                str(exc)
            )

    ############################################################
    # COPY
    ############################################################

    def copy(
        self,
        raw_source,
        raw_destination,
    ):

        source = self._resolve(
            raw_source
        )

        destination = self._resolve(
            raw_destination
        )

        if source is None or destination is None:

            return self._failure(
                "Source or destination path is invalid."
            )

        if not source.exists():

            return self._failure(
                f"Source does not exist: {source}"
            )

        destination = (
            self._destination_for_source(
                destination,
                source,
            )
        )

        if self._same_path(
            source,
            destination,
        ):

            return self._failure(
                "Source and destination are the same path."
            )

        if (
            destination.exists()
            and
            destination.is_dir()
        ):

            return self._failure(
                "Destination resolves to a directory."
            )

        try:

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            ####################################################
            # Do not silently overwrite an existing target.
            ####################################################

            if destination.exists():

                return self._failure(
                    (
                        "Destination already exists: "
                        f"{destination}"
                    )
                )

            if source.is_dir():

                shutil.copytree(
                    source,
                    destination,
                )

            else:

                shutil.copy2(
                    source,
                    destination,
                )

            print(
                "[Filesystem] Copy completed"
            )

            return self._success(
                "Copy completed.",
                source=source,
                destination=destination,
            )

        except Exception as exc:

            print(
                "[Filesystem] "
                f"Copy failed: {exc}"
            )

            return self._failure(
                str(exc)
            )

    ############################################################
    # MOVE
    ############################################################

    def move(
        self,
        raw_source,
        raw_destination,
    ):

        source = self._resolve(
            raw_source
        )

        destination = self._resolve(
            raw_destination
        )

        if source is None or destination is None:

            return self._failure(
                "Source or destination path is invalid."
            )

        if not source.exists():

            return self._failure(
                f"Source does not exist: {source}"
            )

        destination = (
            self._destination_for_source(
                destination,
                source,
            )
        )

        if self._same_path(
            source,
            destination,
        ):

            return self._failure(
                "Source and destination are the same path."
            )

        if destination.exists():

            return self._failure(
                (
                    "Destination already exists: "
                    f"{destination}"
                )
            )

        ########################################################
        # Prevent moving a directory into itself.
        ########################################################

        try:

            if source.is_dir():

                source_resolved = (
                    source.resolve()
                )

                destination_resolved = (
                    destination.resolve()
                )

                if source_resolved in (
                    destination_resolved.parents
                ):

                    return self._failure(
                        "Cannot move a folder into itself."
                    )

        except Exception:
            pass

        try:

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            final_path = Path(
                shutil.move(
                    str(source),
                    str(destination),
                )
            )

            print(
                "[Filesystem] Move completed"
            )

            return self._success(
                "Move completed.",
                source=source,
                destination=final_path,
            )

        except Exception as exc:

            print(
                "[Filesystem] "
                f"Move failed: {exc}"
            )

            return self._failure(
                str(exc)
            )

    ############################################################
    # RENAME
    ############################################################

    def rename(
        self,
        raw_source,
        new_name,
    ):

        source = self._resolve(
            raw_source
        )

        new_name = str(
            new_name
            or
            ""
        ).strip()

        if source is None:

            return self._failure(
                "Source path is invalid."
            )

        if not source.exists():

            return self._failure(
                f"Source does not exist: {source}"
            )

        if not source.name:

            return self._failure(
                "Source has no valid filename."
            )

        if not self._valid_name(
            new_name
        ):

            return self._failure(
                (
                    "Invalid new filename: "
                    f"{new_name}"
                )
            )

        destination = (
            source.with_name(
                new_name
            )
        )

        if self._same_path(
            source,
            destination,
        ):

            return self._success(
                "Filename is already correct.",
                source=source,
                destination=destination,
                renamed=False,
            )

        if destination.exists():

            return self._failure(
                (
                    "A file or folder with the new "
                    f"name already exists: {destination}"
                )
            )

        try:

            source.rename(
                destination
            )

            print(
                "[Filesystem] Rename completed"
            )

            return self._success(
                "Rename completed.",
                source=source,
                destination=destination,
                renamed=True,
            )

        except Exception as exc:

            print(
                "[Filesystem] "
                f"Rename failed: {exc}"
            )

            return self._failure(
                str(exc)
            )

    ############################################################
    # RESULT HELPERS
    ############################################################

    @staticmethod
    def _serialize_path(
        value,
    ):

        if value is None:
            return None

        return str(
            value
        )

    @classmethod
    def _success(
        cls,
        message,
        **data,
    ):

        result = {
            "success":
                True,

            "message":
                str(
                    message
                ),
        }

        for key, value in data.items():

            result[
                key
            ] = cls._serialize_path(
                value
            )

        return result

    @staticmethod
    def _failure(
        message,
        **data,
    ):

        result = {
            "success":
                False,

            "error":
                str(
                    message
                ),
        }

        for key, value in data.items():

            result[
                key
            ] = str(
                value
            )

        return result