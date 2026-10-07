from PySide6.QtWidgets import QWidget

from PySide6.QtCore import (
    Qt,
    QTimer,
)

from PySide6.QtGui import (
    QPainter,
    QColor,
)


class HUDBar(QWidget):

    def __init__(self):

        super().__init__()

        ##################################################
        # VALUES
        ##################################################

        self.value = 50

        ##################################################
        # GLOW ANIMATION
        ##################################################

        self.glow = 40

        self.direction = 1

        ##################################################

        self.setFixedHeight(12)

        ##################################################
        # TIMER
        ##################################################

        self.timer = QTimer(self)

        self.timer.timeout.connect(self.animate)

        self.timer.start(35)

    ##################################################

    def setValue(self, value):

        self.value = max(
            0,
            min(
                100,
                value
            )
        )

    ##################################################
    # BREATHING EFFECT
    ##################################################

    def animate(self):

        self.glow += self.direction * 5

        if self.glow >= 130:

            self.glow = 130

            self.direction = -1

        elif self.glow <= 30:

            self.glow = 30

            self.direction = 1

        self.update()

    ##################################################
    # PAINT
    ##################################################

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        totalSegments = 18

        gap = 3

        h = self.height()

        segmentWidth = (

            self.width()

            - gap * (totalSegments - 1)

        ) / totalSegments

        active = int(

            self.value

            / 100

            * totalSegments

        )

        ##################################################
        # DRAW
        ##################################################

        for i in range(totalSegments):

            x = i * (

                segmentWidth + gap

            )

            ##################################################
            # ACTIVE
            ##################################################

            if i < active:

                # Outer glow

                painter.fillRect(

                    int(x),

                    0,

                    int(segmentWidth),

                    h,

                    QColor(

                        0,

                        255,

                        255,

                        30

                    )

                )

                # Main block

                painter.fillRect(

                    int(x),

                    2,

                    int(segmentWidth),

                    h - 4,

                    QColor(

                        35,

                        225,

                        255

                    )

                )

                ##################################################
                # LEADING SEGMENT
                ##################################################

                if i == active - 1:

                    painter.fillRect(

                        int(x),

                        1,

                        int(segmentWidth),

                        h - 2,

                        QColor(

                            220,

                            255,

                            255,

                            self.glow

                        )

                    )

            ##################################################
            # INACTIVE
            ##################################################

            else:

                painter.fillRect(

                    int(x),

                    2,

                    int(segmentWidth),

                    h - 4,

                    QColor(

                        18,

                        34,

                        45

                    )

                )

        painter.end()