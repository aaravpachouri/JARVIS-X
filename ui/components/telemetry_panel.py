from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
)

from PySide6.QtCore import Qt, QTimer

from PySide6.QtGui import (
    QFont,
    QPainter,
    QColor,
    QPen,
)

import random

from ui.components.hud_bar import HUDBar


class TelemetryPanel(QWidget):

    def __init__(self):

        super().__init__()

        ##################################################
        # PANEL
        ##################################################

        self.setFixedWidth(320)

        self.layout = QVBoxLayout(self)

        self.layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        self.layout.setSpacing(18)

        ##################################################
        # TITLE
        ##################################################

        title = QLabel("SYSTEM STATUS")

        font = QFont()

        font.setPointSize(15)

        font.setBold(True)

        title.setFont(font)

        title.setStyleSheet("""
            color:#8BE9FD;
        """)

        self.layout.addWidget(title)

        ##################################################
        # SUBTITLE
        ##################################################

        subtitle = QLabel("PRIMARY CORE")

        subtitle.setStyleSheet("""
            color:#36DFFF;
            font-size:10px;
            letter-spacing:2px;
        """)

        self.layout.addWidget(subtitle)

        ##################################################
        # METRICS
        ##################################################

        self.cpu = self.createMetric("CPU", 32)
        self.ram = self.createMetric("RAM", 78)
        self.gpu = self.createMetric("GPU", 46)
        self.net = self.createMetric("NETWORK", 69)
        self.temp = self.createMetric("CORE TEMP", 57)

        self.layout.addStretch()

        ##################################################
        # SCAN LINE
        ##################################################

        self.scanY = -80

        ##################################################
        # TIMER
        ##################################################

        self.timer = QTimer(self)

        self.timer.timeout.connect(self.animate)

        self.timer.start(1200)

    ##################################################

    def createMetric(self, name, value):

        container = QWidget()

        layout = QVBoxLayout(container)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(5)

        ##################################################
        # TOP ROW
        ##################################################

        top = QHBoxLayout()

        top.setContentsMargins(0, 0, 0, 0)

        top.setSpacing(6)

        ##################################################
        # LED
        ##################################################

        led = QLabel("●")

        led.setFixedWidth(12)

        led.setStyleSheet("""
            color:#28E1FF;
            font-size:11px;
        """)

        ##################################################
        # LABEL
        ##################################################

        label = QLabel(name)

        label.setStyleSheet("""
            color:white;
            font-size:12px;
        """)

        ##################################################
        # VALUE
        ##################################################

        valueLabel = QLabel(f"{value}%")

        valueLabel.setFixedWidth(48)

        valueLabel.setAlignment(
            Qt.AlignRight |
            Qt.AlignVCenter
        )

        valueLabel.setStyleSheet("""
            color:#4DEBFF;
            font-size:12px;
            font-weight:bold;
        """)

        ##################################################
        # LAYOUT
        ##################################################

        top.addWidget(led)

        top.addWidget(label)

        top.addStretch()

        top.addWidget(valueLabel)

        layout.addLayout(top)

        ##################################################
        # HUD BAR
        ##################################################

        bar = HUDBar()

        bar.setValue(value)

        layout.addWidget(bar)

        self.layout.addWidget(container)

        return (bar, valueLabel)

    ##################################################

    def animate(self):

        metrics = [

            self.cpu,
            self.ram,
            self.gpu,
            self.net,
            self.temp

        ]

        for bar, label in metrics:

            current = int(
                label.text().replace("%", "")
            )

            target = current + random.randint(-3, 3)

            target = max(15, min(95, target))

            bar.setValue(target)

            label.setText(f"{target}%")

        ##################################################

        self.scanY += 3

        if self.scanY > self.height() + 80:

            self.scanY = -80

        self.update()

    ##################################################

    def paintEvent(self, event):

        super().paintEvent(event)

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        w = self.width() - 1

        h = self.height() - 1

        corner = 28

        ##################################################
        # OUTER GLOW
        ##################################################

        glow = QPen(
            QColor(0,220,255,35),
            6
        )

        painter.setPen(glow)

        corners = [

            ((0,0),(corner,0)),
            ((0,0),(0,corner)),

            ((w,0),(w-corner,0)),
            ((w,0),(w,corner)),

            ((0,h),(corner,h)),
            ((0,h),(0,h-corner)),

            ((w,h),(w-corner,h)),
            ((w,h),(w,h-corner))

        ]

        for p1, p2 in corners:

            painter.drawLine(

                p1[0],
                p1[1],

                p2[0],
                p2[1]

            )

        ##################################################
        # MAIN FRAME
        ##################################################

        frame = QPen(
            QColor(0,220,255,180),
            2
        )

        painter.setPen(frame)

        for p1, p2 in corners:

            painter.drawLine(

                p1[0],
                p1[1],

                p2[0],
                p2[1]

            )

        ##################################################
        # HEADER DIVIDER
        ##################################################

        painter.setPen(

            QPen(

                QColor(0,220,255,120),

                1

            )

        )

        painter.drawLine(

            18,

            64,

            w - 18,

            64

        )

        ##################################################
        # SCAN LINE
        ##################################################

        painter.setPen(

            QPen(

                QColor(0,220,255,40),

                2

            )

        )

        painter.drawLine(

            15,

            self.scanY,

            self.width() - 15,

            self.scanY

        )

        painter.end()