from pathlib import Path
import time

from PIL import Image

from automation.ocr.service import OCRService
from automation.mouse.controller import MouseController
from automation.keyboard.controller import KeyboardController
from automation.screenshot.service import ScreenshotService


class ScreenLocator:

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(self):

        self.ocr = OCRService()

        self.screenshot = ScreenshotService()

        self.mouse = MouseController()

        self.keyboard = KeyboardController()

    ##################################################
    # CAPTURE SCREEN
    ##################################################

    def capture(
        self,
        filename="jarvis_screen.png"
    ):

        path = Path(
            filename
        )

        self.screenshot.save(
            str(path)
        )

        return path

    ##################################################
    # SCREEN SIZE
    ##################################################

    def _screenSize(
        self,
        screenshot
    ):

        image = Image.open(
            str(screenshot)
        )

        return image.size

    ##################################################
    # NORMALIZE TEXT
    ##################################################

    def _normalizeText(
        self,
        text
    ):

        return (

            str(text)
            .strip()
            .lower()
            .replace(
                "...",
                ""
            )
            .strip()

        )

    ##################################################
    # FIND TEXT
    ##################################################

    def find(
        self,
        target,
        screenshot=None
    ):

        normalized = self._normalizeText(
            target
        )

        ##################################################
        # YOUTUBE SEARCH
        ##################################################

        if normalized in (
            "search",
            "search bar",
            "youtube search"
        ):

            return self.findSearchBar(
                screenshot
            )

        ##################################################
        # CAPTURE
        ##################################################

        if screenshot is None:

            screenshot = self.capture()

        ##################################################
        # OCR
        ##################################################

        result = self.ocr.findText(
            str(screenshot),
            target
        )

        if result is None:

            print(
                f"[Locator] Could not find: "
                f"{target}"
            )

            return None

        ##################################################
        # OUTPUT
        ##################################################

        print(
            f"[Locator] Found: "
            f"{result['text']}"
        )

        print(
            f"[Locator] Position: "
            f"({result['x']}, {result['y']})"
        )

        print(
            f"[Locator] Confidence: "
            f"{result['confidence']:.2f}"
        )

        return result

    ##################################################
    # FIND YOUTUBE SEARCH BAR
    ##################################################

    def findSearchBar(
        self,
        screenshot=None,
        retries=3
    ):

        for attempt in range(
            retries
        ):

            ##################################################
            # FRESH SCREENSHOT
            ##################################################

            if screenshot is None:

                screenshot = self.capture(
                    "jarvis_search.png"
                )

            width, height = self._screenSize(
                screenshot
            )

            ##################################################
            # OCR
            ##################################################

            results = self.ocr.readImage(
                str(screenshot)
            )

            candidates = []

            ##################################################
            # SEARCH OCR
            ##################################################

            for result in results:

                if len(result) < 2:

                    continue

                box = result[0]

                text = str(
                    result[1]
                ).strip()

                confidence = (

                    float(result[2])

                    if len(result) > 2

                    else 0.0

                )

                normalized = self._normalizeText(
                    text
                )

                ##################################################
                # EXACT SEARCH MATCH
                ##################################################

                if normalized != "search":

                    continue

                ##################################################
                # CONFIDENCE
                ##################################################

                if confidence < 0.50:

                    continue

                ##################################################
                # BOUNDING BOX
                ##################################################

                xs = [

                    float(point[0])

                    for point in box

                ]

                ys = [

                    float(point[1])

                    for point in box

                ]

                left = min(xs)

                right = max(xs)

                top = min(ys)

                bottom = max(ys)

                center_x = (
                    left + right
                ) / 2

                center_y = (
                    top + bottom
                ) / 2

                ##################################################
                # SEARCH BAR LOCATION
                ##################################################

                if center_y > height * 0.20:

                    continue

                if center_x < width * 0.20:

                    continue

                if center_x > width * 0.80:

                    continue

                ##################################################
                # SCORE
                ##################################################

                y_distance = abs(
                    center_y -
                    height * 0.095
                )

                x_distance = abs(
                    center_x -
                    width * 0.50
                )

                score = (

                    confidence * 1000

                    - y_distance * 2

                    - x_distance * 0.5

                )

                candidates.append({

                    "text":
                        text,

                    "confidence":
                        confidence,

                    "x":
                        int(center_x),

                    "y":
                        int(center_y),

                    "box":
                        box,

                    "score":
                        score

                })

            ##################################################
            # FOUND
            ##################################################

            if candidates:

                candidates.sort(

                    key=lambda item:
                        item["score"],

                    reverse=True

                )

                best = candidates[0]

                print(
                    "[Locator] YouTube Search found:"
                )

                print(
                    f"[Locator] Position: "
                    f"({best['x']}, {best['y']})"
                )

                print(
                    f"[Locator] Confidence: "
                    f"{best['confidence']:.2f}"
                )

                return best

            ##################################################
            # RETRY
            ##################################################

            print(
                f"[Locator] Search bar not found "
                f"(attempt {attempt + 1}/{retries})"
            )

            screenshot = None

            if attempt < retries - 1:

                time.sleep(
                    1
                )

        ##################################################
        # DYNAMIC FALLBACK
        ##################################################

        screenshot = self.capture(
            "jarvis_search_fallback.png"
        )

        width, height = self._screenSize(
            screenshot
        )

        x = int(
            width * 0.50
        )

        y = int(
            height * 0.095
        )

        print(
            "[Locator] OCR could not identify Search."
        )

        print(
            "[Locator] Using dynamic search position: "
            f"({x}, {y})"
        )

        return {

            "text":
                "Search",

            "confidence":
                0.0,

            "x":
                x,

            "y":
                y,

            "box":
                None

        }

    ##################################################
    # CLICK
    ##################################################

    def click(
        self,
        target,
        screenshot=None
    ):

        result = self.find(
            target,
            screenshot
        )

        if result is None:

            return False

        x = result["x"]

        y = result["y"]

        print(
            f"[Locator] Clicking "
            f"({x}, {y})"
        )

        self.mouse.move(
            x,
            y
        )

        time.sleep(
            0.15
        )

        self.mouse.click()

        return True

    ##################################################
    # CLICK SEARCH BAR
    ##################################################

    def clickSearchBar(
        self
    ):

        result = self.findSearchBar()

        if result is None:

            return False

        x = result["x"]

        y = result["y"]

        print(
            f"[Locator] Clicking YouTube Search "
            f"({x}, {y})"
        )

        self.mouse.move(
            x,
            y
        )

        time.sleep(
            0.15
        )

        self.mouse.click()

        return True

    ##################################################
    # CLICK + TYPE + ENTER
    ##################################################

    def clickTypeEnter(
        self,
        target,
        text
    ):

        ##################################################
        # FIND / CLICK
        ##################################################

        normalized = self._normalizeText(
            target
        )

        if normalized in (
            "search",
            "search bar",
            "youtube search"
        ):

            clicked = self.clickSearchBar()

        else:

            clicked = self.click(
                target
            )

        ##################################################
        # CLICK FAILED
        ##################################################

        if not clicked:

            print(
                f"[ScreenAction] Could not click: "
                f"{target}"
            )

            return False

        ##################################################
        # TYPE
        ##################################################

        print(
            f"[ScreenAction] Typing: "
            f"{text}"
        )

        self.keyboard.type(
            str(text)
        )

        ##################################################
        # ENTER
        ##################################################

        print(
            "[Keyboard] Pressing: enter"
        )

        self.keyboard.press(
            "enter"
        )

        return True

    ##################################################
    # FIND FIRST VIDEO
    ##################################################

    def findFirstVideo(
        self,
        screenshot=None
    ):

        ##################################################
        # CAPTURE
        ##################################################

        if screenshot is None:

            screenshot = self.capture(
                "jarvis_results.png"
            )

        width, height = self._screenSize(
            screenshot
        )

        ##################################################
        # OCR
        ##################################################

        results = self.ocr.readImage(
            str(screenshot)
        )

        candidates = []

        ##################################################
        # UI TEXT TO IGNORE
        ##################################################

        ignored = {

            "home",
            "shorts",
            "subscriptions",
            "you",
            "filters",
            "live",
            "videos",
            "watched",
            "unwatched",
            "recently uploaded",
            "all",
            "search",
            "gaming",
            "music",
            "mixes",
            "minecraft modding",
            "trailers",
            "asmr",
            "cricket",
            "comedy",
            "simulations",
            "simulation video games",
            "presentation"

        }

        ##################################################
        # OCR RESULTS
        ##################################################

        for result in results:

            if len(result) < 3:

                continue

            box = result[0]

            text = str(
                result[1]
            ).strip()

            confidence = float(
                result[2]
            )

            if confidence < 0.60:

                continue

            ##################################################
            # BOX
            ##################################################

            xs = [

                float(point[0])

                for point in box

            ]

            ys = [

                float(point[1])

                for point in box

            ]

            left = min(xs)

            right = max(xs)

            top = min(ys)

            bottom = max(ys)

            box_width = (
                right - left
            )

            box_height = (
                bottom - top
            )

            center_x = (
                left + right
            ) / 2

            center_y = (
                top + bottom
            ) / 2

            normalized = self._normalizeText(
                text
            )

            ##################################################
            # BELOW NAVIGATION
            ##################################################

            if center_y < height * 0.20:

                continue

            ##################################################
            # NOT RIGHT-SIDE PANEL
            ##################################################

            if center_x > width * 0.70:

                continue

            ##################################################
            # NOT LEFT SIDEBAR
            ##################################################

            if center_x < width * 0.08:

                continue

            ##################################################
            # IGNORE SMALL UI
            ##################################################

            if box_width < 80:

                continue

            ##################################################
            # IGNORE TALL ELEMENTS
            ##################################################

            if box_height > 120:

                continue

            ##################################################
            # IGNORE UI
            ##################################################

            if normalized in ignored:

                continue

            ##################################################
            # SCORE
            ##################################################

            vertical_score = (

                1.0 -

                min(
                    center_y / height,
                    1.0
                )

            )

            center_score = (

                1.0 -

                abs(
                    center_x -
                    width * 0.38
                ) / width

            )

            score = (

                confidence * 5

                + vertical_score * 2

                + center_score

            )

            candidates.append({

                "text":
                    text,

                "confidence":
                    confidence,

                "x":
                    int(center_x),

                "y":
                    int(center_y),

                "box":
                    box,

                "top":
                    top,

                "left":
                    left,

                "width":
                    box_width,

                "height":
                    box_height,

                "score":
                    score

            })

        ##################################################
        # NONE
        ##################################################

        if not candidates:

            print(
                "[Locator] No video result found."
            )

            return None

        ##################################################
        # SORT
        ##################################################

        candidates.sort(

            key=lambda item: (

                item["top"],

                -item["score"]

            )

        )

        ##################################################
        # FIRST RESULT
        ##################################################

        first = candidates[0]

        print(
            "[Locator] First video candidate:"
        )

        print(
            f"[Locator] Text: "
            f"{first['text']}"
        )

        print(
            f"[Locator] Position: "
            f"({first['x']}, {first['y']})"
        )

        print(
            f"[Locator] Confidence: "
            f"{first['confidence']:.2f}"
        )

        return first

    ##################################################
    # CLICK FIRST VIDEO
    ##################################################

    def clickFirstVideo(
        self,
        screenshot=None
    ):

        result = self.findFirstVideo(
            screenshot
        )

        if result is None:

            return False

        x = result["x"]

        y = result["y"]

        print(
            f"[Locator] Clicking first video "
            f"at ({x}, {y})"
        )

        self.mouse.move(
            x,
            y
        )

        time.sleep(
            0.15
        )

        self.mouse.click()

        return True