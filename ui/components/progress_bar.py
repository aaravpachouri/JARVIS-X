from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt


class ProgressBar(QWidget):

    def __init__(self):

        super().__init__()

        self.value = 50

        self.setFixedSize(220, 12)

    def setValue(self, value):

        self.value = value

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        ##################################################

        painter.setPen(Qt.NoPen)

        painter.setBrush(QColor(20, 35, 45))

        painter.drawRoundedRect(
            self.rect(),
            6,
            6
        )

        ##################################################

        width = int(
            self.width() * self.value / 100
        )

        painter.setBrush(
            QColor(0, 230, 255)
        )

        painter.drawRoundedRect(
            0,
            0,
            width,
            self.height(),
            6,
            6
        )

        ##################################################

        glow = QPen(
            QColor(150, 255, 255, 120),
            1
        )

        painter.setPen(glow)

        painter.drawRoundedRect(
            self.rect().adjusted(0, 0, -1, -1),
            6,
            6
        )