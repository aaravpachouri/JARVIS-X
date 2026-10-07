from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
)
from PySide6.QtGui import QColor, Qt


class GlowButton(QPushButton):

    def __init__(self, text=""):
        super().__init__(text)

        self.base = QColor("#07111D")

        self.hover = QColor("#0B2235")

        self.current = self.base

        self.setCursor(Qt.PointingHandCursor)

        self.setMinimumSize(72,72)

        self.anim = QPropertyAnimation(
            self,
            b"geometry"
        )

        self.anim.setDuration(170)

        self.anim.setEasingCurve(
            QEasingCurve.OutCubic
        )

    ##################################################

    def enterEvent(self, e):

        g = self.geometry()

        self.anim.stop()

        self.anim.setStartValue(g)

        self.anim.setEndValue(

            g.adjusted(
                -3,
                -3,
                3,
                3
            )

        )

        self.anim.start()

        super().enterEvent(e)

    ##################################################

    def leaveEvent(self,e):

        g=self.geometry()

        self.anim.stop()

        self.anim.setStartValue(g)

        self.anim.setEndValue(

            g.adjusted(
                3,
                3,
                -3,
                -3
            )

        )

        self.anim.start()

        super().leaveEvent(e)