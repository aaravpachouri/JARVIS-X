import json
import os
import tempfile
from pathlib import Path

import ollama
from PIL import Image, ImageOps


class LocalAIClient:

    # Local model defaults. Environment variables allow tuning without code edits.
    MODEL = "qwen3-vl:4b-instruct"
    REQUEST_TIMEOUT_SECONDS = 180
    NUM_CTX = 8192
    NUM_PREDICT = 384
    VISION_MAX_SIDE = 1600

    def __init__(self):
        self.model = os.getenv("JARVIS_LOCAL_MODEL", self.MODEL).strip() or self.MODEL
        self.timeout_seconds = self._positive_int(
            "JARVIS_LOCAL_TIMEOUT_SECONDS", self.REQUEST_TIMEOUT_SECONDS
        )
        self.num_ctx = self._positive_int("JARVIS_LOCAL_NUM_CTX", self.NUM_CTX)
        self.num_predict = self._positive_int(
            "JARVIS_LOCAL_NUM_PREDICT", self.NUM_PREDICT
        )
        self.vision_max_side = self._positive_int(
            "JARVIS_LOCAL_VISION_MAX_SIDE", self.VISION_MAX_SIDE
        )
        # Ollama calls are bounded so a stalled request cannot hang a mission forever.
        self.client = ollama.Client(timeout=self.timeout_seconds)
        print(f"[LocalAI] Model: {self.model}")
        print(
            f"[LocalAI] Timeout: {self.timeout_seconds}s; "
            f"context: {self.num_ctx}; max output: {self.num_predict} tokens"
        )

    @staticmethod
    def _positive_int(name, default):
        try:
            value = int(os.getenv(name, str(default)))
        except (TypeError, ValueError):
            return default
        return value if value > 0 else default

    def _prepare_vision_image(self, image_path):
        """Validate the screenshot and downscale oversized images for faster vision inference."""
        source = Path(image_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Vision image does not exist: {source}")

        try:
            with Image.open(source) as opened:
                image = ImageOps.exif_transpose(opened)
                image.load()
                width, height = image.size
                max_side = self.vision_max_side
                if max(width, height) <= max_side:
                    return str(source), None

                image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGB")

                handle = tempfile.NamedTemporaryFile(
                    prefix="jarvis_vision_",
                    suffix=".png",
                    delete=False,
                )
                prepared_path = Path(handle.name)
                handle.close()
                image.save(prepared_path, format="PNG", optimize=True)
                print(
                    f"[LocalAI] Resized vision image {width}x{height} -> "
                    f"{image.width}x{image.height}"
                )
                return str(prepared_path), prepared_path
        except (OSError, ValueError) as exc:
            raise ValueError(f"Could not read vision image '{source}': {exc}") from exc

    def chat(self, prompt, system=None):
        messages = []
        if system:
            messages.append({"role": "system", "content": str(system)})
        messages.append({"role": "user", "content": str(prompt)})

        response = self.client.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": 0.1,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict,
            },
            keep_alive="10m",
        )
        return response["message"]["content"]

    def vision(self, image_path, prompt, system=None):
        prepared_path, temporary_path = self._prepare_vision_image(image_path)
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": str(system)})
            messages.append(
                {
                    "role": "user",
                    "content": str(prompt),
                    "images": [prepared_path],
                }
            )
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": 0.05,
                    "num_ctx": self.num_ctx,
                    # Computer actions should be compact JSON, not long essays.
                    "num_predict": self.num_predict,
                },
                # Keep the model resident between observe/think iterations.
                keep_alive="10m",
            )
            content = response.get("message", {}).get("content", "")
            if not isinstance(content, str) or not content.strip():
                raise RuntimeError(
                    f"Ollama model '{self.model}' returned an empty vision response."
                )
            return content
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError as exc:
                    print(f"[LocalAI] Temporary vision image cleanup warning: {exc}")

    def json(self, prompt, system=None):
        return self._parse_json(self.chat(prompt, system))

    def vision_json(self, image_path, prompt, system=None):
        return self._parse_json(self.vision(image_path, prompt, system))

    @staticmethod
    def _parse_json(raw):
        text = str(raw or "").strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    pass
            raise ValueError("Local AI returned invalid JSON.")
