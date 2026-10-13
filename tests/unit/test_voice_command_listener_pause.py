import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


# The behavior under test is controller state, not Qt or microphone I/O.
qtcore = ModuleType("PySide6.QtCore")
qtcore.QObject = type("QObject", (), {})
qtcore.QThread = type("QThread", (), {})
qtcore.Signal = lambda *args, **kwargs: SimpleNamespace(emit=lambda *a: None)
qtcore.Slot = lambda *args, **kwargs: (lambda fn: fn)

speech_module = ModuleType("voice.speech_recognizer")
speech_module.SpeechRecognizer = type("SpeechRecognizer", (), {})
tts_module = ModuleType("voice.tts_manager")
tts_module.get_tts = lambda: SimpleNamespace(speak=lambda *a: None)
wake_module = ModuleType("voice.wake_detector")
wake_module.WakeDetector = type("WakeDetector", (), {})

with patch.dict(
    sys.modules,
    {
        "PySide6": ModuleType("PySide6"),
        "PySide6.QtCore": qtcore,
        "voice.speech_recognizer": speech_module,
        "voice.tts_manager": tts_module,
        "voice.wake_detector": wake_module,
    },
):
    from voice.voice_controller import VoiceController


def test_command_disables_listener_autorestart_until_command_finishes():
    controller = VoiceController.__new__(VoiceController)
    controller.active = True
    controller.busy = False
    controller.autoRestart = True
    controller.worker = SimpleNamespace(stop=lambda: None)
    controller.commandRecognized = SimpleNamespace(emit=lambda command: None)

    controller._commandReceived("open youtube")

    assert controller.busy is True
    assert controller.autoRestart is False


def test_command_finished_reenables_listener_autorestart():
    controller = VoiceController.__new__(VoiceController)
    controller.busy = True
    controller.running = False
    controller.active = True
    controller.autoRestart = False

    controller.commandFinished()

    assert controller.busy is False
    assert controller.autoRestart is True
