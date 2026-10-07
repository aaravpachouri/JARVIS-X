from pathlib import Path

import mss
import mss.tools


class ScreenshotService:

    def __init__(self):

        self.sct = mss.mss()

    ##################################################

    def capture(self):

        return self.sct.grab(

            self.sct.monitors[1]

        )

    ##################################################

    def save(

        self,

        filename="screenshot.png"

    ):

        image = self.capture()

        path = Path(filename)

        mss.tools.to_png(

            image.rgb,

            image.size,

            output=str(path)

        )

        return path

    ##################################################

    def captureMonitor(

        self,

        monitor=1

    ):

        return self.sct.grab(

            self.sct.monitors[monitor]

        )

    ##################################################

    def monitorCount(self):

        return len(

            self.sct.monitors

        ) - 1