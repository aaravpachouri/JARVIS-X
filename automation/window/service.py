import pygetwindow as gw


class WindowService:

    ##################################################
    # FIND WINDOW
    ##################################################

    def findWindow(self, title):

        title = title.lower()

        for window in gw.getAllWindows():

            if title in window.title.lower():

                return window

        return None

    ##################################################
    # EXISTS
    ##################################################

    def exists(self, title):

        return self.findWindow(title) is not None

    ##################################################
    # ACTIVE WINDOW
    ##################################################

    def activeWindow(self):

        return gw.getActiveWindow()

    ##################################################
    # LIST WINDOWS
    ##################################################

    def listWindows(self):

        return [

            window.title

            for window in gw.getAllWindows()

            if window.title.strip()

        ]

    ##################################################
    # FOCUS
    ##################################################

    def focus(self, title):

        window = self.findWindow(title)

        if not window:

            return False

        try:

            window.activate()

            return True

        except Exception:

            return False

    ##################################################
    # MINIMIZE
    ##################################################

    def minimize(self, title):

        window = self.findWindow(title)

        if not window:

            return False

        window.minimize()

        return True

    ##################################################
    # MAXIMIZE
    ##################################################

    def maximize(self, title):

        window = self.findWindow(title)

        if not window:

            return False

        window.maximize()

        return True

    ##################################################
    # RESTORE
    ##################################################

    def restore(self, title):

        window = self.findWindow(title)

        if not window:

            return False

        window.restore()

        return True

    ##################################################
    # MOVE
    ##################################################

    def move(self, title, x, y):

        window = self.findWindow(title)

        if not window:

            return False

        window.moveTo(x, y)

        return True

    ##################################################
    # RESIZE
    ##################################################

    def resize(self, title, width, height):

        window = self.findWindow(title)

        if not window:

            return False

        window.resizeTo(width, height)

        return True

    ##################################################
    # CLOSE
    ##################################################

    def close(self, title):

        window = self.findWindow(title)

        if not window:

            return False

        window.close()

        return True