from ai.local_client import LocalAIClient


def test_chat_uses_expanded_context_window(monkeypatch):
    calls = []

    def fake_chat(**kwargs):
        calls.append(kwargs)
        return {"message": {"content": "ok"}}

    monkeypatch.setattr("ai.local_client.ollama.chat", fake_chat)

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

    monkeypatch.setattr("ai.local_client.ollama.chat", fake_chat)

    client = LocalAIClient()
    assert client.vision(str(image), "inspect") == '{"status":"CONTINUE"}'

    assert calls[0]["options"]["num_ctx"] == 8192
    assert calls[0]["messages"][-1]["images"] == [str(image.resolve())]
