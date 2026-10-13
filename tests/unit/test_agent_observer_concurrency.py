import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


# The unit test checks temp-file behavior, not real desktop capture or OCR.
# Stub those service imports so CI doesn't need mss/easyocr installed.
screenshot_service = ModuleType("automation.screenshot.service")
screenshot_service.ScreenshotService = type("ScreenshotService", (), {})
ocr_service = ModuleType("automation.ocr.service")
ocr_service.OCRService = type("OCRService", (), {})

with patch.dict(
    sys.modules,
    {
        "automation.screenshot.service": screenshot_service,
        "automation.ocr.service": ocr_service,
    },
):
    from backend.agent_observer import AgentObserver


def test_concurrent_observations_use_distinct_temp_files(tmp_path):
    observer = AgentObserver.__new__(AgentObserver)
    observer.temp_dir = tmp_path

    def fake_save(path):
        with open(path, "wb") as screenshot:
            screenshot.write(b"fake screenshot")
        return path

    observer.screenshot = SimpleNamespace(save=fake_save)

    first = observer.capture_to_temp()
    second = observer.capture_to_temp()

    try:
        assert first != second
        assert observer.read_bytes(first) == b"fake screenshot"
        assert observer.read_bytes(second) == b"fake screenshot"
    finally:
        observer.delete_temp(first)
        observer.delete_temp(second)
