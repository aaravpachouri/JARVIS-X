import os
from pathlib import Path


class EnvironmentService:

    def __init__(self):

        self.env = os.environ

    ##################################################

    def get(self, key, default=None):

        return self.env.get(key, default)

    ##################################################

    def userProfile(self):

        return Path(

            self.get("USERPROFILE")

        )

    ##################################################

    def desktop(self):

        oneDrive = self.get("OneDrive")

        if oneDrive:

            desktop = Path(oneDrive) / "Desktop"

            if desktop.exists():

                return desktop

        return self.userProfile() / "Desktop"

    ##################################################

    def documents(self):

        oneDrive = self.get("OneDrive")

        if oneDrive:

            docs = Path(oneDrive) / "Documents"

            if docs.exists():

                return docs

        return self.userProfile() / "Documents"

    ##################################################

    def downloads(self):

        downloads = self.userProfile() / "Downloads"

        return downloads

    ##################################################

    def pictures(self):

        return self.userProfile() / "Pictures"

    ##################################################

    def videos(self):

        return self.userProfile() / "Videos"

    ##################################################

    def music(self):

        return self.userProfile() / "Music"

    ##################################################

    def temp(self):

        return Path(

            self.get("TEMP")

        )

    ##################################################

    def appData(self):

        return Path(

            self.get("APPDATA")

        )

    ##################################################

    def localAppData(self):

        return Path(

            self.get("LOCALAPPDATA")

        )

    ##################################################

    def programFiles(self):

        return Path(

            self.get("PROGRAMFILES")

        )

    ##################################################

    def programFilesX86(self):

        return Path(

            self.get("PROGRAMFILES(X86)")

        )