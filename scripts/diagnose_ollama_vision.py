"""Smoke-test Ollama vision separately from JARVIS UI, voice, and automation.

Run from the repository root:
    python scripts/diagnose_ollama_vision.py
    python scripts/diagnose_ollama_vision.py --image path/to/image.png
"""
from __future__ import annotations

import argparse
import sys
import tempfile
import time
from pathlib import Path

# Executing a file inside scripts/ puts that directory, not the repository
# root, at sys.path[0]. Add the detected project root so `ai.local_client`
# resolves reliably even when launched from another working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check whether the configured local Ollama model can interpret an image."
    )
    parser.add_argument(
        "--image",
        type=Path,
        help="Use an existing image instead of capturing the current screen.",
    )
    args = parser.parse_args()

    temporary_image = None
    image_path = args.image.expanduser().resolve() if args.image else None

    try:
        if image_path is None:
            try:
                import pyautogui
            except Exception as exc:
                raise RuntimeError(
                    "Could not import the screenshot dependency. "
                    "Run this from JARVIS-X's activated environment."
                ) from exc

            handle = tempfile.NamedTemporaryFile(
                prefix="jarvis_vision_smoke_",
                suffix=".png",
                delete=False,
            )
            temporary_image = Path(handle.name)
            handle.close()
            pyautogui.screenshot().save(temporary_image)
            image_path = temporary_image

        if not image_path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")

        from ai.local_client import LocalAIClient

        print("[VisionCheck] Image captured/loaded.")
        client = LocalAIClient()
        print(f"[VisionCheck] Sending one read-only image request to {client.model}...")
        started = time.monotonic()
        answer = client.vision(
            str(image_path),
            "Describe the visible screen in one short sentence. "
            "Do not suggest or execute any computer actions.",
        )
        elapsed = time.monotonic() - started

        print(f"[VisionCheck] SUCCESS in {elapsed:.1f}s")
        print(f"[VisionCheck] Model response: {answer.strip()}")
        return 0

    except Exception as exc:
        print(f"[VisionCheck] FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "[VisionCheck] This test does not run the voice listener or execute desktop actions.",
            file=sys.stderr,
        )
        return 1
    finally:
        if temporary_image is not None:
            try:
                temporary_image.unlink(missing_ok=True)
            except OSError as exc:
                print(f"[VisionCheck] Temporary screenshot cleanup warning: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
