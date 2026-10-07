import json
from pathlib import Path

import ollama


class LocalAIClient:

    ##################################################
    # CONFIGURATION
    ##################################################

    MODEL = "qwen3-vl:4b"

    def __init__(self):

        self.model = self.MODEL

        print(
            f"[LocalAI] Model: {self.model}"
        )

    ##################################################
    # BASIC CHAT
    ##################################################

    def chat(
        self,
        prompt,
        system=None
    ):

        messages = []

        if system:

            messages.append(
                {
                    "role": "system",
                    "content": str(system)
                }
            )

        messages.append(
            {
                "role": "user",
                "content": str(prompt)
            }
        )

        response = ollama.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": 0.1
            }
        )

        return (
            response["message"]["content"]
        )

    ##################################################
    # VISION
    ##################################################

    def vision(
        self,
        image_path,
        prompt,
        system=None
    ):

        image_path = str(
            Path(image_path).resolve()
        )

        messages = []

        if system:

            messages.append(
                {
                    "role": "system",
                    "content": str(system)
                }
            )

        messages.append(
            {
                "role": "user",
                "content": str(prompt),
                "images": [
                    image_path
                ]
            }
        )

        response = ollama.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": 0.05
            }
        )

        return (
            response["message"]["content"]
        )

    ##################################################
    # JSON CHAT
    ##################################################

    def json(
        self,
        prompt,
        system=None
    ):

        raw = self.chat(
            prompt,
            system
        )

        return self._parse_json(
            raw
        )

    ##################################################
    # JSON VISION
    ##################################################

    def vision_json(
        self,
        image_path,
        prompt,
        system=None
    ):

        raw = self.vision(
            image_path,
            prompt,
            system
        )

        return self._parse_json(
            raw
        )

    ##################################################
    # JSON PARSER
    ##################################################

    @staticmethod
    def _parse_json(raw):

        text = str(
            raw or ""
        ).strip()

        if text.startswith(
            "```"
        ):

            lines = text.splitlines()

            if lines:

                lines = lines[1:]

            if lines and lines[-1].strip() == "```":

                lines = lines[:-1]

            text = "\n".join(
                lines
            ).strip()

        try:

            return json.loads(
                text
            )

        except Exception:

            start = text.find(
                "{"
            )

            end = text.rfind(
                "}"
            )

            if (
                start >= 0
                and end > start
            ):

                return json.loads(
                    text[
                        start:
                        end + 1
                    ]
                )

            raise ValueError(
                "Local AI returned invalid JSON."
            )