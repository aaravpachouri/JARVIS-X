import sys
from types import ModuleType
from unittest.mock import patch

from PIL import Image


# Ollama is the external inference runtime; these tests mock its chat call.
ollama_stub = ModuleType("ollama")
ollama_stub.chat = lambda **kwargs: None


class StubClient:
    def __init__(self, timeout=None):
        self.timeout = timeout

    def chat(self, **kwargs):
        return ollama_stub.chat(**kwargs)


ollama_stub.Client = StubClient

with patch.dict(sys.modules, {"ollama": ollama_stub}):
    from ai.local_client import LocalAIClient


def make_image(path, size=(320, 180)):
    Image.new("RGB", size, color="white").save(path, format="PNG")
    return path


def test_chat_uses_bounded_generation_options(monkeypatch):
    calls = []

    def fake_chat(**kwargs):
        calls.append(kwargs)
        return {"message": {"content": "ok"}}

    monkeypatch.setattr(
        "ai.local_client.ollama.Client",
        lambda timeout=None: type("FakeClient", (), {"chat": staticmethod(fake_chat)})(),
    )

    client = LocalAIClient()
    assert client.chat("hello") == "ok"
    assert calls[0]["options"]["num_ctx"] == 8192
    assert calls[0]["options"]["num_predict"] == 384
    assert calls[0]["keep_alive"] == "10m"


def test_vision_uses_image_and_bounded_generation_options(monkeypatch, tmp_path):
    calls = []
    image = make_image(tmp_path / "screen.png")

    def fake_chat(**kwargs):
        calls.append(kwargs)
        return {"message": {"content": '{"status":"CONTINUE"}'}}

    monkeypatch.setattr(
        "ai.local_client.ollama.Client",
        lambda timeout=None: type("FakeClient", (), {"chat": staticmethod(fake_chat)})(),
    )

    client = LocalAIClient()
    assert client.vision(str(image), "inspect") == '{"status":"CONTINUE"}'
    assert calls[0]["options"]["num_ctx"] == 8192
    assert calls[0]["options"]["num_predict"] == 384
    assert calls[0]["keep_alive"] == "10m"
    assert calls[0]["messages"][-1]["images"] == [str(image.resolve())]


def test_oversized_vision_image_is_resized_and_temp_file_removed(monkeypatch, tmp_path):
    image = make_image(tmp_path / "large.png", size=(2400, 1200))
    captured = {}

    def fake_chat(**kwargs):
        sent_path = kwargs["messages"][-1]["images"][0]
        captured["path"] = sent_path
        with Image.open(sent_path) as sent_image:
            captured["size"] = sent_image.size
        return {"message": {"content": "ok"}}

    monkeypatch.setattr(
        "ai.local_client.ollama.Client",
        lambda timeout=None: type("FakeClient", (), {"chat": staticmethod(fake_chat)})(),
    )

    client = LocalAIClient()
    assert client.vision(str(image), "inspect") == "ok"
    assert captured["size"] == (1600, 800)
    assert captured["path"] != str(image.resolve())
    assert not __import__("pathlib").Path(captured["path"]).exists()


def test_missing_vision_image_fails_before_ollama_call(monkeypatch, tmp_path):
    def unexpected_chat(**kwargs):
        raise AssertionError("Ollama must not be called for a missing image")

    monkeypatch.setattr(
        "ai.local_client.ollama.Client",
        lambda timeout=None: type("FakeClient", (), {"chat": staticmethod(unexpected_chat)})(),
    )
    client = LocalAIClient()
    try:
        client.vision(str(tmp_path / "missing.png"), "inspect")
    except FileNotFoundError as exc:
        assert "Vision image does not exist" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")


def test_local_client_sets_bounded_ollama_timeout(monkeypatch):
    captured = {}

    class FakeClient:
        def __init__(self, timeout=None):
            captured["timeout"] = timeout

        def chat(self, **kwargs):
            return {"message": {"content": "ok"}}

    with patch("ai.local_client.ollama.Client", FakeClient):
        LocalAIClient()

    assert captured["timeout"] == 180


def test_local_client_timeout_can_be_configured(monkeypatch):
    monkeypatch.setenv("JARVIS_LOCAL_TIMEOUT_SECONDS", "75")
    captured = {}

    class FakeClient:
        def __init__(self, timeout=None):
            captured["timeout"] = timeout

        def chat(self, **kwargs):
            return {"message": {"content": "ok"}}

    with patch("ai.local_client.ollama.Client", FakeClient):
        LocalAIClient()

    assert captured["timeout"] == 75


def test_local_client_uses_computer_vision_model_by_default(monkeypatch):
    monkeypatch.delenv("JARVIS_LOCAL_MODEL", raising=False)
    client = LocalAIClient()
    assert client.model == "qwen3-vl:4b-instruct"


def test_local_client_model_can_be_configured(monkeypatch):
    monkeypatch.setenv("JARVIS_LOCAL_MODEL", "qwen3-vl:4b")
    client = LocalAIClient()
    assert client.model == "qwen3-vl:4b"
