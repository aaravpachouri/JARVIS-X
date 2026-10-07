from PySide6.QtCore import (
    QObject,
    Signal,
)

from core.state import JarvisState


class JarvisController(QObject):

    ##################################################
    # GLOBAL SIGNALS
    ##################################################

    stateChanged = Signal(object)

    commandChanged = Signal(str)

    responseChanged = Signal(str)

    notificationChanged = Signal(str)

    automationStarted = Signal(str)

    automationFinished = Signal(str)

    ##################################################

    def __init__(self):

        super().__init__()

        ##################################################
        # STATE
        ##################################################

        self._state = JarvisState.STARTING

        ##################################################
        # DATA
        ##################################################

        self._command = ""

        self._response = ""

        self._notification = ""

    ##################################################
    # GETTERS
    ##################################################

    @property
    def state(self):

        return self._state

    @property
    def command(self):

        return self._command

    @property
    def response(self):

        return self._response

    ##################################################
    # STATE
    ##################################################

    def setState(self, state):

        if state == self._state:

            return

        self._state = state

        self.stateChanged.emit(state)

    ##################################################
    # COMMAND
    ##################################################

    def setCommand(self, command):

        self._command = command

        self.commandChanged.emit(command)

    ##################################################
    # RESPONSE
    ##################################################

    def setResponse(self, response):

        self._response = response

        self.responseChanged.emit(response)

    ##################################################
    # NOTIFICATION
    ##################################################

    def notify(self, text):

        self._notification = text

        self.notificationChanged.emit(text)

    ##################################################
    # AUTOMATION
    ##################################################

    def automationBegin(self, task):

        self.automationStarted.emit(task)

    ##################################################

    def automationEnd(self, task):

        self.automationFinished.emit(task)