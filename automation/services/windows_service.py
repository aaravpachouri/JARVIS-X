from automation.services.environment_service import EnvironmentService
from automation.services.path_service import PathService


class WindowsService:

    def __init__(self):

        self.environment = EnvironmentService()

        self.paths = PathService()

    ##################################################
    # COMMON FOLDERS
    ##################################################

    def desktop(self):

        return self.environment.desktop()

    ##################################################

    def documents(self):

        return self.environment.documents()

    ##################################################

    def downloads(self):

        return self.environment.downloads()

    ##################################################

    def pictures(self):

        return self.environment.pictures()

    ##################################################

    def videos(self):

        return self.environment.videos()

    ##################################################

    def music(self):

        return self.environment.music()

    ##################################################

    def temp(self):

        return self.environment.temp()

    ##################################################
    # PATHS
    ##################################################

    def resolvePath(self, location):

        return self.paths.resolve(location)

    ##################################################

    def pathExists(self, location):

        return self.paths.exists(location)

    ##################################################

    def parent(self, location):

        return self.paths.parent(location)

    ##################################################

    def filename(self, location):

        return self.paths.filename(location)

    ##################################################

    def extension(self, location):

        return self.paths.extension(location)