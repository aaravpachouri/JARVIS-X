from __future__ import annotations

import fnmatch
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Optional


############################################################
# FILE INTELLIGENCE RESULT
############################################################

@dataclass
class FileCandidate:

    path: str

    name: str

    is_file: bool

    is_directory: bool

    extension: str = ""

    size: int = 0

    score: float = 0.0

    reasons: list[str] = field(
        default_factory=list
    )

    def to_dict(
        self,
    ) -> dict:

        return asdict(
            self
        )


############################################################
# FILE INTELLIGENCE
############################################################

class FileIntelligence:

    """
    Deterministic filesystem discovery layer.

    Purpose:
        Turn natural-language file references such as:

            "chemistry PDF"
            "the notes folder"
            "jarvis_test.txt"

        into ranked filesystem candidates.

    This component DOES NOT modify the filesystem.

    It only discovers and ranks candidates.

    Actual CREATE / MOVE / COPY / RENAME / DELETE operations
    remain the responsibility of FilesystemExecutor.
    """

    DEFAULT_IGNORED_DIRECTORIES = {
        ".git",
        ".venv",
        "__pycache__",
        "node_modules",
        "$recycle.bin",
        "system volume information",
    }

    def __init__(
        self,
        ignored_directories: Optional[
            Iterable[str]
        ] = None,
    ):

        ignored = (
            set(
                self.DEFAULT_IGNORED_DIRECTORIES
            )
            if ignored_directories is None
            else {
                str(item).strip().lower()
                for item in ignored_directories
            }
        )

        self.ignored_directories = ignored

    ########################################################
    # SEARCH
    ########################################################

    def search(
        self,
        root: str | Path,
        query: str,
        *,
        extension: Optional[str] = None,
        files_only: bool = False,
        directories_only: bool = False,
        max_results: int = 20,
        recursive: bool = True,
    ) -> list[FileCandidate]:

        root_path = Path(
            root
        ).expanduser()

        query = str(
            query or ""
        ).strip()

        if not query:

            return []

        if not root_path.exists():

            return []

        if not root_path.is_dir():

            return []

        extension = self._normalize_extension(
            extension
        )

        try:

            limit = max(
                1,
                int(
                    max_results
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            limit = 20

        candidates = []

        iterator = (
            root_path.rglob("*")
            if recursive
            else root_path.glob("*")
        )

        query_tokens = self._tokens(
            query
        )

        for path in iterator:

            if self._should_ignore(
                path
            ):

                continue

            try:

                is_file = path.is_file()
                is_directory = path.is_dir()

            except OSError:

                continue

            if files_only and not is_file:
                continue

            if directories_only and not is_directory:
                continue

            if extension and (
                not is_file
                or
                path.suffix.lower()
                != extension
            ):

                continue

            candidate = self._score_candidate(
                path,
                query,
                query_tokens,
            )

            if candidate.score <= 0:

                continue

            candidates.append(
                candidate
            )

        candidates.sort(
            key=lambda item: (
                item.score,
                -len(
                    Path(
                        item.path
                    ).parts
                ),
                item.name.lower(),
            ),
            reverse=True,
        )

        return candidates[:limit]

    ########################################################
    # FIND FILE
    ########################################################

    def find_file(
        self,
        root: str | Path,
        query: str,
        extension: Optional[str] = None,
        max_results: int = 20,
    ) -> list[FileCandidate]:

        return self.search(
            root,
            query,
            extension=extension,
            files_only=True,
            max_results=max_results,
        )

    ########################################################
    # FIND DIRECTORY
    ########################################################

    def find_directory(
        self,
        root: str | Path,
        query: str,
        max_results: int = 20,
    ) -> list[FileCandidate]:

        return self.search(
            root,
            query,
            directories_only=True,
            max_results=max_results,
        )

    ########################################################
    # EXACT PATH
    ########################################################

    @staticmethod
    def resolve_exact(
        path: str | Path,
    ) -> Optional[Path]:

        candidate = Path(
            path
        ).expanduser()

        try:

            if candidate.exists():

                return candidate.resolve()

        except OSError:

            pass

        return None

    ########################################################
    # BEST MATCH
    ########################################################

    def best_match(
        self,
        candidates: list[FileCandidate],
        minimum_score: float = 50.0,
    ) -> Optional[FileCandidate]:

        if not candidates:

            return None

        best = candidates[0]

        if best.score < float(
            minimum_score
        ):

            return None

        return best

    ########################################################
    # SCORE
    ########################################################

    def _score_candidate(
        self,
        path: Path,
        query: str,
        query_tokens: list[str],
    ) -> FileCandidate:

        name = path.name
        stem = path.stem

        name_lower = name.lower()
        stem_lower = stem.lower()
        query_lower = query.lower().strip()

        score = 0.0
        reasons = []

        ####################################################
        # Exact filename
        ####################################################

        if name_lower == query_lower:

            score += 100.0

            reasons.append(
                "exact filename"
            )

        ####################################################
        # Exact stem
        ####################################################

        if stem_lower == query_lower:

            score += 90.0

            reasons.append(
                "exact filename stem"
            )

        ####################################################
        # Full substring
        ####################################################

        if query_lower in name_lower:

            score += 65.0

            reasons.append(
                "filename contains query"
            )

        ####################################################
        # Token overlap
        ####################################################

        for token in query_tokens:

            if len(token) < 2:

                continue

            if token in name_lower:

                score += 15.0

                reasons.append(
                    f"name token: {token}"
                )

            elif token in stem_lower:

                score += 12.0

                reasons.append(
                    f"stem token: {token}"
                )

        ####################################################
        # Path token overlap
        ####################################################

        path_text = str(
            path.parent
        ).lower()

        for token in query_tokens:

            if len(token) < 2:
                continue

            if token in path_text:

                score += 4.0

                reasons.append(
                    f"path token: {token}"
                )

        ####################################################
        # File metadata
        ####################################################

        extension = (
            path.suffix.lower()
            if path.is_file()
            else ""
        )

        size = 0

        if path.is_file():

            try:

                size = path.stat().st_size

            except OSError:

                size = 0

        return FileCandidate(
            path=str(
                path.resolve()
            ),

            name=name,

            is_file=path.is_file(),

            is_directory=path.is_dir(),

            extension=extension,

            size=size,

            score=score,

            reasons=list(
                dict.fromkeys(
                    reasons
                )
            ),
        )

    ########################################################
    # TOKENIZATION
    ########################################################

    @staticmethod
    def _tokens(
        query: str,
    ) -> list[str]:

        normalized = (
            query.lower()
            .replace(
                "_",
                " "
            )
            .replace(
                "-",
                " "
            )
        )

        return [
            token
            for token
            in normalized.split()
            if token
        ]

    ########################################################
    # EXTENSION
    ########################################################

    @staticmethod
    def _normalize_extension(
        extension: Optional[str],
    ) -> Optional[str]:

        if not extension:

            return None

        value = str(
            extension
        ).strip().lower()

        if not value:

            return None

        if not value.startswith("."):

            value = "." + value

        return value

    ########################################################
    # IGNORE
    ########################################################

    def _should_ignore(
        self,
        path: Path,
    ) -> bool:

        for part in path.parts:

            if part.lower() in (
                self.ignored_directories
            ):

                return True

        return False

    ########################################################
    # SAFE NAME MATCH
    ########################################################

    @staticmethod
    def matches_pattern(
        name: str,
        pattern: str,
    ) -> bool:

        return fnmatch.fnmatch(
            str(
                name or ""
            ).lower(),
            str(
                pattern or ""
            ).lower(),
        )