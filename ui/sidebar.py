from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)

from PySide6.QtCore import Qt

from ui.components.hud_panel import HUDPanel


class Sidebar(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedWidth(115)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(15, 20, 15, 20)

        layout.setSpacing(18)

        ####################################################
        # LOGO
        ####################################################

        logo = QLabel("J")

        logo.setAlignment(Qt.AlignCenter)

        logo.setObjectName("JarvisLogo")

        layout.addWidget(logo)

        ####################################################
        # BUTTONS
        ####################################################

        icons = [

            "⌂",

            "💬",

            "🎤",

            "🧠",

            "👁",

            "⚙",

            "⚡"

        ]

        self.cards = []

        for icon in icons:

            panel = HUDPanel()

            panel.setFixedSize(74,74)

            inside = QVBoxLayout(panel)

            inside.setContentsMargins(0,0,0,0)

            label = QLabel(icon)

            label.setAlignment(Qt.AlignCenter)

            label.setObjectName("SideIcon")

            inside.addWidget(label)

            layout.addWidget(
                panel,
                alignment=Qt.AlignCenter
            )

            self.cards.append(panel)

        layout.addStretch()