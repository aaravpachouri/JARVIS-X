from pathlib import Path
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


class AIClient:
    def __init__(self):
        project_root = Path(__file__).resolve().parent.parent
        load_dotenv(project_root / ".env")
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        self.model = os.getenv("JARVIS_GEMINI_MODEL", "gemini-flash-latest")
        self.client = genai.Client(api_key=self.api_key)

    def chat(self, message):
        response = self.client.models.generate_content(
            model=self.model,
            contents=message,
        )
        return (response.text or "").strip()

    def vision(self, image_bytes, instruction, mime_type="image/png"):
        image = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        response = self.client.models.generate_content(
            model=self.model,
            contents=[instruction, image],
        )
        return (response.text or "").strip()
