import tempfile
from pathlib import Path


from automation.screenshot.service import ScreenshotService
from automation.ocr.service import OCRService


class AgentObserver:
    """
    JARVIS X
    COMPUTER OBSERVATION LAYER

    Responsibilities:
        - Capture the current screen
        - Keep screenshots outside the Desktop
        - Reuse one temporary screenshot
        - Read screenshot bytes
        - Perform OCR
        - Compress OCR output for the local model
        - Delete temporary screenshots automatically

    IMPORTANT:
        Screenshots used for computer reasoning are runtime
        artifacts only. They are never intentionally stored
        on the Desktop or accumulated between tasks.
    """

    # ==================================================
    # INITIALIZATION
    # ==================================================

    def __init__(
        self
    ):
        self.screenshot = (
            ScreenshotService()
        )

        self.ocr = (
            OCRService()
        )

        # Windows temporary directory.
        # This avoids Desktop storage completely.
        self.temp_dir = (
            Path(
                tempfile.gettempdir()
            )
            / "jarvis_runtime"
        )

        self.temp_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.current_path = (
            self.temp_dir
            / "current_screen.png"
        )

    # ==================================================
    # CAPTURE
    # ==================================================

    def capture_to_temp(
        self
    ):
        """
        Capture the current screen to one reusable
        temporary file.

        The same filename is reused every time.
        """

        path = self.current_path

        # Remove previous capture first.
        self.delete_temp(
            path
        )

        saved = self.screenshot.save(
            str(path)
        )

        if saved is None:
            raise RuntimeError(
                "Screenshot service did not return a path."
            )

        return str(
            saved
        )

    # ==================================================
    # READ BYTES
    # ==================================================

    def read_bytes(
        self,
        path
    ):
        """
        Read screenshot bytes for the vision model.
        """

        if not path:
            raise ValueError(
                "Screenshot path is empty."
            )

        target = Path(
            path
        )

        if not target.exists():
            raise FileNotFoundError(
                f"Screenshot does not exist: {target}"
            )

        return target.read_bytes()

    # ==================================================
    # CAPTURE IMAGE
    # ==================================================

    def capture(
        self
    ):
        """
        Capture screen and return image bytes.

        The temporary file is deleted immediately after
        its contents have been read.
        """

        path = None

        try:
            path = self.capture_to_temp()

            return self.read_bytes(
                path
            )

        finally:
            self.delete_temp(
                path
            )

    # ==================================================
    # CAPTURE WITH OCR
    # ==================================================

    def capture_with_ocr(
        self
    ):
        """
        Capture the screen, read image bytes and OCR,
        then remove the temporary screenshot.

        Returns:

            (
                image_bytes,
                compact_ocr
            )
        """

        path = None

        try:
            path = self.capture_to_temp()

            image = self.read_bytes(
                path
            )

            try:
                ocr = self.ocr.readImage(
                    path
                )
            except Exception:
                ocr = []

            return (
                image,
                self.compact_ocr(
                    ocr
                )
            )

        finally:
            self.delete_temp(
                path
            )

    # ==================================================
    # CAPTURE RAW
    # ==================================================

    def capture_raw(
        self
    ):
        """
        Compatibility method.

        Returns:
            {
                "image": bytes,
                "ocr": [...]
            }
        """

        image, ocr = (
            self.capture_with_ocr()
        )

        return {
            "image": image,
            "ocr": ocr
        }

    # ==================================================
    # OCR ONLY
    # ==================================================

    def read_ocr(
        self,
        path
    ):
        """
        Run OCR on an existing image path.
        """

        try:
            return self.ocr.readImage(
                str(path)
            )
        except Exception:
            return []

    # ==================================================
    # DELETE TEMP
    # ==================================================

    def delete_temp(
        self,
        path
    ):
        """
        Delete one temporary runtime file.
        """

        if not path:
            return

        try:
            target = Path(
                path
            )

            if target.exists():
                target.unlink()

        except Exception:
            # Cleanup must never crash the computer
            # automation system.
            pass

    # ==================================================
    # CLEAN ALL
    # ==================================================

    def cleanup(
        self
    ):
        """
        Remove all temporary JARVIS runtime files.
        """

        try:

            if not self.temp_dir.exists():
                return

            for item in self.temp_dir.iterdir():

                try:

                    if item.is_file():
                        item.unlink()

                    elif item.is_dir():
                        # Do not recursively destroy arbitrary
                        # directories. Runtime screenshots are
                        # files only.
                        continue

                except Exception:
                    pass

        except Exception:
            pass

    # ==================================================
    # OCR COMPRESSION
    # ==================================================

    @staticmethod
    def compact_ocr(
        results,
        limit=150
    ):
        """
        Convert raw OCR output into a compact representation
        suitable for the local vision/reasoning layer.

        Supported OCR shape:

            (
                bounding_box,
                text,
                confidence
            )
        """

        items = []

        if not isinstance(
            results,
            list
        ):
            return items

        try:
            limit = max(
                1,
                int(limit)
            )
        except Exception:
            limit = 150

        for result in results[:limit]:

            if not isinstance(
                result,
                (list, tuple)
            ):
                continue

            if len(result) < 2:
                continue

            text = str(
                result[1]
            ).strip()

            if not text:
                continue

            # ----------------------------------------------
            # CONFIDENCE
            # ----------------------------------------------

            try:

                confidence = float(
                    result[2]
                )

            except Exception:

                confidence = 0.0

            item = {
                "text":
                    text,

                "confidence":
                    round(
                        confidence,
                        3
                    )
            }

            # ----------------------------------------------
            # BOUNDING BOX
            # ----------------------------------------------

            box = (
                result[0]
                if len(result) > 0
                else None
            )

            try:

                xs = [
                    float(
                        point[0]
                    )
                    for point in box
                ]

                ys = [
                    float(
                        point[1]
                    )
                    for point in box
                ]

                if xs and ys:

                    item["x"] = round(
                        (
                            min(xs)
                            +
                            max(xs)
                        ) / 2
                    )

                    item["y"] = round(
                        (
                            min(ys)
                            +
                            max(ys)
                        ) / 2
                    )

                    item["left"] = round(
                        min(xs)
                    )

                    item["top"] = round(
                        min(ys)
                    )

                    item["right"] = round(
                        max(xs)
                    )

                    item["bottom"] = round(
                        max(ys)
                    )

            except Exception:
                pass

            items.append(
                item
            )

        return items

    # ==================================================
    # CONTEXT
    # ==================================================

    def observe(
        self
    ):
        """
        One complete observation cycle.

        This is the preferred method for the autonomous
        computer kernel.

        Returns:
            {
                "image": bytes,
                "ocr": [...]
            }
        """

        image, ocr = (
            self.capture_with_ocr()
        )

        return {
            "image":
                image,

            "ocr":
                ocr
        }

    # ==================================================
    # SHUTDOWN
    # ==================================================

    def close(
        self
    ):
        """
        Final cleanup hook.
        """

        self.cleanup()

    # ==================================================
    # CONTEXT MANAGER
    # ==================================================

    def __enter__(
        self
    ):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):
        self.cleanup()
        return False