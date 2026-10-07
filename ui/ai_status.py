from enum import Enum, auto

from PySide6.QtCore import (
    Qt,
    QTimer,
)

from PySide6.QtGui import (
    QFont,
)

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
)


############################################################
# AI STATE
############################################################

class AIState(Enum):

    IDLE = auto()

    LISTENING = auto()

    THINKING = auto()

    EXECUTING = auto()

    COMPLETED = auto()

    ERROR = auto()


############################################################
# AI STATUS
############################################################

class AIStatus(QWidget):

    def __init__(self):

        super().__init__()

        ####################################################
        # SIZE
        ####################################################

        self.setFixedHeight(
            118
        )

        self.setMinimumWidth(
            420
        )

        ####################################################
        # ROOT
        ####################################################

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            4,
            0,
            4,
        )

        layout.setAlignment(
            Qt.AlignCenter
        )

        layout.setSpacing(
            2
        )

        ####################################################
        # TITLE
        ####################################################

        self.title = QLabel(
            "J A R V I S"
        )

        self.title.setObjectName(
            "AIStatusTitle"
        )

        self.title.setAlignment(
            Qt.AlignCenter
        )

        ####################################################
        # STATUS
        #
        # IMPORTANT:
        # MainWindow accesses this directly.
        ####################################################

        self.status = QLabel(
            "AI ONLINE"
        )

        self.status.setObjectName(
            "AIStatusMain"
        )

        self.status.setAlignment(
            Qt.AlignCenter
        )

        ####################################################
        # MODE
        #
        # IMPORTANT:
        # MainWindow accesses this directly.
        ####################################################

        self.mode = QLabel(
            "IDLE"
        )

        self.mode.setObjectName(
            "AIStatusMode"
        )

        self.mode.setAlignment(
            Qt.AlignCenter
        )

        ####################################################
        # ACTIVITY INDICATOR
        ####################################################

        indicatorLayout = QHBoxLayout()

        indicatorLayout.setAlignment(
            Qt.AlignCenter
        )

        indicatorLayout.setSpacing(
            5
        )

        self.indicator = QLabel(
            "●"
        )

        self.indicator.setObjectName(
            "AIStatusIndicator"
        )

        self.indicatorText = QLabel(
            "SYSTEM READY"
        )

        self.indicatorText.setObjectName(
            "AIStatusIndicatorText"
        )

        indicatorLayout.addWidget(
            self.indicator
        )

        indicatorLayout.addWidget(
            self.indicatorText
        )

        ####################################################
        # LAYOUT
        ####################################################

        layout.addWidget(
            self.title
        )

        layout.addWidget(
            self.status
        )

        layout.addWidget(
            self.mode
        )

        layout.addLayout(
            indicatorLayout
        )

        ####################################################
        # SCAN ANIMATION
        ####################################################

        self.scanVisible = True

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.animateIndicator
        )

        self.timer.start(
            700
        )

        ####################################################
        # INITIAL STATE
        ####################################################

        self.setState(
            AIState.IDLE
        )

    ########################################################
    # INDICATOR ANIMATION
    ########################################################

    def animateIndicator(
        self
    ):

        self.scanVisible = (
            not self.scanVisible
        )

        if self.scanVisible:

            self.indicator.show()

        else:

            self.indicator.hide()

    ########################################################
    # SET STATE
    ########################################################

    def setState(
        self,
        state: AIState,
    ):

        ####################################################
        # IDLE
        ####################################################

        if state == AIState.IDLE:

            self.status.setText(
                "AI ONLINE"
            )

            self.mode.setText(
                "IDLE"
            )

            self.indicatorText.setText(
                "SYSTEM READY"
            )

        ####################################################
        # LISTENING
        ####################################################

        elif state == AIState.LISTENING:

            self.status.setText(
                "LISTENING"
            )

            self.mode.setText(
                "VOICE INPUT ACTIVE"
            )

            self.indicatorText.setText(
                "VOICE CHANNEL OPEN"
            )

        ####################################################
        # THINKING
        ####################################################

        elif state == AIState.THINKING:

            self.status.setText(
                "PROCESSING"
            )

            self.mode.setText(
                "ANALYZING COMMAND"
            )

            self.indicatorText.setText(
                "NEURAL PROCESSING"
            )

        ####################################################
        # EXECUTING
        ####################################################

        elif state == AIState.EXECUTING:

            self.status.setText(
                "EXECUTING"
            )

            self.mode.setText(
                "RUNNING TASK"
            )

            self.indicatorText.setText(
                "AUTOMATION ACTIVE"
            )

        ####################################################
        # COMPLETED
        ####################################################

        elif state == AIState.COMPLETED:

            self.status.setText(
                "COMPLETE"
            )

            self.mode.setText(
                "TASK FINISHED"
            )

            self.indicatorText.setText(
                "SYSTEM STABLE"
            )

        ####################################################
        # ERROR
        ####################################################

        elif state == AIState.ERROR:

            self.status.setText(
                "ERROR"
            )

            self.mode.setText(
                "EXECUTION FAILED"
            )

            self.indicatorText.setText(
                "ATTENTION REQUIRED"
            )