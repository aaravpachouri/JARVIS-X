from voice.voice_controller import VoiceController


def test_command_disables_listener_autorestart_until_command_finishes():
    controller = VoiceController.__new__(VoiceController)
    controller.active = True
    controller.busy = False
    controller.autoRestart = True
    controller.worker = object()
    controller.commandRecognized = type(
        "SignalStub",
        (),
        {"emit": lambda self, command: None},
    )()

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
