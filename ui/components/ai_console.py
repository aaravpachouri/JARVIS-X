from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QApplication,
    QFrame,
)

from PySide6.QtCore import (
    Qt,
    QTimer,
    Signal,
)

from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QFont,
)


class AIConsole(QWidget):

    """
    JARVIS X
    UNIVERSAL CHAT CONSOLE

    This widget is the persistent conversational interface.

    Responsibilities:

        - display the complete conversation
        - preserve long AI responses
        - render Markdown as rich text
        - keep user and JARVIS messages separate
        - provide Copy for AI responses
        - provide Replay for AI responses
        - emit replayRequested so the existing TTS system can
          replay the exact complete response
        - keep the conversation scrollable

    IMPORTANT:

    The original AI response is preserved.

    Markdown is rendered by the UI.

    TTS cleanup happens inside TTSEngine and is NOT performed
    here.

    This prevents the UI and voice layers from corrupting one
    another.
    """

    ############################################################
    # SIGNALS
    ############################################################

    commandSubmitted = Signal(str)

    replayRequested = Signal(str)

    interruptRequested = Signal()

    ############################################################
    # INITIALIZATION
    ############################################################

    def __init__(self):

        super().__init__()

        self.setFixedWidth(340)

        ########################################################
        # RESPONSE HISTORY
        ########################################################

        self.messageHistory = []

        ########################################################
        # ANIMATION
        ########################################################

        self.scanY = -80

        self.glow = 60

        self.direction = 1

        ########################################################
        # MAIN LAYOUT
        ########################################################

        self.layout = QVBoxLayout(self)

        self.layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        self.layout.setSpacing(10)

        ########################################################
        # HUD HEADER
        ########################################################

        headerRow = QHBoxLayout()

        headerRow.setContentsMargins(
            0,
            0,
            0,
            0
        )

        headerRow.setSpacing(
            6
        )

        title = QLabel(
            "AI CORE"
        )

        titleFont = QFont()

        titleFont.setPointSize(
            15
        )

        titleFont.setBold(
            True
        )

        title.setFont(
            titleFont
        )

        title.setStyleSheet(
            """
            color:#8BE9FD;
            background:transparent;
            """
        )

        headerRow.addWidget(
            title
        )

        headerRow.addStretch()

        self.liveIndicator = QLabel(
            "● LIVE"
        )

        self.liveIndicator.setStyleSheet(
            """
            color:#4DEBFF;
            font-size:9px;
            font-weight:bold;
            background:transparent;
            """
        )

        headerRow.addWidget(
            self.liveIndicator
        )

        self.layout.addLayout(
            headerRow
        )

        ########################################################
        # HEADER LINE
        ########################################################

        self.headerLine = QFrame()

        self.headerLine.setFixedHeight(
            1
        )

        self.headerLine.setStyleSheet(
            """
            background:rgba(54,223,255,120);
            border:none;
            """
        )

        self.layout.addWidget(
            self.headerLine
        )

        ########################################################
        # CORE META
        ########################################################

        metaRow = QHBoxLayout()

        metaRow.setContentsMargins(
            0,
            2,
            0,
            2
        )

        metaRow.setSpacing(
            5
        )

        self.metaTitle = QLabel(
            "NEURAL NETWORK"
        )

        self.metaTitle.setStyleSheet(
            """
            color:#36DFFF;
            font-size:9px;
            font-weight:bold;
            background:transparent;
            """
        )

        metaRow.addWidget(
            self.metaTitle
        )

        metaRow.addStretch()

        self.voiceReady = QLabel(
            "VOICE READY"
        )

        self.voiceReady.setStyleSheet(
            """
            color:rgba(139,233,253,190);
            font-size:8px;
            background:transparent;
            """
        )

        metaRow.addWidget(
            self.voiceReady
        )

        self.layout.addLayout(
            metaRow
        )

        ########################################################
        # STATUS
        ########################################################

        self.status = QLabel()

        self.status.setStyleSheet(
            """
            color:white;
            font-size:11px;
            font-weight:bold;
            background:transparent;
            """
        )

        self.layout.addWidget(
            self.status
        )

        ########################################################
        # STATUS SEPARATOR
        ########################################################

        statusLine = QFrame()

        statusLine.setFixedHeight(
            1
        )

        statusLine.setStyleSheet(
            """
            background:rgba(54,223,255,70);
            border:none;
            """
        )

        self.layout.addWidget(
            statusLine
        )

        ########################################################
        # CONVERSATION AREA
        ########################################################

        self.historyScroll = QScrollArea()

        self.historyScroll.setWidgetResizable(
            True
        )

        self.historyScroll.setFrameShape(
            QScrollArea.NoFrame
        )

        self.historyScroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.historyScroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 5px;
            }

            QScrollBar::handle:vertical {
                background: rgba(54,223,255,100);
                border-radius: 2px;
                min-height: 25px;
            }

            QScrollBar::handle:vertical:hover {
                background: rgba(54,223,255,180);
            }
            """
        )

        ########################################################
        # HISTORY CONTAINER
        ########################################################

        self.historyWidget = QWidget()

        self.historyWidget.setStyleSheet(
            "background: transparent;"
        )

        self.historyLayout = QVBoxLayout(
            self.historyWidget
        )

        self.historyLayout.setContentsMargins(
            0,
            8,
            0,
            8
        )

        self.historyLayout.setSpacing(
            9
        )

        self.historyLayout.addStretch()

        self.historyScroll.setWidget(
            self.historyWidget
        )

        self.layout.addWidget(
            self.historyScroll,
            1
        )

        ########################################################
        # INITIAL MESSAGE
        ########################################################

        self.addSystemMessage(
            "JARVIS ONLINE. Awaiting command."
        )

        ########################################################
        # COMMAND SECTION
        ########################################################

        commandHeader = QHBoxLayout()

        commandHeader.setContentsMargins(
            0,
            0,
            0,
            0
        )

        commandLabel = QLabel(
            "COMMAND"
        )

        commandLabel.setStyleSheet(
            """
            color:#36DFFF;
            font-size:10px;
            font-weight:bold;
            background:transparent;
            """
        )

        commandHeader.addWidget(
            commandLabel
        )

        commandHeader.addStretch()

        self.commandHint = QLabel(
            "ENTER"
        )

        self.commandHint.setStyleSheet(
            """
            color:rgba(139,233,253,150);
            font-size:8px;
            background:transparent;
            """
        )

        commandHeader.addWidget(
            self.commandHint
        )

        self.layout.addLayout(
            commandHeader
        )

        commandLine = QFrame()

        commandLine.setFixedHeight(
            1
        )

        commandLine.setStyleSheet(
            """
            background:rgba(54,223,255,80);
            border:none;
            """
        )

        self.layout.addWidget(
            commandLine
        )

        ########################################################
        # INPUT ROW
        ########################################################

        inputRow = QHBoxLayout()

        inputRow.setSpacing(
            6
        )

        ########################################################
        # INPUT
        ########################################################

        self.input = QLineEdit()

        self.input.setPlaceholderText(
            "Ask JARVIS..."
        )

        self.input.setFixedHeight(
            38
        )

        self.input.setStyleSheet(
            """
            QLineEdit {
                background: rgba(5,20,32,220);
                color: white;
                border: 1px solid rgba(54,223,255,120);
                border-radius: 6px;
                padding-left: 10px;
                padding-right: 10px;
                font-size: 12px;
            }

            QLineEdit:focus {
                border: 1px solid rgba(54,223,255,230);
                background: rgba(8,28,42,240);
            }
            """
        )

        self.input.returnPressed.connect(
            self.submitCommand
        )

        inputRow.addWidget(
            self.input,
            1
        )

        ########################################################
        # SEND BUTTON
        ########################################################

        self.sendButton = QPushButton(
            "▶"
        )

        self.sendButton.setFixedSize(
            38,
            38
        )

        self.sendButton.setCursor(
            Qt.PointingHandCursor
        )

        self.sendButton.setStyleSheet(
            """
            QPushButton {
                background: rgba(0,180,220,80);
                color: #BFFFFF;
                border: 1px solid rgba(54,223,255,160);
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: rgba(0,210,255,140);
                border: 1px solid rgba(120,245,255,230);
            }

            QPushButton:pressed {
                background: rgba(0,150,190,180);
            }
            """
        )

        self.sendButton.clicked.connect(
            self.submitCommand
        )


        inputRow.addWidget(
            self.sendButton
        )

        ########################################################
        # INTERRUPT BUTTON
        ########################################################

        self.stopButton = QPushButton(
            "STOP"
        )

        self.stopButton.setFixedHeight(
            38
        )

        self.stopButton.setMinimumWidth(
            56
        )

        self.stopButton.setCursor(
            Qt.PointingHandCursor
        )

        self.stopButton.setEnabled(
            False
        )

        self.stopButton.setToolTip(
            "Interrupt the current JARVIS task"
        )

        self.stopButton.setStyleSheet(
            '''
            QPushButton {
                background: rgba(180,50,60,70);
                color: #FFD9DC;
                border: 1px solid rgba(255,100,115,150);
                border-radius: 6px;
                font-size: 9px;
                font-weight: bold;
                padding-left: 8px;
                padding-right: 8px;
            }

            QPushButton:hover:enabled {
                background: rgba(220,70,80,130);
                color: white;
                border: 1px solid rgba(255,140,150,230);
            }

            QPushButton:pressed:enabled {
                background: rgba(150,35,45,180);
            }

            QPushButton:disabled {
                background: rgba(70,40,45,40);
                color: rgba(255,180,185,90);
                border: 1px solid rgba(255,100,115,45);
            }
            '''
        )

        self.stopButton.clicked.connect(
            self.requestInterrupt
        )

        inputRow.addWidget(
            self.stopButton
        )

        self.layout.addLayout(
            inputRow
        )

        ########################################################
        # FOOTER
        ########################################################

        self.info = QLabel(
            "VOICE ACTIVE  •  ENTER SENDS  •  STOP INTERRUPTS"
        )

        self.info.setAlignment(
            Qt.AlignCenter
        )

        self.info.setStyleSheet(
            """
            color:rgba(77,235,255,150);
            font-size:8px;
            background:transparent;
            """
        )

        self.layout.addWidget(
            self.info
        )

        ########################################################
        # FOOTER LINE
        ########################################################

        footerLine = QFrame()

        footerLine.setFixedHeight(
            1
        )

        footerLine.setStyleSheet(
            """
            background:rgba(54,223,255,80);
            border:none;
            """
        )

        self.layout.addWidget(
            footerLine
        )

        ########################################################
        # TIMER
        ########################################################

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.animate
        )

        self.timer.start(
            40
        )

        self.setStatus(
            "IDLE"
        )

    ############################################################
    # SUBMIT COMMAND
    ############################################################

    def submitCommand(
        self
    ):

        command = (
            self.input.text().strip()
        )

        if not command:
            return

        ########################################################
        # SHOW USER COMMAND
        ########################################################

        self.addUserMessage(
            command
        )

        ########################################################
        # CLEAR INPUT
        ########################################################

        self.input.clear()

        ########################################################
        # UPDATE STATUS
        ########################################################

        self.setStatus(
            "THINKING"
        )

        ########################################################
        # SEND TO MAIN WINDOW / CONTROLLER
        ########################################################

        self.commandSubmitted.emit(
            command
        )

    ############################################################
    # USER MESSAGE
    ############################################################

    def addUserMessage(
        self,
        text
    ):

        text = str(
            text or ""
        )

        label = QLabel(
            f"<b style='color:#36DFFF;'>YOU</b><br>"
            f"<span style='color:white;'>"
            f"{self.escape(text)}"
            f"</span>"
        )

        label.setWordWrap(
            True
        )

        label.setTextFormat(
            Qt.RichText
        )

        label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum
        )

        label.setStyleSheet(
            """
            QLabel {
                background: rgba(0,90,120,55);
                border-left: 2px solid #36DFFF;
                padding: 8px;
                color: white;
                font-size: 11px;
            }
            """
        )

        self.insertMessage(
            label
        )

        self.messageHistory.append(
            {
                "role": "user",
                "text": text,
                "widget": label,
            }
        )

    ############################################################
    # JARVIS MESSAGE
    ############################################################

    def addAIMessage(
        self,
        text
    ):

        text = str(
            text or ""
        )

        ########################################################
        # OUTER MESSAGE FRAME
        ########################################################

        messageFrame = QFrame()

        messageFrame.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum
        )

        messageFrame.setStyleSheet(
            """
            QFrame {
                background: rgba(0,35,55,70);
                border-left: 2px solid #8BE9FD;
            }
            """
        )

        messageLayout = QVBoxLayout(
            messageFrame
        )

        messageLayout.setContentsMargins(
            8,
            8,
            8,
            6
        )

        messageLayout.setSpacing(
            6
        )

        ########################################################
        # HEADER
        ########################################################

        header = QLabel(
            "JARVIS"
        )

        header.setStyleSheet(
            """
            QLabel {
                color:#8BE9FD;
                font-size:11px;
                font-weight:bold;
                background:transparent;
                border:none;
            }
            """
        )

        messageLayout.addWidget(
            header
        )

        ########################################################
        # RESPONSE VIEW
        #
        # QTextBrowser gives us:
        #
        # - rich Markdown
        # - selectable text
        # - internal scrolling for long responses
        # - links
        # - much better long-response behavior than QLabel
        ########################################################

        responseView = QTextBrowser()

        responseView.setOpenExternalLinks(
            True
        )

        responseView.setReadOnly(
            True
        )

        responseView.setFrameShape(
            QFrame.NoFrame
        )

        responseView.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        responseView.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        responseView.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum
        )

        responseView.setStyleSheet(
            """
            QTextBrowser {
                background: transparent;
                border: none;
                color: white;
                font-size: 11px;
                padding: 0px;
                selection-background-color: rgba(54,223,255,100);
                selection-color: white;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 4px;
            }

            QScrollBar::handle:vertical {
                background: rgba(54,223,255,100);
                border-radius: 2px;
                min-height: 18px;
            }
            """
        )

        ########################################################
        # MARKDOWN
        ########################################################

        try:

            responseView.setMarkdown(
                text
            )

        except Exception:

            responseView.setPlainText(
                text
            )

        ########################################################
        # Give the document enough room for the full response.
        #
        # The outer conversation remains scrollable, while each
        # response can still be selected/copied.
        ########################################################

        document = (
            responseView.document()
        )

        document.setDocumentMargin(
            0
        )

        responseView.setMinimumHeight(
            40
        )

        self._resizeResponseView(
            responseView
        )

        messageLayout.addWidget(
            responseView
        )

        ########################################################
        # ACTION BUTTONS
        ########################################################

        buttonRow = QHBoxLayout()

        buttonRow.setContentsMargins(
            0,
            2,
            0,
            0
        )

        buttonRow.setSpacing(
            5
        )

        ########################################################
        # COPY
        ########################################################

        copyButton = QPushButton(
            "COPY"
        )

        copyButton.setFixedHeight(
            25
        )

        copyButton.setCursor(
            Qt.PointingHandCursor
        )

        copyButton.setStyleSheet(
            self._messageButtonStyle()
        )

        copyButton.clicked.connect(
            lambda _=False,
            value=text:
                self.copyResponse(
                    value
                )
        )

        buttonRow.addWidget(
            copyButton
        )

        ########################################################
        # REPLAY
        ########################################################

        replayButton = QPushButton(
            "REPLAY"
        )

        replayButton.setFixedHeight(
            25
        )

        replayButton.setCursor(
            Qt.PointingHandCursor
        )

        replayButton.setStyleSheet(
            self._messageButtonStyle()
        )

        replayButton.clicked.connect(
            lambda _=False,
            value=text:
                self.replayResponse(
                    value
                )
        )

        buttonRow.addWidget(
            replayButton
        )

        buttonRow.addStretch()

        messageLayout.addLayout(
            buttonRow
        )

        ########################################################
        # INSERT
        ########################################################

        self.insertMessage(
            messageFrame
        )

        ########################################################
        # HISTORY
        ########################################################

        self.messageHistory.append(
            {
                "role": "assistant",
                "text": text,
                "widget": messageFrame,
                "responseView": responseView,
                "copyButton": copyButton,
                "replayButton": replayButton,
            }
        )

        ########################################################
        # Recalculate after Qt lays out the document.
        ########################################################

        QTimer.singleShot(
            0,
            lambda view=responseView:
                self._resizeResponseView(
                    view
                )
        )

        QTimer.singleShot(
            80,
            self.scrollToBottom
        )

        return messageFrame

    ############################################################
    # SYSTEM MESSAGE
    ############################################################

    def addSystemMessage(
        self,
        text
    ):

        text = str(
            text or ""
        )

        label = QLabel(
            f"<span style='color:#36DFFF;'>SYSTEM</span><br>"
            f"<span style='color:#B7FFFF;'>"
            f"{self.escape(text)}"
            f"</span>"
        )

        label.setWordWrap(
            True
        )

        label.setTextFormat(
            Qt.RichText
        )

        label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum
        )

        label.setStyleSheet(
            """
            QLabel {
                padding: 6px;
                color: white;
                font-size: 10px;
            }
            """
        )

        self.insertMessage(
            label
        )

        self.messageHistory.append(
            {
                "role": "system",
                "text": text,
                "widget": label,
            }
        )

    ############################################################
    # INSERT MESSAGE
    ############################################################

    def insertMessage(
        self,
        widget
    ):

        self.historyLayout.insertWidget(
            self.historyLayout.count() - 1,
            widget
        )

        QTimer.singleShot(
            50,
            self.scrollToBottom
        )

    ############################################################
    # RESPONSE VIEW HEIGHT
    ############################################################

    def _resizeResponseView(
        self,
        view
    ):

        if view is None:
            return

        try:

            document = (
                view.document()
            )

            height = int(
                document.size().height()
            )

            ####################################################
            # Small padding so the final line never gets clipped.
            ####################################################

            height += 18

            ####################################################
            # Prevent an extremely long response from creating
            # an enormous widget. Long responses get an internal
            # scroll area while the conversation itself remains
            # accessible.
            ####################################################

            height = max(
                45,
                min(
                    height,
                    460
                )
            )

            view.setFixedHeight(
                height
            )

        except Exception:

            view.setMinimumHeight(
                45
            )

    ############################################################
    # INTERRUPT REQUEST
    ############################################################

    def requestInterrupt(
        self
    ):

        if hasattr(
            self,
            "stopButton"
        ):

            self.stopButton.setEnabled(
                False
            )

        self.setStatus(
            "INTERRUPTING"
        )

        self.interruptRequested.emit()

    ############################################################
    # COPY RESPONSE
    ############################################################

    def copyResponse(
        self,
        text
    ):

        text = str(
            text or ""
        )

        if not text:
            return

        try:

            QApplication.clipboard().setText(
                text
            )

            self.setStatus(
                "COPIED"
            )

            QTimer.singleShot(
                1200,
                lambda:
                    self.setStatus(
                        "COMPLETED"
                    )
            )

        except Exception as exc:

            print(
                "[AIConsole] "
                f"Copy error: {exc}"
            )

    ############################################################
    # REPLAY RESPONSE
    ############################################################

    def replayResponse(
        self,
        text
    ):

        text = str(
            text or ""
        ).strip()

        if not text:
            return

        self.setStatus(
            "REPLAYING"
        )

        ########################################################
        # The main application should connect this signal to its
        # EXISTING TTSEngine.
        #
        # We deliberately do not instantiate another TTSEngine
        # here because that would load another Kokoro model.
        ########################################################

        self.replayRequested.emit(
            text
        )

    ############################################################
    # SHOW RESPONSE
    ############################################################

    def showResponse(
        self,
        text
    ):

        self.addAIMessage(
            text
        )

        self.setStatus(
            "COMPLETED"
        )

    ############################################################
    # ERROR
    ############################################################

    def showError(
        self,
        text
    ):

        self.addAIMessage(
            text
        )

        self.setStatus(
            "ERROR"
        )

    ############################################################
    # FOCUS
    ############################################################

    def focusInput(
        self
    ):

        self.input.setFocus()

    ############################################################
    # SCROLL
    ############################################################

    def scrollToBottom(
        self
    ):

        scrollbar = (
            self.historyScroll.verticalScrollBar()
        )

        scrollbar.setValue(
            scrollbar.maximum()
        )

    ############################################################
    # SCROLL TO MESSAGE
    ############################################################

    def scrollToMessage(
        self,
        index
    ):

        if (
            index < 0
            or
            index >= len(
                self.messageHistory
            )
        ):

            return

        item = self.messageHistory[
            index
        ]

        widget = item.get(
            "widget"
        )

        if widget is None:
            return

        self.historyScroll.ensureWidgetVisible(
            widget,
            0,
            20
        )

    ############################################################
    # GET HISTORY
    ############################################################

    def getHistory(
        self
    ):

        return [
            {
                "role":
                    item.get(
                        "role"
                    ),

                "text":
                    item.get(
                        "text"
                    ),
            }

            for item in self.messageHistory
        ]

    ############################################################
    # CLEAR HISTORY
    ############################################################

    def clearHistory(
        self
    ):

        while (
            self.historyLayout.count()
            > 1
        ):

            item = (
                self.historyLayout.takeAt(
                    0
                )
            )

            widget = (
                item.widget()
            )

            if widget is not None:

                widget.deleteLater()

        self.messageHistory.clear()

        self.addSystemMessage(
            "JARVIS ONLINE. Awaiting command."
        )

        self.setStatus(
            "IDLE"
        )

    ############################################################
    # STATUS
    ############################################################

    def setStatus(
        self,
        status
    ):

        status = str(
            status or "IDLE"
        ).upper()

        self.status.setText(
            f"● {status}"
        )

        self.status.setStyleSheet(
            """
            QLabel {
                color:#4DEBFF;
                font-size:11px;
                font-weight:bold;
                background:transparent;
            }
            """
        )

        if hasattr(
            self,
            "liveIndicator"
        ):

            self.liveIndicator.setText(
                "● LIVE"
                if status not in {
                    "ERROR",
                    "INTERRUPTING"
                }
                else
                "● HOLD"
            )

        if hasattr(
            self,
            "voiceReady"
        ):

            if status in {
                "THINKING",
                "EXECUTING",
                "REPLAYING",
                "INTERRUPTING"
            }:

                self.voiceReady.setText(
                    "VOICE BUSY"
                )

            elif status == "ERROR":

                self.voiceReady.setText(
                    "VOICE ALERT"
                )

            else:

                self.voiceReady.setText(
                    "VOICE READY"
                )

        ########################################################
        # STOP BUTTON STATE
        ########################################################

        if hasattr(
            self,
            "stopButton"
        ):

            active = status in {
                "THINKING",
                "EXECUTING",
                "REPLAYING",
                "INTERRUPTING",
            }

            self.stopButton.setEnabled(
                active
            )

    ############################################################
    # MESSAGE BUTTON STYLE
    ############################################################

    @staticmethod
    def _messageButtonStyle():

        return """
        QPushButton {
            background: rgba(0,180,220,45);
            color: rgba(190,250,255,220);
            border: 1px solid rgba(54,223,255,90);
            border-radius: 4px;
            padding-left: 8px;
            padding-right: 8px;
            font-size: 8px;
            font-weight: bold;
        }

        QPushButton:hover {
            background: rgba(0,210,255,100);
            color: white;
            border: 1px solid rgba(120,245,255,190);
        }

        QPushButton:pressed {
            background: rgba(0,150,190,140);
        }
        """

    ############################################################
    # ESCAPE HTML
    ############################################################

    @staticmethod
    def escape(
        text
    ):

        return (
            str(text)
            .replace(
                "&",
                "&amp;"
            )
            .replace(
                "<",
                "&lt;"
            )
            .replace(
                ">",
                "&gt;"
            )
        )

    ############################################################
    # ANIMATION
    ############################################################

    def animate(
        self
    ):

        self.scanY += 2

        if (
            self.scanY
            >
            self.height() + 40
        ):

            self.scanY = -40

        self.glow += (
            self.direction * 4
        )

        if self.glow > 255:

            self.glow = 255

            self.direction = -1

        elif self.glow < 70:

            self.glow = 70

            self.direction = 1

        self.update()

    ############################################################
    # PAINT
    ############################################################

    def paintEvent(
        self,
        event
    ):

        super().paintEvent(
            event
        )

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        w = self.width() - 1

        h = self.height() - 1

        corner = 30

        ########################################################
        # DARK PANEL BODY
        ########################################################

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QColor(
                3,
                10,
                19,
                110
            )
        )

        painter.drawRect(
            self.rect()
        )

        ########################################################
        # CORNER / BRACKET GLOW
        ########################################################

        painter.setPen(
            QPen(
                QColor(
                    0,
                    220,
                    255,
                    45
                ),
                5
            )
        )

        corners = [
            (
                (0, 0),
                (corner, 0)
            ),
            (
                (0, 0),
                (0, corner)
            ),
            (
                (w, 0),
                (w - corner, 0)
            ),
            (
                (w, 0),
                (w, corner)
            ),
            (
                (0, h),
                (corner, h)
            ),
            (
                (0, h),
                (0, h - corner)
            ),
            (
                (w, h),
                (w - corner, h)
            ),
            (
                (w, h),
                (w, h - corner)
            ),
        ]

        for p1, p2 in corners:

            painter.drawLine(
                p1[0],
                p1[1],
                p2[0],
                p2[1]
            )

        ########################################################
        # MAIN BRACKET LINES
        ########################################################

        painter.setPen(
            QPen(
                QColor(
                    0,
                    220,
                    255,
                    190
                ),
                2
            )
        )

        for p1, p2 in corners:

            painter.drawLine(
                p1[0],
                p1[1],
                p2[0],
                p2[1]
            )

        ########################################################
        # TOP HEADER ACCENT
        ########################################################

        painter.setPen(
            QPen(
                QColor(
                    0,
                    220,
                    255,
                    90
                ),
                1
            )
        )

        painter.drawLine(
            22,
            60,
            w - 22,
            60
        )

        ########################################################
        # LOWER ACCENT
        ########################################################

        painter.drawLine(
            22,
            h - 54,
            w - 22,
            h - 54
        )

        ########################################################
        # SUBTLE SCAN LINE
        ########################################################

        painter.setPen(
            QPen(
                QColor(
                    0,
                    220,
                    255,
                    22
                ),
                1
            )
        )

        painter.drawLine(
            18,
            self.scanY,
            w - 18,
            self.scanY
        )

        painter.end()