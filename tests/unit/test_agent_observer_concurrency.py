from backend.agent_observer import AgentObserver


def test_concurrent_observations_use_distinct_temp_files(monkeypatch):
    observer = AgentObserver()

    def fake_save(path):
        with open(path, "wb") as screenshot:
            screenshot.write(b"fake screenshot")
        return path

    monkeypatch.setattr(observer.screenshot, "save", fake_save)

    first = observer.capture_to_temp()
    second = observer.capture_to_temp()

    try:
        assert first != second
        assert observer.read_bytes(first) == b"fake screenshot"
        assert observer.read_bytes(second) == b"fake screenshot"
    finally:
        observer.delete_temp(first)
        observer.delete_temp(second)
