from PySide6.QtCore import (
    QObject,
    QThread,
    Signal,
    Slot,
)

from voice.speech_recognizer import SpeechRecognizer
from voice.tts_manager import get_tts
from voice.wake_detector import WakeDetector


class VoiceController(QObject):

    ##################################################
    # SIGNALS
    ##################################################

    commandRecognized = Signal(str)

    wakeDetected = Signal()

    activated = Signal()

    deactivated = Signal()

    listeningStarted = Signal()

    listeningStopped = Signal()

    error = Signal(str)

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(
        self,
    ):

        super().__init__()

        ##################################################
        # SPEECH RECOGNITION
        ##################################################

        self.recognizer = SpeechRecognizer()

        ##################################################
        # WAKE WORD
        ##################################################

        self.wakeDetector = WakeDetector()

        ##################################################
        # TEXT TO SPEECH
        ##################################################

        self.tts = get_tts()

        ##################################################
        # THREAD
        ##################################################

        self.thread = None

        self.worker = None

        ##################################################
        # STATE
        ##################################################

        self.running = False

        self.active = False

        self.busy = False

        self.autoRestart = True

    ##################################################
    # START LISTENING
    ##################################################

    def startListening(
        self,
    ):

        if self.running:

            return

        self.running = True

        self.active = False

        self.busy = False

        self.autoRestart = True

        print(
            "[Voice] Voice system started."
        )

        print(
            "[Voice] JARVIS DORMANT."
        )

        self._createListener()

    ##################################################
    # CREATE LISTENER
    ##################################################

    def _createListener(
        self,
    ):

        if not self.running:

            return

        if self.worker is not None:

            return

        ##################################################
        # THREAD
        ##################################################

        self.thread = QThread()

        ##################################################
        # WORKER
        ##################################################

        self.worker = VoiceWorker(
            self.recognizer,
            self.wakeDetector,
            self.active,
        )

        self.worker.moveToThread(
            self.thread
        )

        ##################################################
        # START WORKER
        ##################################################

        self.thread.started.connect(
            self.worker.listen
        )

        ##################################################
        # COMMAND
        ##################################################

        self.worker.commandRecognized.connect(
            self._commandReceived
        )

        ##################################################
        # WAKE WORD
        ##################################################

        self.worker.wakeDetected.connect(
            self._wakeDetected
        )

        ##################################################
        # ERROR
        ##################################################

        self.worker.error.connect(
            self.error
        )

        ##################################################
        # FINISHED
        ##################################################

        self.worker.finished.connect(
            self._listenerFinished
        )

        ##################################################
        # START
        ##################################################

        self.listeningStarted.emit()

        self.thread.start()

    ##################################################
    # WAKE DETECTED
    ##################################################

    @Slot()
    def _wakeDetected(
        self,
    ):

        if self.active:

            return

        ##################################################
        # ACTIVATE
        ##################################################

        self.active = True

        print(
            "[Voice] HEY JARVIS DETECTED"
        )

        print(
            "[Voice] JARVIS ACTIVATED"
        )

        ##################################################
        # UPDATE UI
        ##################################################

        self.wakeDetected.emit()

        self.activated.emit()

        ##################################################
        # JARVIS SPEAKS
        ##################################################

        try:

            self.tts.speak(
                "Yes, sir?"
            )

        except Exception as exc:

            print(
                "[Voice] TTS error:",
                exc,
            )

    ##################################################
    # COMMAND RECEIVED
    ##################################################

    @Slot(str)
    def _commandReceived(
        self,
        command,
    ):

        command = str(
            command or ""
        ).strip()

        if not command:

            return

        ##################################################
        # MAKE SURE ACTIVE
        ##################################################

        if not self.active:

            self.active = True

            self.activated.emit()

        ##################################################
        # BUSY
        ##################################################

        self.busy = True

        print(
            f"[Voice] Command: {command}"
        )

        ##################################################
        # SEND COMMAND
        ##################################################

        self.commandRecognized.emit(
            command
        )

    ##################################################
    # COMMAND FINISHED
    ##################################################

    @Slot()
    def commandFinished(
        self,
    ):

        self.busy = False

        if not self.running:

            return

        if not self.active:

            return

        print(
            "[Voice] Command finished."
        )

        ##################################################
        # IMPORTANT:
        #
        # There is NO inactivity timeout anymore.
        #
        # JARVIS remains active indefinitely.
        ##################################################

        print(
            "[Voice] Active session continues."
        )

        ##################################################
        # CONTINUE LISTENING
        ##################################################

        if self.worker is None:

            self._createListener()

    ##################################################
    # SPEAK
    ##################################################

    def speak(
        self,
        text,
    ):

        text = str(
            text or ""
        ).strip()

        if not text:

            return

        try:

            self.tts.speak(
                text
            )

        except Exception as exc:

            print(
                "[Voice] TTS error:",
                exc,
            )

    ##################################################
    # DEACTIVATE
    ##################################################

    @Slot()
    def deactivate(
        self,
    ):

        if not self.active:

            return

        ##################################################
        # NEVER DEACTIVATE DURING COMMAND
        ##################################################

        if self.busy:

            print(
                "[Voice] "
                "Deactivation ignored - "
                "command running."
            )

            return

        ##################################################
        # DORMANT
        ##################################################

        print(
            "[Voice] JARVIS DEACTIVATED"
        )

        self.active = False

        ##################################################
        # UPDATE UI
        ##################################################

        self.deactivated.emit()

        ##################################################
        # STOP ACTIVE LISTENER
        ##################################################

        if self.worker:

            self.worker.stop()

    ##################################################
    # STOP LISTENING
    ##################################################

    def stopListening(
        self,
    ):

        self.autoRestart = False

        self.running = False

        self.active = False

        self.busy = False

        ##################################################
        # STOP WORKER
        ##################################################

        if self.worker:

            self.worker.stop()

        ##################################################
        # STOP TTS
        ##################################################

        try:

            self.tts.stop()

        except Exception:
            pass

    ##################################################
    # PAUSE LISTENING
    ##################################################

    def pauseListening(
        self,
    ):

        self.autoRestart = False

        self.running = False

        if self.worker:

            self.worker.stop()

    ##################################################
    # RESUME LISTENING
    ##################################################

    def resumeListening(
        self,
    ):

        if self.running:

            return

        self.running = True

        self.busy = False

        self.autoRestart = True

        ##################################################
        # Preserve current active state when resuming.
        ##################################################

        self._createListener()

    ##################################################
    # LISTENER FINISHED
    ##################################################

    @Slot()
    def _listenerFinished(
        self,
    ):

        self.listeningStopped.emit()

        ##################################################
        # SAVE REFERENCES
        ##################################################

        thread = self.thread

        worker = self.worker

        ##################################################
        # CLEAR REFERENCES
        ##################################################

        self.thread = None

        self.worker = None

        ##################################################
        # CLEAN THREAD
        ##################################################

        if thread:

            thread.quit()

            thread.deleteLater()

        if worker:

            worker.deleteLater()

        ##################################################
        # AUTOMATIC RESTART
        ##################################################

        if (
            self.running
            and self.autoRestart
            and not self.busy
        ):

            self._createListener()


