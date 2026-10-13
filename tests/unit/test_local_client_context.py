import sys
from types import ModuleType
from unittest.mock import patch


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


def test_chat_uses_expanded_context_window(monkeypatch):
    calls = []

    def fake_chat(**kwargs):
        calls.append(kwargs)
        return {"message": {"content": "ok"}}

    monkeypatch.setattr("ai.local_client.ollama.Client", lambda timeout=None: type("FakeClient", (), {"chat": staticmethod(fake_chat)})())

    client = LocalAIClient()
    assert client.chat("hello") == "ok"

    assert calls[0]["options"]["num_ctx"] == 8192


def test_vision_uses_expanded_context_window(monkeypatch, tmp_path):
    calls = []

    def fake_chat(**kwargs):
        calls.append(kwargs)
        return {"message": {"content": '{"status":"CONTINUE"}'}}

    image = tmp_path / "screen.png"
    image.write_bytes(b"fake image")

    monkeypatch.setattr("ai.local_client.ollama.Client", lambda timeout=None: type("FakeClient", (), {"chat": staticmethod(fake_chat)})())

    client = LocalAIClient()
    assert client.vision(str(image), "inspect") == '{"status":"CONTINUE"}'

    assert calls[0]["options"]["num_ctx"] == 8192
    assert calls[0]["messages"][-1]["images"] == [str(image.resolve())]


def test_local_client_sets_bounded_ollama_timeout():
    captured = {}

    class FakeClient:
        def __init__(self, timeout=None):
            captured["timeout"] = timeout

        def chat(self, **kwargs):
            return {"message": {"content": "ok"}}

    with patch("ai.local_client.ollama.Client", FakeClient):
        client = LocalAIClient()
        assert client.chat("hello") == "ok"

    assert captured["timeout"] == 180
