from pathlib import Path

from automation.services.environment_service import EnvironmentService


class PathService:

    def __init__(self):

        self.env = EnvironmentService()

    ##################################################

    def resolve(self, location):

        """
        Converts human-friendly paths into absolute paths.
        """

        if isinstance(location, Path):

            return location

        location = location.strip()

        lower = location.lower()

        ##################################################
        # ROOT FOLDERS
        ##################################################

        roots = {

            "desktop": self.env.desktop(),

            "documents": self.env.documents(),

            "downloads": self.env.downloads(),

            "pictures": self.env.pictures(),

            "videos": self.env.videos(),

            "music": self.env.music(),

            "temp": self.env.temp()

        }

        ##################################################

        for key, root in roots.items():

            if lower == key:

                return root

            if lower.startswith(key + "/"):

                remainder = location[len(key) + 1:]

                return root / remainder

            if lower.startswith(key + "\\"):

                remainder = location[len(key) + 1:]

                return root / remainder

        ##################################################
        # ABSOLUTE PATH
        ##################################################

        path = Path(location)

        if path.is_absolute():

            return path

        ##################################################
        # DEFAULT
        ##################################################

        return self.env.desktop() / location

    ##################################################

    def exists(self, location):

        return self.resolve(location).exists()

    ##################################################

    def parent(self, location):

        return self.resolve(location).parent

    ##################################################

    def filename(self, location):

        return self.resolve(location).name

    ##################################################

    def extension(self, location):

        return self.resolve(location).suffix