######################################################
# VOICE WORKER
######################################################


class VoiceWorker(QObject):

    ##################################################
    # SIGNALS
    ##################################################

    commandRecognized = Signal(str)

    wakeDetected = Signal()

    finished = Signal()

    error = Signal(str)

    ##################################################
    # INITIALIZATION
    ##################################################

    def __init__(
        self,
        recognizer,
        wakeDetector,
        active=False,
    ):

        super().__init__()

        self.recognizer = recognizer

        self.wakeDetector = wakeDetector

        self.active = active

        self.running = True

    ##################################################
    # STOP
    ##################################################

    def stop(
        self,
    ):

        self.running = False

    ##################################################
    # LISTEN
    ##################################################

    @Slot()
    def listen(
        self,
    ):

        try:

            if not self.running:

                return

            ##################################################
            # DORMANT MODE
            ##################################################

            if not self.active:

                print(
                    "[Voice] "
                    "DORMANT - "
                    "waiting for Hey JARVIS..."
                )

                event = (
                    self.wakeDetector.listen()
                )

                if not self.running:

                    return

                ##################################################
                # ONLY WAKE WORD
                ##################################################

                if event != "WAKE":

                    print(
                        "[Voice] "
                        f"Ignored wake event: {event}"
                    )

                    return

                ##################################################
                # WAKE DETECTED
                ##################################################

                print(
                    "[Voice] "
                    "Hey JARVIS detected."
                )

                self.wakeDetected.emit()

                ##################################################
                # COMMAND
                ##################################################

                print(
                    "[Voice] "
                    "Active listening..."
                )

                command = (
                    self.recognizer.listen()
                )

                if (
                    command
                    and
                    self.running
                ):

                    print(
                        "[Voice] "
                        f"Command: {command}"
                    )

                    self.commandRecognized.emit(
                        command
                    )

                return

            ##################################################
            # ACTIVE MODE
            ##################################################

            print(
                "[Voice] Active listening..."
            )

            command = (
                self.recognizer.listen()
            )

            if (
                command
                and
                self.running
            ):

                print(
                    "[Voice] "
                    f"Command: {command}"
                )

                self.commandRecognized.emit(
                    command
                )

        except Exception as exc:

            print(
                "[Voice] Error:",
                exc,
            )

            self.error.emit(
                str(exc)
            )

        finally:

            self.finished.emit()