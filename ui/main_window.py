from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QSizePolicy,
)

from PySide6.QtGui import (
    QKeySequence,
    QShortcut,
)

from PySide6.QtCore import (
    Qt,
    QObject,
    QThread,
    Signal,
    Slot,
    QTimer,
)

from ui.styles import MAIN_STYLE
from ui.top_bar import TopBar
from ui.ai_status import AIStatus
from ui.components.arc_reactor import ArcReactor
from ui.components.telemetry_panel import TelemetryPanel
from ui.components.ai_console import AIConsole
from ui.components.analytics_dashboard import (
    AnalyticsDashboard,
)

from backend.ai_controller import AIController

from automation.runtime_state import (
    RuntimeStateSynchronizer,
)

from voice.voice_controller import VoiceController


############################################################
# COMMAND WORKER
############################################################

class CommandWorker(QObject):

    finished = Signal(int, str)

    error = Signal(int, str)

    def __init__(
        self,
        controller,
        command,
        command_id,
    ):

        super().__init__()

        self.controller = controller

        self.command = command

        self.command_id = int(
            command_id
        )

    @Slot()
    def run(
        self,
    ):

        try:

            result = self.controller.execute(
                self.command
            )

            self.finished.emit(
                self.command_id,
                str(result or ""),
            )

        except Exception as exc:

            self.error.emit(
                self.command_id,
                str(exc),
            )


############################################################
# MAIN WINDOW
############################################################

