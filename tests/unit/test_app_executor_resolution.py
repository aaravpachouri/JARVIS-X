from pathlib import Path

from automation.executors.app_executor import AppExecutor


def test_resolve_chrome_checks_standard_install_locations(monkeypatch, tmp_path):
    chrome = tmp_path / "Google" / "Chrome" / "Application" / "chrome.exe"
    chrome.parent.mkdir(parents=True)
    chrome.write_text("stub", encoding="utf-8")

    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    monkeypatch.setenv("ProgramFiles(x86)", str(tmp_path / "x86"))
    monkeypatch.setenv("LocalAppData", str(tmp_path / "local"))

    executor = AppExecutor()
    monkeypatch.setattr("automation.executors.app_executor.shutil.which", lambda _: None)

    assert executor.resolve("Chrome") == str(chrome.resolve())


def test_resolve_chrome_returns_none_when_not_installed(monkeypatch, tmp_path):
    monkeypatch.setenv("ProgramFiles", str(tmp_path / "pf"))
    monkeypatch.setenv("ProgramFiles(x86)", str(tmp_path / "x86"))
    monkeypatch.setenv("LocalAppData", str(tmp_path / "local"))
    monkeypatch.setattr("automation.executors.app_executor.shutil.which", lambda _: None)

    assert AppExecutor().resolve("Chrome") is None
