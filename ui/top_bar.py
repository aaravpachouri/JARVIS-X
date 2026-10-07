from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
)

from PySide6.QtCore import (
    Qt,
    QTimer,
)

from backend.system_monitor import (
    SystemMonitor,
)


############################################################
# INFO BOX
############################################################

class InfoBox(QFrame):

    def __init__(
        self,
        title,
    ):

        super().__init__()

        self.setObjectName(
            "InfoBox"
        )

        self.setFixedWidth(
            62
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            6,
            2,
            6,
            2,
        )

        layout.setSpacing(
            0
        )

        ####################################################
        # TITLE
        ####################################################

        self.title = QLabel(
            title
        )

        self.title.setObjectName(
            "InfoTitle"
        )

        self.title.setAlignment(
            Qt.AlignCenter
        )

        ####################################################
        # VALUE
        ####################################################

        self.value = QLabel(
            "--"
        )

        self.value.setObjectName(
            "InfoValue"
        )

        self.value.setAlignment(
            Qt.AlignCenter
        )

        ####################################################
        # LAYOUT
        ####################################################

        layout.addWidget(
            self.title
        )

        layout.addWidget(
            self.value
        )

    ########################################################
    # SET VALUE
    ########################################################

    def setValue(
        self,
        value,
    ):

        self.value.setText(
            str(value)
        )


############################################################
# TOP BAR
############################################################

class TopBar(QWidget):

    def __init__(
        self,
    ):

        super().__init__()

        ####################################################
        # SIZE
        ####################################################

        self.setFixedHeight(
            54
        )

        self.setObjectName(
            "TopBar"
        )

        ####################################################
        # ROOT LAYOUT
        ####################################################

        root = QHBoxLayout(
            self
        )

        root.setContentsMargins(
            22,
            4,
            22,
            4,
        )

        root.setSpacing(
            10
        )

        ####################################################
        # JARVIS IDENTIFIER
        ####################################################

        self.logo = QLabel(
            "JARVIS X"
        )

        self.logo.setObjectName(
            "JarvisTopLogo"
        )

        self.logo.setAlignment(
            Qt.AlignVCenter |
            Qt.AlignLeft
        )

        root.addWidget(
            self.logo
        )

        ####################################################
        # FLEX SPACE
        ####################################################

        root.addStretch(
            1
        )

        ####################################################
        # LIVE SYSTEM TELEMETRY
        ####################################################

        self.cpu = InfoBox(
            "CPU"
        )

        self.ram = InfoBox(
            "RAM"
        )

        self.disk = InfoBox(
            "DISK"
        )

        self.net = InfoBox(
            "NET"
        )

        root.addWidget(
            self.cpu
        )

        root.addWidget(
            self.ram
        )

        root.addWidget(
            self.disk
        )

        root.addWidget(
            self.net
        )

        ####################################################
        # DIVIDER
        ####################################################

        divider = QFrame()

        divider.setObjectName(
            "TopDivider"
        )

        divider.setFixedWidth(
            1
        )

        divider.setFixedHeight(
            24
        )

        root.addWidget(
            divider
        )

        ####################################################
        # SYSTEM STATUS
        ####################################################

        self.status = QLabel(
            "● ONLINE"
        )

        self.status.setObjectName(
            "Online"
        )

        self.status.setAlignment(
            Qt.AlignCenter
        )

        root.addWidget(
            self.status
        )

        ####################################################
        # CLOCK
        ####################################################

        self.clock = QLabel(
            "00:00:00"
        )

        self.clock.setObjectName(
            "Clock"
        )

        self.clock.setAlignment(
            Qt.AlignRight |
            Qt.AlignVCenter
        )

        root.addWidget(
            self.clock
        )

        ####################################################
        # UPDATE TIMER
        ####################################################

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.updateStats
        )

        self.timer.start(
            1000
        )

        ####################################################
        # INITIAL DATA
        ####################################################

        self.updateStats()

    ########################################################
    # UPDATE TELEMETRY
    ########################################################

    def updateStats(
        self,
    ):

        ####################################################
        # CPU
        ####################################################

        try:

            cpu = SystemMonitor.cpu()

            self.cpu.setValue(
                f"{cpu}%"
            )

        except Exception:

            self.cpu.setValue(
                "--"
            )

        ####################################################
        # RAM
        ####################################################

        try:

            ram = SystemMonitor.ram()

            self.ram.setValue(
                f"{ram}%"
            )

        except Exception:

            self.ram.setValue(
                "--"
            )

        ####################################################
        # DISK
        ####################################################

        try:

            disk = SystemMonitor.disk()

            self.disk.setValue(
                f"{disk}%"
            )

        except Exception:

            self.disk.setValue(
                "--"
            )

        ####################################################
        # NETWORK
        ####################################################

        try:

            sent, received = (
                SystemMonitor.network_usage()
            )

            self.net.setValue(
                f"{received:.1f} MB"
            )

        except Exception:

            self.net.setValue(
                "--"
            )

        ####################################################
        # CLOCK
        ####################################################

        try:

            self.clock.setText(
                SystemMonitor.current_time()
            )

        except Exception:

            self.clock.setText(
                "--:--:--"
            )