class MainWindow(QMainWindow):

    """
    JARVIS X MAIN HUD

    DEFAULT WORKSPACE:

        LEFT   = System Telemetry
        CENTER = AI Status + Arc Reactor
        RIGHT  = AI Console

    ANALYTICS:

        Dedicated Business Intelligence workspace.

    WORKSPACE RULE:

        Main HUD and Analytics occupy exactly the same
        workspace rectangle.

    ACCESS RULE:

        Ctrl+Shift+A works only after JARVIS has been
        activated by the wake word.
    """

    ############################################################
    # INITIALIZATION
    ############################################################

    def __init__(
        self,
    ):

        super().__init__()

        ########################################################
        # WINDOW
        ########################################################

        self.setWindowTitle(
            "JARVIS X"
        )

        self.resize(
            1920,
            1080,
        )

        self.setMinimumSize(
            1500,
            850,
        )

        self.setStyleSheet(
            MAIN_STYLE
        )

        ########################################################
        # CONTROLLERS
        ########################################################

        self.controller = AIController()

        self.currentThread = None

        self.currentWorker = None

        ########################################################
        # INTERFACE STATE
        ########################################################

        self.interfaceActive = False

        self.analyticsMode = False

        ########################################################
        # RUNTIME STATE
        ########################################################

        self.runtimeState = (
            RuntimeStateSynchronizer()
        )

        self.runtimeTimer = QTimer(
            self
        )

        self.runtimeTimer.setInterval(
            250
        )

        self.runtimeTimer.timeout.connect(
            self.updateRuntimeState
        )

        self.runtimeTimer.start()

        ########################################################
        # COMMAND GENERATION
        ########################################################

        self._command_counter = 0

        self._active_command_id = 0

        self._interrupted_command_ids = set()

        ########################################################
        # VOICE
        ########################################################

        self.voiceController = VoiceController()

        self.voiceController.commandRecognized.connect(
            self.handleVoiceCommand
        )

        self.voiceController.activated.connect(
            self.activateInterface
        )

        self.voiceController.deactivated.connect(
            self.deactivateInterface
        )

        self.voiceController.error.connect(
            self.voiceError
        )

        ########################################################
        # CENTRAL ROOT
        ########################################################

        central = QWidget()

        central.setObjectName(
            "JarvisCentral"
        )

        self.setCentralWidget(
            central
        )

        self.root = QVBoxLayout(
            central
        )

        self.root.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.root.setSpacing(
            0
        )

        ########################################################
        # TOP BAR
        ########################################################

        self.topBar = TopBar()

        self.root.addWidget(
            self.topBar
        )

        ########################################################
        # WORKSPACE CONTAINER
        #
        # IMPORTANT:
        #
        # Both the original HUD and analytics screen live
        # inside this exact same rectangle.
        ########################################################

        self.workspace = QWidget()

        self.workspace.setObjectName(
            "JarvisWorkspace"
        )

        self.workspaceLayout = QVBoxLayout(
            self.workspace
        )

        self.workspaceLayout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.workspaceLayout.setSpacing(
            0
        )

        self.root.addWidget(
            self.workspace,
            1,
        )

        ########################################################
        # MAIN HUD
        ########################################################

        self.mainArea = QFrame()

        self.mainArea.setObjectName(
            "MainArea"
        )

        self.workspaceLayout.addWidget(
            self.mainArea,
            1,
        )

        ########################################################
        # ORIGINAL THREE-COLUMN HUD
        ########################################################

        self.canvasLayout = QHBoxLayout(
            self.mainArea
        )

        self.canvasLayout.setContentsMargins(
            40,
            20,
            40,
            20,
        )

        self.canvasLayout.setSpacing(
            35
        )

        ########################################################
        # LEFT PANEL
        ########################################################

        self.leftPanel = QWidget()

        self.leftPanel.setFixedWidth(
            340
        )

        self.leftPanel.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding,
        )

        self.leftLayout = QVBoxLayout(
            self.leftPanel
        )

        self.leftLayout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.leftLayout.setSpacing(
            0
        )

        self.telemetry = TelemetryPanel()

        self.telemetry.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Maximum,
        )

        self.leftLayout.addWidget(
            self.telemetry,
            0,
            Qt.AlignTop,
        )

        self.leftLayout.addStretch(
            1
        )

        ########################################################
        # CENTER PANEL
        ########################################################

        self.centerPanel = QWidget()

        self.centerPanel.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.centerLayout = QVBoxLayout(
            self.centerPanel
        )

        self.centerLayout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.centerLayout.setSpacing(
            8
        )

        self.centerLayout.setAlignment(
            Qt.AlignCenter
        )

        ########################################################
        # AI STATUS
        ########################################################

        self.aiStatus = AIStatus()

        self.aiStatus.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed,
        )

        self.centerLayout.addWidget(
            self.aiStatus,
            0,
            Qt.AlignHCenter,
        )

        ########################################################
        # REACTOR
        ########################################################

        self.reactorContainer = QWidget()

        self.reactorContainer.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.reactorContainerLayout = QVBoxLayout(
            self.reactorContainer
        )

        self.reactorContainerLayout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.reactorContainerLayout.setAlignment(
            Qt.AlignCenter
        )

        self.reactor = ArcReactor()

        self.reactorContainerLayout.addWidget(
            self.reactor,
            0,
            Qt.AlignCenter,
        )

        self.centerLayout.addWidget(
            self.reactorContainer,
            1,
        )

        ########################################################
        # RIGHT PANEL
        ########################################################

        self.rightPanel = QWidget()

        self.rightPanel.setFixedWidth(
            340
        )

        self.rightPanel.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding,
        )

        self.rightLayout = QVBoxLayout(
            self.rightPanel
        )

        self.rightLayout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.rightLayout.setSpacing(
            0
        )

        self.aiConsole = AIConsole()

        self.aiConsole.setFixedWidth(
            340
        )

        self.aiConsole.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )

        self.rightLayout.addWidget(
            self.aiConsole,
            0,
            Qt.AlignTop,
        )

        self.rightLayout.addStretch(
            1
        )

        ########################################################
        # ADD ORIGINAL HUD PANELS
        ########################################################

        self.canvasLayout.addWidget(
            self.leftPanel,
            0,
        )

        self.canvasLayout.addWidget(
            self.centerPanel,
            1,
        )

        self.canvasLayout.addWidget(
            self.rightPanel,
            0,
        )

        ########################################################
        # ANALYTICS DASHBOARD
        #
        # Same parent/workspace geometry as mainArea.
        ########################################################

        self.analyticsDashboard = (
            AnalyticsDashboard(
                self.workspace
            )
        )

        self.analyticsDashboard.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.workspaceLayout.addWidget(
            self.analyticsDashboard,
            1,
        )

        self.analyticsDashboard.hide()

        ########################################################
        # ANALYTICS SHORTCUT
        ########################################################

        self.analyticsShortcut = QShortcut(
            QKeySequence(
                "Ctrl+Shift+A"
            ),
            self,
        )

        self.analyticsShortcut.activated.connect(
            self.handleAnalyticsShortcut
        )

        ########################################################
        # CONSOLE COMMAND
        ########################################################

        self.aiConsole.commandSubmitted.connect(
            self.handleCommand
        )

        ########################################################
        # REPLAY
        ########################################################

        if hasattr(
            self.aiConsole,
            "replayRequested",
        ):

            self.aiConsole.replayRequested.connect(
                self.replayResponse
            )

        ########################################################
        # INTERRUPT
        ########################################################

        if hasattr(
            self.aiConsole,
            "interruptRequested",
        ):

            self.aiConsole.interruptRequested.connect(
                self.interruptCurrentTask
            )

        ########################################################
        # DEFAULT STATE
        ########################################################

        self.setDormantState()

        ########################################################
        # START VOICE
        ########################################################

        self.voiceController.startListening()

    ############################################################
    # ANALYTICS COMMAND DETECTION
    ############################################################

    @staticmethod
    def isAnalyticsCommand(
        command,
    ):

        text = str(
            command or ""
        ).strip().lower()

        commands = {
            "open analytics",
            "show analytics",
            "open business analytics",
            "show business analytics",
            "business analytics",
            "analytics",
            "open analytics dashboard",
            "show analytics dashboard",
            "open business intelligence",
            "show business intelligence",
        }

        return text in commands

    ############################################################
    # COMMAND CENTER COMMAND DETECTION
    ############################################################

    @staticmethod
    def isCommandCenterCommand(
        command,
    ):

        text = str(
            command or ""
        ).strip().lower()

        commands = {
            "command center",
            "open command center",
            "show command center",
            "go to command center",
            "return to command center",
            "go back",
            "go back to main",
            "return to main",
            "main interface",
            "open main interface",
            "show main interface",
        }

        return text in commands

    ############################################################
    # ANALYTICS SHORTCUT
    ############################################################

    @Slot()
    def handleAnalyticsShortcut(
        self,
    ):

        if not self.interfaceActive:

            print(
                "[UI] Analytics shortcut ignored: "
                "JARVIS is dormant."
            )

            return

        if self.analyticsMode:

            self.showCommandCenter()

        else:

            self.showAnalytics()

    ############################################################
    # SHOW ANALYTICS
    ############################################################

    def showAnalytics(
        self,
    ):

        if not self.interfaceActive:

            print(
                "[UI] Analytics request ignored: "
                "JARVIS is dormant."
            )

            return

        if self.analyticsMode:

            return

        print(
            "[UI] ANALYTICS MODE"
        )

        self.analyticsMode = True

        ########################################################
        # HIDE MAIN HUD
        ########################################################

        self.mainArea.hide()

        ########################################################
        # SHOW ANALYTICS
        ########################################################

        self.analyticsDashboard.show()

        self.analyticsDashboard.raise_()

        ########################################################
        # DO NOT TOUCH:
        #
        # AIStatus
        # ArcReactor
        # AIConsole
        ########################################################

    ############################################################
    # SHOW COMMAND CENTER
    ############################################################

    def showCommandCenter(
        self,
    ):

        print(
            "[UI] COMMAND CENTER"
        )

        self.analyticsMode = False

        self.analyticsDashboard.hide()

        self.mainArea.show()

        self.mainArea.raise_()

    ############################################################
    # RUNTIME STATE
    ############################################################

    def updateRuntimeState(
        self,
    ):

        orchestrator = getattr(
            self.controller,
            "orchestrator",
            None,
        )

        if orchestrator is None:

            return

        try:

            snapshot = (
                orchestrator.task_snapshot()
            )

        except Exception as exc:

            print(
                "[UI] Runtime state snapshot warning:",
                exc,
            )

            return

        if snapshot is None:

            return

        try:

            state = (
                self.runtimeState.sync(
                    snapshot,
                    self._active_command_id,
                )
            )

        except Exception as exc:

            print(
                "[UI] Runtime state update warning:",
                exc,
            )

            return

        status = str(
            state.status or ""
        ).strip().upper()

        ########################################################
        # ACTIVE
        ########################################################

        if status in {
            "CREATED",
            "PLANNING",
            "READY",
            "RUNNING",
            "PAUSED",
        }:

            self.setExecutingState()

            progress = ""

            if state.total_steps:

                progress = (
                    f" "
                    f"{state.completed_steps}/"
                    f"{state.total_steps}"
                )

            self.aiConsole.setStatus(
                "EXECUTING"
                +
                progress
            )

            return

        ########################################################
        # COMPLETED
        ########################################################

        if status == "COMPLETED":

            self.setCompletedState()

            return

        ########################################################
        # FAILED
        ########################################################

        if status == "FAILED":

            self.setErrorState()

            return

        ########################################################
        # CANCELLED
        ########################################################

        if status == "CANCELLED":

            self.setCompletedState()

            return

    ############################################################
    # DORMANT
    ############################################################

    def setDormantState(
        self,
    ):

        self.interfaceActive = False

        self.analyticsMode = False

        self.topBar.hide()

        self.mainArea.hide()

        self.analyticsDashboard.hide()

        self.setReactorState(
            "DORMANT"
        )

    ############################################################
    # ACTIVATE
    ############################################################

    @Slot()
    def activateInterface(
        self,
    ):

        print(
            "[UI] JARVIS ACTIVATED"
        )

        self.interfaceActive = True

        self.topBar.show()

        self.showCommandCenter()

        self.setAIStatus(
            "LISTENING",
            "READY",
        )

        self.setReactorState(
            "LISTENING"
        )

        self.aiConsole.setStatus(
            "LISTENING"
        )

        self.aiConsole.focusInput()

    ############################################################
    # DEACTIVATE
    ############################################################

    @Slot()
    def deactivateInterface(
        self,
    ):

        print(
            "[UI] JARVIS DORMANT"
        )

        self.setDormantState()

    ############################################################
    # HANDLE TEXT COMMAND
    ############################################################

    @Slot(str)
    def handleCommand(
        self,
        command,
    ):

        command = str(
            command or ""
        ).strip()

        if not command:

            return

        ########################################################
        # DORMANT SAFETY
        ########################################################

        if not self.interfaceActive:

            print(
                "[UI] Ignoring text command while dormant:",
                command,
            )

            return

        ########################################################
        # ANALYTICS
        ########################################################

        if self.isAnalyticsCommand(
            command
        ):

            self.showAnalytics()

            return

        ########################################################
        # COMMAND CENTER
        ########################################################

        if self.isCommandCenterCommand(
            command
        ):

            self.showCommandCenter()

            return

        ########################################################
        # NORMAL AI COMMAND
        ########################################################

        self._command_counter += 1

        command_id = (
            self._command_counter
        )

        self._active_command_id = (
            command_id
        )

        thread = QThread()

        worker = CommandWorker(
            self.controller,
            command,
            command_id,
        )

        worker.moveToThread(
            thread
        )

        self.currentThread = thread

        self.currentWorker = worker

        ########################################################
        # CONNECTIONS
        ########################################################

        thread.started.connect(
            worker.run
        )

        worker.finished.connect(
            self.commandFinished
        )

        worker.error.connect(
            self.commandFailed
        )

        worker.finished.connect(
            thread.quit
        )

        worker.error.connect(
            thread.quit
        )

        thread.finished.connect(
            lambda cid=command_id,
            t=thread,
            w=worker:
                self.workerFinished(
                    cid,
                    t,
                    w,
                )
        )

        ########################################################
        # STATE
        ########################################################

        self.setThinkingState()

        self.setExecutingState()

        ########################################################
        # START
        ########################################################

        thread.start()

    ############################################################
    # HANDLE VOICE COMMAND
    ############################################################

    @Slot(str)
    def handleVoiceCommand(
        self,
        command,
    ):

        command = str(
            command or ""
        ).strip()

        if not command:

            return

        ########################################################
        # DORMANT SAFETY
        ########################################################

        if not self.interfaceActive:

            print(
                "[UI] Ignoring voice command while dormant:",
                command,
            )

            return

        ########################################################
        # ANALYTICS
        ########################################################

        if self.isAnalyticsCommand(
            command
        ):

            self.showAnalytics()

            return

        ########################################################
        # COMMAND CENTER
        ########################################################

        if self.isCommandCenterCommand(
            command
        ):

            self.showCommandCenter()

            return

        ########################################################
        # INTERRUPT
        ########################################################

        if self.isInterruptPhrase(
            command
        ):

            self.interruptCurrentTask(
                f"Voice interruption: {command}"
            )

            return

        ########################################################
        # NORMAL COMMAND
        ########################################################

        self.handleCommand(
            command
        )

    ############################################################
    # INTERRUPTION PHRASE
    ############################################################

    @staticmethod
    def isInterruptPhrase(
        command,
    ):

        text = str(
            command or ""
        ).strip().lower()

        phrases = {
            "stop",
            "stop jarvis",
            "jarvis stop",
            "cancel",
            "cancel this",
            "cancel that",
            "abort",
            "abort this",
            "wait",
            "wait jarvis",
            "hold on",
            "never mind",
            "nevermind",
            "don't do that",
            "do not do that",
            "stop this",
            "stop the task",
            "stop current task",
        }

        if text in phrases:

            return True

        return any(
            text.startswith(
                phrase + " "
            )
            for phrase in {
                "stop jarvis",
                "jarvis stop",
                "cancel this",
                "stop the task",
                "stop current task",
            }
        )

    ############################################################
    # INTERRUPT
    ############################################################

    @Slot()
    def interruptCurrentTask(
        self,
        reason="Task interrupted by user.",
    ):

        reason = str(
            reason
            or
            "Task interrupted by user."
        ).strip()

        print()

        print(
            "[UI] JARVIS INTERRUPT"
        )

        print(
            reason
        )

        ########################################################
        # MARK COMMAND STALE
        ########################################################

        interrupted_id = (
            self._active_command_id
        )

        if interrupted_id:

            self._interrupted_command_ids.add(
                interrupted_id
            )

        self._command_counter += 1

        self._active_command_id = (
            self._command_counter
        )

        ########################################################
        # STOP CONTROLLER
        ########################################################

        try:

            self.controller.interrupt(
                reason
            )

        except Exception as exc:

            print(
                "[UI] Controller interrupt error:",
                exc
            )

        ########################################################
        # VOICE
        ########################################################

        try:

            self.voiceController.commandFinished()

        except Exception:

            pass

        ########################################################
        # UI
        ########################################################

        self.setCompletedState()

        try:

            self.aiConsole.addSystemMessage(
                "Current task interrupted."
            )

            self.aiConsole.focusInput()

        except Exception:

            pass

    ############################################################
    # VOICE ERROR
    ############################################################

    @Slot(str)
    def voiceError(
        self,
        error,
    ):

        print(
            f"[Voice] {error}"
        )

        self.aiConsole.showError(
            f"Voice error: {error}"
        )

        self.setErrorState()

    ############################################################
    # COMMAND FINISHED
    ############################################################

    @Slot(int, str)
    def commandFinished(
        self,
        command_id,
        result,
    ):

        command_id = int(
            command_id
        )

        ########################################################
        # STALE RESULT
        ########################################################

        if (
            command_id
            !=
            self._active_command_id
            or
            command_id
            in
            self._interrupted_command_ids
        ):

            print(
                "[UI] Ignoring stale command result:",
                command_id
            )

            return

        if str(
            result or ""
        ).strip() == getattr(
            self.controller,
            "INTERRUPTED_RESULT",
            "__JARVIS_INTERRUPT__",
        ):

            return

        self.aiConsole.showResponse(
            result
        )

        self.setCompletedState()

        self.voiceController.commandFinished()

    ############################################################
    # COMMAND FAILED
    ############################################################

    @Slot(int, str)
    def commandFailed(
        self,
        command_id,
        error,
    ):

        command_id = int(
            command_id
        )

        if (
            command_id
            !=
            self._active_command_id
            or
            command_id
            in
            self._interrupted_command_ids
        ):

            print(
                "[UI] Ignoring stale command error:",
                command_id
            )

            return

        print(
            f"[JARVIS] {error}"
        )

        self.aiConsole.showError(
            f"Command failed: {error}"
        )

        self.setErrorState()

        self.voiceController.commandFinished()

    ############################################################
    # REPLAY
    ############################################################

    @Slot(str)
    def replayResponse(
        self,
        text,
    ):

        text = str(
            text or ""
        ).strip()

        if not text:

            return

        try:

            self.setAIStatus(
                "AI ONLINE",
                "REPLAYING",
            )

            self.setReactorState(
                "SPEAKING"
            )

            self.aiConsole.setStatus(
                "REPLAYING"
            )

            tts = getattr(
                self.controller,
                "tts",
                None
            )

            if tts is None:

                raise RuntimeError(
                    "JARVIS TTS engine is unavailable."
                )

            tts.speak(
                text
            )

            self.setCompletedState()

        except Exception as exc:

            print(
                "[UI] Replay error:",
                exc
            )

            self.setErrorState()

            self.aiConsole.showError(
                f"Replay failed: {exc}"
            )

    ############################################################
    # THREAD CLEANUP
    ############################################################

    @Slot(int, QThread, QObject)
    def workerFinished(
        self,
        command_id,
        thread,
        worker,
    ):

        command_id = int(
            command_id
        )

        try:

            worker.deleteLater()

        except Exception:

            pass

        try:

            thread.deleteLater()

        except Exception:

            pass

        ########################################################
        # ONLY CLEAR NEWEST WORKER
        ########################################################

        if (
            command_id
            ==
            self._active_command_id
        ):

            self.currentWorker = None

            self.currentThread = None

        ########################################################
        # CONTROL STALE ID GROWTH
        ########################################################

        if len(
            self._interrupted_command_ids
        ) > 32:

            self._interrupted_command_ids = set(
                sorted(
                    self._interrupted_command_ids
                )[-16:]
            )

    ############################################################
    # IDLE
    ############################################################

    def setIdleState(
        self,
    ):

        self.setAIStatus(
            "AI ONLINE",
            "IDLE",
        )

        self.setReactorState(
            "IDLE"
        )

        self.aiConsole.setStatus(
            "IDLE"
        )

    ############################################################
    # LISTENING
    ############################################################

    def setListeningState(
        self,
    ):

        self.setAIStatus(
            "LISTENING",
            "READY",
        )

        self.setReactorState(
            "LISTENING"
        )

        self.aiConsole.setStatus(
            "LISTENING"
        )

    ############################################################
    # THINKING
    ############################################################

    def setThinkingState(
        self,
    ):

        self.setAIStatus(
            "PROCESSING",
            "THINKING",
        )

        self.setReactorState(
            "THINKING"
        )

        self.aiConsole.setStatus(
            "THINKING"
        )

    ############################################################
    # EXECUTING
    ############################################################

    def setExecutingState(
        self,
    ):

        self.setAIStatus(
            "EXECUTING",
            "EXECUTING",
        )

        self.setReactorState(
            "EXECUTING"
        )

        self.aiConsole.setStatus(
            "EXECUTING"
        )

    ############################################################
    # COMPLETED
    ############################################################

    def setCompletedState(
        self,
    ):

        self.setAIStatus(
            "AI ONLINE",
            "READY",
        )

        self.setReactorState(
            "COMPLETED"
        )

        self.aiConsole.setStatus(
            "COMPLETE"
        )

    ############################################################
    # ERROR
    ############################################################

    def setErrorState(
        self,
    ):

        self.setAIStatus(
            "AI ONLINE",
            "ERROR",
        )

        self.setReactorState(
            "ERROR"
        )

        self.aiConsole.setStatus(
            "ERROR"
        )

    ############################################################
    # AI STATUS
    ############################################################

    def setAIStatus(
        self,
        status,
        mode,
    ):

        if hasattr(
            self.aiStatus,
            "status",
        ):

            self.aiStatus.status.setText(
                str(status)
            )

        if hasattr(
            self.aiStatus,
            "mode",
        ):

            self.aiStatus.mode.setText(
                str(mode)
            )

    ############################################################
    # REACTOR STATE
    ############################################################

    def setReactorState(
        self,
        state,
    ):

        if not hasattr(
            self.reactor,
            "setState",
        ):

            return

        try:

            self.reactor.setState(
                state
            )

        except Exception as exc:

            print(
                f"[Reactor] State update failed: {exc}"
            )