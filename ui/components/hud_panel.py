from PySide6.QtWidgets import QFrame
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
)
from PySide6.QtCore import Qt


class HUDPanel(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_TranslucentBackground)

    #######################################################

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        r = self.rect().adjusted(1,1,-1,-1)

        ####################################################
        # PANEL
        ####################################################

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor(
                6,
                15,
                26,
                225
            )
        )

        painter.drawRoundedRect(
            r,
            26,
            26
        )

        ####################################################
        # BORDER
        ####################################################

        pen = QPen(
            QColor(
                70,
                200,
                255,
                120
            ),
            2
        )

        painter.setPen(pen)

        painter.setBrush(Qt.NoBrush)

        painter.drawRoundedRect(
            r,
            26,
            26
        )

        ####################################################
        # CORNER LINES
        ####################################################

        pen = QPen(
            QColor(
                120,
                235,
                255,
                220
            ),
            2
        )

        painter.setPen(pen)

        l = 22

        painter.drawLine(18,18,18+l,18)
        painter.drawLine(18,18,18,18+l)

        painter.drawLine(
            self.width()-18,
            18,
            self.width()-18-l,
            18
        )

        painter.drawLine(
            self.width()-18,
            18,
            self.width()-18,
            18+l
        )

        painter.drawLine(
            18,
            self.height()-18,
            18+l,
            self.height()-18
        )

        painter.drawLine(
            18,
            self.height()-18,
            18,
            self.height()-18-l
        )

        painter.drawLine(
            self.width()-18,
            self.height()-18,
            self.width()-18-l,
            self.height()-18
        )

        painter.drawLine(
            self.width()-18,
            self.height()-18,
            self.width()-18,
            self.height()-18-l
        )