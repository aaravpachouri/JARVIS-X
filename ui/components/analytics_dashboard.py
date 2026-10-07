from __future__ import annotations

import math

from datetime import datetime, timedelta
from collections import Counter

from business_outreach.outreach.lead_tracker import (
    LeadTracker,
)

from PySide6.QtCore import (
    Qt,
    QTimer,
    QPointF,
    QRectF,
)

from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
    QBrush,
    QPainterPath,
    QLinearGradient,
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
)


############################################################
# DATA ENGINE
############################################################

class OutreachAnalytics:

    """
    Live business-outreach analytics backed by LeadTracker.

    LeadTracker is the single source of truth for lead state and
    history. The dashboard never reads lead_history.json directly.

    The analytics layer exposes the same API expected by the
    existing visual components while adding support for the full
    outreach lifecycle:

        DISCOVERED -> CONTACTED -> REPLIED -> INTERESTED
        -> DEMO_SENT -> CLIENT

    Rejected and skipped leads remain visible as pipeline exits.
    """

    def __init__(self):

        self.tracker = LeadTracker()

        self.records = {}

        self.last_loaded = None

        self.refresh()

    ########################################################
    # REFRESH
    ########################################################

    def refresh(self):

        try:

            self.tracker.refresh()

            self.records = self.tracker.get_snapshot()

        except Exception as exc:

            print(
                "[Analytics] LeadTracker refresh failed:",
                exc,
            )

            self.records = {}

        self.last_loaded = datetime.now()

    ########################################################
    # ALL RECORDS
    ########################################################

    def all_records(self):

        return [
            record
            for record in self.records.values()
            if isinstance(record, dict)
        ]

    ########################################################
    # STATUS
    ########################################################

    @staticmethod
    def status(record):

        return str(
            record.get("status", "")
            or ""
        ).strip().upper()

    ########################################################
    # CATEGORY
    ########################################################

    @staticmethod
    def category(record):

        return str(
            record.get("category", "UNKNOWN")
            or "UNKNOWN"
        ).strip()

    ########################################################
    # COUNT
    ########################################################

    def count(self, status):

        target = str(status).strip().upper()

        return sum(
            1
            for record in self.all_records()
            if self.status(record) == target
        )

    ########################################################
    # TOTAL
    ########################################################

    def total(self):

        return len(self.all_records())

    ########################################################
    # DISCOVERED / OPPORTUNITIES
    ########################################################

    def discovered(self):

        active_states = {
            "DISCOVERED",
            "CONTACTED",
            "REPLIED",
            "INTERESTED",
            "DEMO_SENT",
            "CLIENT",
            "NOT_INTERESTED",
        }

        return sum(
            1
            for record in self.all_records()
            if self.status(record) in active_states
        )

    ########################################################
    # QUALIFIED
    ########################################################

    def qualified(self):

        excluded = {
            "NEW",
            "REJECTED_WEBSITE",
            "REJECTED_TOO_ESTABLISHED",
            "SKIPPED_NO_PHONE",
            "SKIPPED_MANUALLY",
            "SKIPPED_CONTACT_FAILED",
        }

        return sum(
            1
            for record in self.all_records()
            if self.status(record) not in excluded
        )

    ########################################################
    # CONTACTED
    ########################################################

    def contacted(self):

        contacted_states = {
            "CONTACTED",
            "REPLIED",
            "INTERESTED",
            "DEMO_SENT",
            "CLIENT",
            "NOT_INTERESTED",
        }

        return sum(
            1
            for record in self.all_records()
            if self.status(record) in contacted_states
        )

    ########################################################
    # REPLIED
    ########################################################

    def replied(self):

        replied_states = {
            "REPLIED",
            "INTERESTED",
            "DEMO_SENT",
            "CLIENT",
        }

        return sum(
            1
            for record in self.all_records()
            if self.status(record) in replied_states
        )

    ########################################################
    # INTERESTED
    ########################################################

    def interested(self):

        interested_states = {
            "INTERESTED",
            "DEMO_SENT",
            "CLIENT",
        }

        return sum(
            1
            for record in self.all_records()
            if self.status(record) in interested_states
        )

    ########################################################
    # DEMOS
    ########################################################

    def demos(self):

        demo_states = {
            "DEMO_SENT",
            "CLIENT",
        }

        return sum(
            1
            for record in self.all_records()
            if self.status(record) in demo_states
        )

    ########################################################
    # CLIENTS
    ########################################################

    def clients(self):

        return self.count("CLIENT")

    ########################################################
    # REJECTED
    ########################################################

    def rejected(self):

        return sum(
            1
            for record in self.all_records()
            if self.status(record).startswith("REJECTED")
        )

    ########################################################
    # SKIPPED
    ########################################################

    def skipped(self):

        return sum(
            1
            for record in self.all_records()
            if self.status(record).startswith("SKIPPED")
        )

    ########################################################
    # NOT INTERESTED
    ########################################################

    def not_interested(self):

        return self.count("NOT_INTERESTED")

    ########################################################
    # REPLY RATE
    ########################################################

    def reply_rate(self):

        contacted = self.contacted()

        if contacted <= 0:

            return 0.0

        return (
            self.replied()
            / contacted
            * 100.0
        )

    ########################################################
    # INTEREST RATE
    ########################################################

    def interest_rate(self):

        contacted = self.contacted()

        if contacted <= 0:

            return 0.0

        return (
            self.interested()
            / contacted
            * 100.0
        )

    ########################################################
    # DEMO RATE
    ########################################################

    def demo_rate(self):

        contacted = self.contacted()

        if contacted <= 0:

            return 0.0

        return (
            self.demos()
            / contacted
            * 100.0
        )

    ########################################################
    # CLIENT RATE
    ########################################################

    def client_rate(self):

        contacted = self.contacted()

        if contacted <= 0:

            return 0.0

        return (
            self.clients()
            / contacted
            * 100.0
        )

    ########################################################
    # CATEGORY DISTRIBUTION
    ########################################################

    def categories(self):

        counter = Counter()

        for record in self.all_records():

            counter[
                self.category(record).upper()
            ] += 1

        return counter

    ########################################################
    # STATUS DISTRIBUTION
    ########################################################

    def statuses(self):

        counter = Counter()

        for record in self.all_records():

            counter[
                self.status(record)
            ] += 1

        return counter

    ########################################################
    # REJECTION DISTRIBUTION
    ########################################################

    def rejection_types(self):

        counter = Counter()

        for record in self.all_records():

            status = self.status(record)

            if status.startswith("REJECTED"):

                counter[status] += 1

        return counter

    ########################################################
    # RECENT CONTACTS
    ########################################################

    def recent_contacts(self, limit=8):

        records = []

        for record in self.all_records():

            timestamp = str(
                record.get("contacted_at", "")
                or ""
            ).strip()

            if not timestamp:

                continue

            records.append(
                (timestamp, record)
            )

        records.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            record
            for _, record in records[:limit]
        ]

    ########################################################
    # TIMESTAMP PARSER
    ########################################################

    @staticmethod
    def _date_from_record(record, field_name):

        timestamp = str(
            record.get(field_name, "")
            or ""
        ).strip()

        if not timestamp:

            return None

        try:

            return datetime.fromisoformat(
                timestamp
            ).date()

        except Exception:

            return None

    ########################################################
    # ACTIVITY TIMELINE
    ########################################################

    def daily_activity(self, days=14):

        days = max(
            1,
            int(days),
        )

        today = datetime.now().date()

        result = {
            today - timedelta(days=index):
                {
                    "discovered": 0,
                    "contacted": 0,
                    "replied": 0,
                }
            for index in range(days)
        }

        for record in self.all_records():

            discovered_day = self._date_from_record(
                record,
                "discovered_at",
            )

            if discovered_day in result:

                result[
                    discovered_day
                ][
                    "discovered"
                ] += 1

            contacted_day = self._date_from_record(
                record,
                "contacted_at",
            )

            if contacted_day in result:

                result[
                    contacted_day
                ][
                    "contacted"
                ] += 1

            ################################################
            # Prefer the explicit reply timestamp added by
            # LeadTracker. For older records, fall back to
            # updated_at for reply-capable states.
            ################################################

            replied_day = self._date_from_record(
                record,
                "replied_at",
            )

            if replied_day is None:

                if self.status(record) in {
                    "REPLIED",
                    "INTERESTED",
                    "DEMO_SENT",
                    "CLIENT",
                }:

                    replied_day = self._date_from_record(
                        record,
                        "updated_at",
                    )

            if replied_day in result:

                result[
                    replied_day
                ][
                    "replied"
                ] += 1

        return {
            day: result[day]
            for day in sorted(result)
        }


############################################################
# HUD PANEL
############################################################

class HUDPanel(QFrame):

    def __init__(
        self,
        title,
        subtitle="",
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.setObjectName(
            "HUDPanel"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        layout.setSpacing(
            8
        )

        ####################################################
        # HEADER
        ####################################################

        header = QHBoxLayout()

        title_label = QLabel(
            title.upper()
        )

        title_label.setStyleSheet(
            """
            color:#77F2FF;
            font-size:9px;
            font-weight:bold;
            letter-spacing:2px;
            background:transparent;
            """
        )

        header.addWidget(
            title_label
        )

        header.addStretch()

        if subtitle:

            subtitle_label = QLabel(
                subtitle.upper()
            )

            subtitle_label.setStyleSheet(
                """
                color:rgba(110,230,255,135);
                font-size:7px;
                letter-spacing:1px;
                background:transparent;
                """
            )

            header.addWidget(
                subtitle_label
            )

        layout.addLayout(
            header
        )

        self.body = QVBoxLayout()

        self.body.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.addLayout(
            self.body,
            1,
        )


############################################################
# METRIC CARD
############################################################

class DealMetric(QFrame):

    def __init__(
        self,
        title,
        value,
        secondary,
        accent,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.setObjectName(
            "DealMetric"
        )

        self.accent = accent

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            14,
            11,
            14,
            11,
        )

        layout.setSpacing(
            5
        )

        ####################################################
        # TITLE
        ####################################################

        label = QLabel(
            title.upper()
        )

        label.setStyleSheet(
            f"""
            color:{accent.name()};
            font-size:8px;
            font-weight:bold;
            letter-spacing:1.5px;
            background:transparent;
            """
        )

        layout.addWidget(
            label
        )

        ####################################################
        # VALUE
        ####################################################

        self.value_label = QLabel(
            str(value)
        )

        self.value_label.setStyleSheet(
            """
            color:#E8FCFF;
            font-size:25px;
            font-weight:bold;
            font-family:Consolas;
            background:transparent;
            """
        )

        layout.addWidget(
            self.value_label
        )

        ####################################################
        # SECONDARY
        ####################################################

        self.secondary_label = QLabel(
            secondary
        )

        self.secondary_label.setStyleSheet(
            """
            color:rgba(185,235,245,170);
            font-size:8px;
            background:transparent;
            """
        )

        layout.addWidget(
            self.secondary_label
        )

    ########################################################
    # UPDATE
    ########################################################

    def set_value(
        self,
        value,
        secondary=None,
    ):

        self.value_label.setText(
            str(value)
        )

        if secondary is not None:

            self.secondary_label.setText(
                str(secondary)
            )


############################################################
# HOLOGRAPHIC DEAL CORE
############################################################

class DealIntelligenceCore(QWidget):

    def __init__(
        self,
        analytics,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.analytics = analytics

        self.rotation = 0.0
        self.rotation2 = 0.0
        self.sweep = 0.0
        self.pulse = 0.0

        self.total = 0
        self.contacted = 0
        self.interested = 0
        self.clients = 0

        self.nodes = []

        ####################################################
        # NETWORK NODES
        ####################################################

        for index in range(28):

            angle = (
                math.tau
                * index
                / 28
            )

            radius = (
                125
                +
                (index % 5)
                * 24
            )

            self.nodes.append(
                {
                    "angle": angle,
                    "radius": radius,
                    "speed": (
                        0.0015
                        +
                        index % 4
                        * 0.0007
                    ),
                }
            )

        ####################################################
        # ANIMATION
        ####################################################

        self.animation = QTimer(
            self
        )

        self.animation.setInterval(
            28
        )

        self.animation.timeout.connect(
            self.animate
        )

        self.animation.start()

        ####################################################
        # DATA
        ####################################################

        self.refresh_timer = QTimer(
            self
        )

        self.refresh_timer.setInterval(
            1200
        )

        self.refresh_timer.timeout.connect(
            self.refresh_data
        )

        self.refresh_timer.start()

        self.refresh_data()

    ########################################################
    # DATA
    ########################################################

    def refresh_data(
        self
    ):

        self.analytics.refresh()

        self.total = (
            self.analytics.total()
        )

        self.contacted = (
            self.analytics.contacted()
        )

        self.interested = (
            self.analytics.interested()
        )

        self.clients = (
            self.analytics.clients()
        )

        self.update()

    ########################################################
    # ANIMATE
    ########################################################

    def animate(
        self
    ):

        self.rotation += 0.42

        self.rotation2 -= 0.72

        self.sweep += 2.0

        self.pulse += 0.025

        if self.rotation >= 360:

            self.rotation -= 360

        if self.rotation2 <= -360:

            self.rotation2 += 360

        if self.sweep >= 360:

            self.sweep -= 360

        for node in self.nodes:

            node["angle"] += (
                node["speed"]
            )

        self.update()

    ########################################################
    # PAINT
    ########################################################

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        rect = self.rect()

        center = QPointF(
            rect.width() / 2,
            rect.height() / 2,
        )

        radius = min(
            rect.width(),
            rect.height(),
        ) * 0.39

        cyan = QColor(
            63,
            226,
            255,
        )

        pale = QColor(
            206,
            249,
            255,
        )

        blue = QColor(
            92,
            129,
            255,
        )

        ####################################################
        # BACKGROUND GRID
        ####################################################

        painter.setPen(
            QPen(
                QColor(
                    65,
                    220,
                    255,
                    18,
                ),
                1,
            )
        )

        for x in range(
            0,
            rect.width(),
            24,
        ):

            painter.drawLine(
                x,
                0,
                x,
                rect.height(),
            )

        for y in range(
            0,
            rect.height(),
            24,
        ):

            painter.drawLine(
                0,
                y,
                rect.width(),
                y,
            )

        ####################################################
        # OUTER GLOW
        ####################################################

        for index in range(
            10,
            0,
            -1,
        ):

            r = (
                radius
                *
                (
                    0.92
                    +
                    index * 0.014
                )
            )

            painter.setPen(
                QPen(
                    QColor(
                        30,
                        210,
                        255,
                        7 + index * 3,
                    ),
                    3,
                )
            )

            painter.drawEllipse(
                center,
                r,
                r,
            )

        ####################################################
        # ROTATING TICK RING
        ####################################################

        painter.save()

        painter.translate(
            center
        )

        painter.rotate(
            self.rotation
        )

        for index in range(
            72
        ):

            painter.save()

            painter.rotate(
                index * 5
            )

            length = (
                13
                if index % 6 == 0
                else 6
            )

            painter.setPen(
                QPen(
                    QColor(
                        80,
                        235,
                        255,
                        185
                        if index % 6 == 0
                        else 70,
                    ),
                    2,
                )
            )

            painter.drawLine(
                0,
                -radius,
                0,
                -radius + length,
            )

            painter.restore()

        painter.restore()

        ####################################################
        # OUTER SEGMENTS
        ####################################################

        painter.save()

        painter.translate(
            center
        )

        painter.rotate(
            self.rotation2
        )

        outer_rect = QRectF(
            -radius * 0.88,
            -radius * 0.88,
            radius * 1.76,
            radius * 1.76,
        )

        for index in range(
            18
        ):

            painter.setPen(
                QPen(
                    (
                        pale
                        if index % 4 == 0
                        else cyan
                    ),
                    3,
                )
            )

            painter.drawArc(
                outer_rect,
                index * 20 * 16,
                (
                    10
                    if index % 3
                    else 14
                ) * 16,
            )

        painter.restore()

        ####################################################
        # DEAL FLOW ORBIT
        ####################################################

        orbit_radius = (
            radius * 0.72
        )

        statuses = [
            self.total,
            self.contacted,
            self.interested,
            self.clients,
        ]

        total_status = max(
            1,
            sum(
                statuses
            )
        )

        status_colors = [
            cyan,
            blue,
            QColor(
                155,
                110,
                255,
            ),
            pale,
        ]

        start_angle = -90.0

        for index, value in enumerate(
            statuses
        ):

            span = (
                value
                /
                total_status
                *
                360.0
            )

            painter.setPen(
                QPen(
                    status_colors[index],
                    8,
                )
            )

            painter.drawArc(
                QRectF(
                    center.x()
                    - orbit_radius,
                    center.y()
                    - orbit_radius,
                    orbit_radius * 2,
                    orbit_radius * 2,
                ),
                int(
                    start_angle * 16
                ),
                int(
                    -span * 16
                ),
            )

            start_angle -= span

        ####################################################
        # NETWORK NODES
        ####################################################

        for index, node in enumerate(
            self.nodes
        ):

            angle = node[
                "angle"
            ]

            r = node[
                "radius"
            ]

            x = (
                center.x()
                +
                math.cos(angle)
                * r
            )

            y = (
                center.y()
                +
                math.sin(angle)
                * r
            )

            next_index = (
                (
                    index + 1
                )
                %
                len(
                    self.nodes
                )
            )

            next_node = self.nodes[
                next_index
            ]

            nx = (
                center.x()
                +
                math.cos(
                    next_node["angle"]
                )
                *
                next_node["radius"]
            )

            ny = (
                center.y()
                +
                math.sin(
                    next_node["angle"]
                )
                *
                next_node["radius"]
            )

            painter.setPen(
                QPen(
                    QColor(
                        60,
                        220,
                        255,
                        30,
                    ),
                    1,
                )
            )

            painter.drawLine(
                x,
                y,
                nx,
                ny,
            )

            painter.setPen(
                Qt.NoPen
            )

            painter.setBrush(
                cyan
            )

            painter.drawEllipse(
                QPointF(
                    x,
                    y,
                ),
                2,
                2,
            )

        ####################################################
        # RADIAL DATA MATRIX
        ####################################################

        painter.save()

        painter.translate(
            center
        )

        painter.rotate(
            self.rotation * 0.28
        )

        for index in range(
            24
        ):

            painter.save()

            painter.rotate(
                index * 15
            )

            painter.setPen(
                QPen(
                    QColor(
                        65,
                        225,
                        255,
                        80
                        if index % 2 == 0
                        else 32,
                    ),
                    1,
                )
            )

            painter.drawLine(
                0,
                -radius * 0.16,
                0,
                -radius * 0.65,
            )

            painter.restore()

        painter.restore()

        ####################################################
        # SCAN SWEEP
        ####################################################

        painter.save()

        painter.translate(
            center
        )

        painter.rotate(
            self.sweep
        )

        painter.setPen(
            QPen(
                QColor(
                    78,
                    240,
                    255,
                    200,
                ),
                2,
            )
        )

        painter.drawLine(
            0,
            0,
            0,
            -radius * 0.88,
        )

        painter.setPen(
            QPen(
                QColor(
                    70,
                    225,
                    255,
                    55,
                ),
                10,
            )
        )

        painter.drawArc(
            QRectF(
                -radius * 0.78,
                -radius * 0.78,
                radius * 1.56,
                radius * 1.56,
            ),
            48 * 16,
            28 * 16,
        )

        painter.restore()

        ####################################################
        # CENTRAL CORE
        ####################################################

        core = radius * 0.27

        gradient = QLinearGradient(
            center.x() - core,
            center.y() - core,
            center.x() + core,
            center.y() + core,
        )

        gradient.setColorAt(
            0.0,
            QColor(
                30,
                255,
                255,
                210,
            ),
        )

        gradient.setColorAt(
            0.5,
            QColor(
                40,
                140,
                255,
                130,
            ),
        )

        gradient.setColorAt(
            1.0,
            QColor(
                100,
                60,
                255,
                100,
            ),
        )

        painter.setPen(
            QPen(
                pale,
                2,
            )
        )

        painter.setBrush(
            QBrush(
                gradient
            )
        )

        painter.drawEllipse(
            center,
            core,
            core,
        )

        ####################################################
        # CENTER CIRCLES
        ####################################################

        for ratio in (
            0.82,
            0.61,
            0.38,
        ):

            painter.setPen(
                QPen(
                    cyan,
                    1,
                )
            )

            painter.setBrush(
                Qt.NoBrush
            )

            painter.drawEllipse(
                center,
                core * ratio,
                core * ratio,
            )

        ####################################################
        # CORE TEXT
        ####################################################

        painter.setPen(
            pale
        )

        painter.setFont(
            QFont(
                "Consolas",
                9,
                QFont.Bold,
            )
        )

        painter.drawText(
            QRectF(
                center.x() - 70,
                center.y() - 14,
                140,
                20,
            ),
            Qt.AlignCenter,
            "DEAL MATRIX",
        )

        painter.setFont(
            QFont(
                "Consolas",
                17,
                QFont.Bold,
            )
        )

        painter.drawText(
            QRectF(
                center.x() - 80,
                center.y() + 8,
                160,
                30,
            ),
            Qt.AlignCenter,
            f"{self.total:,}",
        )

        painter.setFont(
            QFont(
                "Segoe UI",
                7,
            )
        )

        painter.setPen(
            QColor(
                170,
                240,
                250,
                175,
            )
        )

        painter.drawText(
            QRectF(
                center.x() - 90,
                center.y() + 36,
                180,
                18,
            ),
            Qt.AlignCenter,
            "LIVE LEAD INTELLIGENCE",
        )

        painter.end()


############################################################
# FUNNEL
############################################################

class LeadFunnel(QWidget):

    def __init__(
        self,
        analytics,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.analytics = analytics

        self.timer = QTimer(
            self
        )

        self.timer.setInterval(
            1200
        )

        self.timer.timeout.connect(
            self.refresh
        )

        self.timer.start()

        self.refresh()

    ########################################################
    # REFRESH
    ########################################################

    def refresh(
        self
    ):

        self.total = self.analytics.total()
        self.contacted = self.analytics.contacted()
        self.replied = self.analytics.replied()
        self.interested = self.analytics.interested()
        self.clients = self.analytics.clients()

        self.update()

    ########################################################
    # PAINT
    ########################################################

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        rect = self.rect()

        values = [
            (
                "DISCOVERED",
                self.total,
                QColor(
                    60,
                    225,
                    255,
                ),
            ),
            (
                "CONTACTED",
                self.contacted,
                QColor(
                    95,
                    160,
                    255,
                ),
            ),
            (
                "REPLIED",
                self.replied,
                QColor(
                    140,
                    120,
                    255,
                ),
            ),
            (
                "INTERESTED",
                self.interested,
                QColor(
                    190,
                    100,
                    255,
                ),
            ),
            (
                "CLIENT",
                self.clients,
                QColor(
                    220,
                    245,
                    255,
                ),
            ),
        ]

        maximum = max(
            1,
            self.total,
        )

        y = 18

        for label, value, color in values:

            painter.setPen(
                color
            )

            painter.setFont(
                QFont(
                    "Segoe UI",
                    8,
                    QFont.Bold,
                )
            )

            painter.drawText(
                0,
                y + 15,
                label,
            )

            painter.setPen(
                Qt.NoPen
            )

            painter.setBrush(
                QColor(
                    12,
                    34,
                    48,
                )
            )

            painter.drawRoundedRect(
                92,
                y,
                rect.width() - 130,
                22,
                7,
                7,
            )

            width = (
                (
                    value
                    /
                    maximum
                )
                *
                (
                    rect.width()
                    - 130
                )
            )

            painter.setBrush(
                color
            )

            painter.drawRoundedRect(
                92,
                y,
                width,
                22,
                7,
                7,
            )

            painter.setPen(
                QColor(
                    220,
                    250,
                    255,
                )
            )

            painter.drawText(
                rect.width() - 30,
                y + 15,
                str(
                    value
                ),
            )

            y += 32

        painter.end()


############################################################
# CATEGORY MATRIX
############################################################

class CategoryMatrix(QWidget):

    def __init__(
        self,
        analytics,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.analytics = analytics

        self.timer = QTimer(
            self
        )

        self.timer.setInterval(
            1500
        )

        self.timer.timeout.connect(
            self.refresh
        )

        self.timer.start()

        self.categories = {}

        self.refresh()

    ########################################################
    # REFRESH
    ########################################################

    def refresh(
        self
    ):

        self.categories = dict(
            self.analytics.categories()
        )

        self.update()

    ########################################################
    # PAINT
    ########################################################

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        items = sorted(
            self.categories.items(),
            key=lambda item:
                item[1],
            reverse=True,
        )[:8]

        maximum = max(
            [
                value
                for _, value
                in items
            ]
            or [1]
        )

        y = 6

        colors = [
            QColor(
                55,
                225,
                255,
            ),
            QColor(
                95,
                160,
                255,
            ),
            QColor(
                145,
                115,
                255,
            ),
            QColor(
                190,
                95,
                255,
            ),
        ]

        for index, (name, value) in enumerate(
            items
        ):

            painter.setPen(
                QColor(
                    175,
                    235,
                    245,
                )
            )

            painter.setFont(
                QFont(
                    "Segoe UI",
                    7,
                    QFont.Bold,
                )
            )

            painter.drawText(
                0,
                y + 11,
                name[:18],
            )

            painter.setPen(
                Qt.NoPen
            )

            painter.setBrush(
                QColor(
                    10,
                    29,
                    42,
                )
            )

            painter.drawRoundedRect(
                105,
                y,
                130,
                16,
                5,
                5,
            )

            bar_width = (
                value
                /
                maximum
                *
                130
            )

            painter.setBrush(
                colors[
                    index
                    % len(colors)
                ]
            )

            painter.drawRoundedRect(
                105,
                y,
                bar_width,
                16,
                5,
                5,
            )

            painter.setPen(
                QColor(
                    215,
                    250,
                    255,
                )
            )

            painter.drawText(
                245,
                y + 11,
                str(
                    value
                ),
            )

            y += 24

        painter.end()


############################################################
# ACTIVITY GRAPH
############################################################

class ActivityGraph(QWidget):

    def __init__(
        self,
        analytics,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.analytics = analytics

        self.timeline = {}

        self.timer = QTimer(
            self
        )

        self.timer.setInterval(
            1300
        )

        self.timer.timeout.connect(
            self.refresh
        )

        self.timer.start()

        self.refresh()

    ########################################################
    # REFRESH
    ########################################################

    def refresh(
        self
    ):

        self.timeline = (
            self.analytics.daily_activity(
                14
            )
        )

        self.update()

    ########################################################
    # PAINT
    ########################################################

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        rect = self.rect()

        chart = QRectF(
            32,
            10,
            rect.width() - 48,
            rect.height() - 30,
        )

        ####################################################
        # GRID
        ####################################################

        painter.setPen(
            QPen(
                QColor(
                    75,
                    210,
                    240,
                    30,
                ),
                1,
            )
        )

        for row in range(
            4
        ):

            y = (
                chart.top()
                +
                chart.height()
                *
                row
                / 4
            )

            painter.drawLine(
                chart.left(),
                y,
                chart.right(),
                y,
            )

        values = list(
            self.timeline.values()
        )

        if not values:

            painter.end()

            return

        discovered = [
            item["discovered"]
            for item in values
        ]

        contacted = [
            item["contacted"]
            for item in values
        ]

        replied = [
            item["replied"]
            for item in values
        ]

        maximum = max(
            1,
            max(
                discovered
                + contacted
                + replied
            )
        )

        ####################################################
        # DRAW SERIES
        ####################################################

        series = [
            (
                discovered,
                QColor(
                    60,
                    230,
                    255,
                ),
            ),
            (
                contacted,
                QColor(
                    105,
                    155,
                    255,
                ),
            ),
            (
                replied,
                QColor(
                    180,
                    110,
                    255,
                ),
            ),
        ]

        for values, color in series:

            path = QPainterPath()

            count = len(
                values
            )

            for index, value in enumerate(
                values
            ):

                x = (
                    chart.left()
                    +
                    chart.width()
                    *
                    index
                    /
                    max(
                        1,
                        count - 1
                    )
                )

                y = (
                    chart.bottom()
                    -
                    (
                        value
                        /
                        maximum
                    )
                    *
                    chart.height()
                )

                point = QPointF(
                    x,
                    y,
                )

                if index == 0:

                    path.moveTo(
                        point
                    )

                else:

                    path.lineTo(
                        point
                    )

            painter.setPen(
                QPen(
                    color,
                    2,
                )
            )

            painter.drawPath(
                path
            )

        painter.end()


############################################################
# LIVE DEAL TAPE
############################################################

class DealTape(QWidget):

    def __init__(
        self,
        analytics,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.analytics = analytics

        self.records = []

        self.offset = 0

        self.timer = QTimer(
            self
        )

        self.timer.setInterval(
            45
        )

        self.timer.timeout.connect(
            self.animate
        )

        self.timer.start()

        self.refresh()

    ########################################################
    # REFRESH
    ########################################################

    def refresh(
        self
    ):

        self.records = (
            self.analytics.recent_contacts(
                8
            )
        )

    ########################################################
    # ANIMATE
    ########################################################

    def animate(
        self
    ):

        self.offset += 1

        if self.offset > 10000:

            self.offset = 0

        self.update()

    ########################################################
    # PAINT
    ########################################################

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        rect = self.rect()

        painter.setPen(
            QColor(
                120,
                230,
                245,
            )
        )

        painter.setFont(
            QFont(
                "Segoe UI",
                8,
                QFont.Bold,
            )
        )

        painter.drawText(
            0,
            14,
            "LIVE DEAL TAPE"
        )

        if not self.records:

            painter.setPen(
                QColor(
                    120,
                    190,
                    205,
                )
            )

            painter.setFont(
                QFont(
                    "Consolas",
                    8,
                )
            )

            painter.drawText(
                0,
                40,
                "NO RECENT DEAL ACTIVITY"
            )

            painter.end()

            return

        x = -(
            self.offset % 260
        )

        y = 42

        loops = 0

        while x < rect.width():

            for record in self.records:

                name = str(
                    record.get(
                        "name",
                        "UNKNOWN",
                    )
                )

                status = str(
                    record.get(
                        "status",
                        "",
                    )
                ).upper()

                segment = (
                    f"{name[:28]}"
                    f"  //  "
                    f"{status}"
                    f"          "
                )

                painter.setPen(
                    QColor(
                        180,
                        240,
                        250,
                        180,
                    )
                )

                painter.setFont(
                    QFont(
                        "Consolas",
                        8,
                    )
                )

                painter.drawText(
                    x,
                    y,
                    segment
                )

                x += 260

                loops += 1

                if loops > 20:

                    break

            if loops > 20:

                break

        painter.end()


############################################################
# MAIN ANALYTICS DASHBOARD
############################################################

class AnalyticsDashboard(QWidget):

    """
    JARVIS X
    BUSINESS INTELLIGENCE / DEAL COMMAND CENTER

    Designed as a dense, high-information Stark-style
    command surface rather than a conventional dashboard.

    Uses live outreach history from LeadTracker.
    """

    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.setObjectName(
            "AnalyticsDashboard"
        )

        ####################################################
        # DATA
        ####################################################

        self.analytics = (
            OutreachAnalytics()
        )

        ####################################################
        # ROOT
        ####################################################

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            20,
            14,
            20,
            14,
        )

        root.setSpacing(
            9
        )

        ####################################################
        # TOP CONTROL STRIP
        ####################################################

        header = QHBoxLayout()

        title = QLabel(
            "JARVIS // BUSINESS INTELLIGENCE"
        )

        title.setStyleSheet(
            """
            color:#E5FCFF;
            font-size:18px;
            font-weight:bold;
            letter-spacing:3px;
            background:transparent;
            """
        )

        header.addWidget(
            title
        )

        header.addStretch()

        self.live_status = QLabel(
            "● LIVE DEAL STREAM"
        )

        self.live_status.setStyleSheet(
            """
            color:#56EFFF;
            font-size:8px;
            font-weight:bold;
            letter-spacing:1px;
            background:transparent;
            """
        )

        header.addWidget(
            self.live_status
        )

        self.time_label = QLabel(
            "--:--:--"
        )

        self.time_label.setStyleSheet(
            """
            color:rgba(175,235,245,175);
            font-size:8px;
            font-family:Consolas;
            background:transparent;
            """
        )

        header.addWidget(
            self.time_label
        )

        root.addLayout(
            header
        )

        ####################################################
        # KPI STRIP
        ####################################################

        kpi = QHBoxLayout()

        kpi.setSpacing(
            8
        )

        self.kpi_leads = DealMetric(
            "OPPORTUNITIES",
            "0",
            "TOTAL DISCOVERED",
            QColor(
                55,
                225,
                255,
            ),
        )

        self.kpi_contacted = DealMetric(
            "CONTACTED",
            "0",
            "OUTREACH SENT",
            QColor(
                95,
                155,
                255,
            ),
        )

        self.kpi_replies = DealMetric(
            "REPLIES",
            "0",
            "REPLY RATE 0%",
            QColor(
                140,
                120,
                255,
            ),
        )

        self.kpi_interest = DealMetric(
            "INTERESTED",
            "0",
            "INTEREST RATE 0%",
            QColor(
                190,
                105,
                255,
            ),
        )

        self.kpi_clients = DealMetric(
            "CLOSED",
            "0",
            "CLIENT CONVERSIONS",
            QColor(
                220,
                245,
                255,
            ),
        )

        for widget in (
            self.kpi_leads,
            self.kpi_contacted,
            self.kpi_replies,
            self.kpi_interest,
            self.kpi_clients,
        ):

            kpi.addWidget(
                widget,
                1,
            )

        root.addLayout(
            kpi
        )

        ####################################################
        # CENTER COMMAND AREA
        ####################################################

        center = QHBoxLayout()

        center.setSpacing(
            8
        )

        ####################################################
        # LEFT INTELLIGENCE
        ####################################################

        left_column = QVBoxLayout()

        left_column.setSpacing(
            8
        )

        funnel_panel = HUDPanel(
            "LEAD CONVERSION FUNNEL",
            "PIPELINE",
        )

        funnel = LeadFunnel(
            self.analytics
        )

        funnel_panel.body.addWidget(
            funnel
        )

        left_column.addWidget(
            funnel_panel,
            1,
        )

        category_panel = HUDPanel(
            "MARKET / CATEGORY MATRIX",
            "DISTRIBUTION",
        )

        category_matrix = CategoryMatrix(
            self.analytics
        )

        category_panel.body.addWidget(
            category_matrix
        )

        left_column.addWidget(
            category_panel,
            1,
        )

        ####################################################
        # CORE
        ####################################################

        core_panel = HUDPanel(
            "JARVIS DEAL MATRIX",
            "LIVE",
        )

        self.core = DealIntelligenceCore(
            self.analytics
        )

        core_panel.body.addWidget(
            self.core,
            1,
        )

        ####################################################
        # RIGHT INTELLIGENCE
        ####################################################

        right_column = QVBoxLayout()

        right_column.setSpacing(
            8
        )

        conversion_panel = HUDPanel(
            "CONVERSION INTELLIGENCE",
            "PERFORMANCE",
        )

        self.conversion_label = QLabel(
            "CONTACT → REPLY → INTEREST → CLIENT"
        )

        self.conversion_label.setStyleSheet(
            """
            color:rgba(185,235,245,175);
            font-size:8px;
            letter-spacing:1px;
            background:transparent;
            """
        )

        conversion_panel.body.addWidget(
            self.conversion_label
        )

        self.conversion_graph = ActivityGraph(
            self.analytics
        )

        conversion_panel.body.addWidget(
            self.conversion_graph,
            1,
        )

        right_column.addWidget(
            conversion_panel,
            1,
        )

        activity_panel = HUDPanel(
            "DEAL ACTIVITY",
            "RECENT",
        )

        self.deal_tape = DealTape(
            self.analytics
        )

        activity_panel.body.addWidget(
            self.deal_tape,
            1,
        )

        right_column.addWidget(
            activity_panel,
            1,
        )

        ####################################################
        # PLACE THREE COLUMNS
        ####################################################

        center.addLayout(
            left_column,
            1,
        )

        center.addWidget(
            core_panel,
            2,
        )

        center.addLayout(
            right_column,
            1,
        )

        root.addLayout(
            center,
            1,
        )

        ####################################################
        # BOTTOM STRIP
        ####################################################

        bottom = QHBoxLayout()

        bottom.setSpacing(
            8
        )

        health_panel = HUDPanel(
            "PIPELINE HEALTH",
            "SYSTEM",
        )

        self.health_label = QLabel(
            "ANALYZING"
        )

        self.health_label.setStyleSheet(
            """
            color:#E5FCFF;
            font-size:14px;
            font-weight:bold;
            background:transparent;
            """
        )

        health_panel.body.addWidget(
            self.health_label
        )

        self.health_detail = QLabel(
            "Awaiting outreach data"
        )

        self.health_detail.setStyleSheet(
            """
            color:rgba(175,235,245,165);
            font-size:8px;
            background:transparent;
            """
        )

        health_panel.body.addWidget(
            self.health_detail
        )

        bottom.addWidget(
            health_panel,
            1,
        )

        rejection_panel = HUDPanel(
            "REJECTION MATRIX",
            "FILTERS",
        )

        self.rejection_label = QLabel(
            "WEBSITE 0   |   ESTABLISHED 0   |   SKIPPED 0"
        )

        self.rejection_label.setStyleSheet(
            """
            color:#8DEBFF;
            font-size:9px;
            font-family:Consolas;
            background:transparent;
            """
        )

        rejection_panel.body.addWidget(
            self.rejection_label
        )

        bottom.addWidget(
            rejection_panel,
            1,
        )

        root.addLayout(
            bottom
        )

        ####################################################
        # DATA REFRESH
        ####################################################

        self.refresh_timer = QTimer(
            self
        )

        self.refresh_timer.setInterval(
            1000
        )

        self.refresh_timer.timeout.connect(
            self.refresh_dashboard
        )

        self.refresh_timer.start()

        self.refresh_dashboard()

        ####################################################
        # STYLE
        ####################################################

        self.setStyleSheet(
            """
            #AnalyticsDashboard {
                background:
                    qlineargradient(
                        x1:0,
                        y1:0,
                        x2:1,
                        y2:1,
                        stop:0 #020811,
                        stop:0.45 #041421,
                        stop:1 #020710
                    );
            }

            #HUDPanel {
                background:rgba(3,16,29,235);
                border:1px solid rgba(50,220,250,90);
                border-radius:12px;
            }

            #HUDPanel:hover {
                border:1px solid rgba(80,235,255,155);
            }

            #DealMetric {
                background:rgba(3,15,27,242);
                border:1px solid rgba(55,220,250,82);
                border-radius:10px;
            }

            #DealMetric:hover {
                background:rgba(5,23,39,248);
                border:1px solid rgba(90,235,255,170);
            }
            """
        )

    ########################################################
    # REFRESH DASHBOARD
    ########################################################

    def refresh_dashboard(
        self
    ):

        self.analytics.refresh()

        total = (
            self.analytics.total()
        )

        contacted = (
            self.analytics.contacted()
        )

        replied = (
            self.analytics.replied()
        )

        interested = (
            self.analytics.interested()
        )

        clients = (
            self.analytics.clients()
        )

        reply_rate = (
            self.analytics.reply_rate()
        )

        interest_rate = (
            self.analytics.interest_rate()
        )

        ####################################################
        # KPI
        ####################################################

        self.kpi_leads.set_value(
            f"{total:,}",
            "TOTAL DISCOVERED",
        )

        self.kpi_contacted.set_value(
            f"{contacted:,}",
            "OUTREACH SENT",
        )

        self.kpi_replies.set_value(
            f"{replied:,}",
            f"REPLY RATE {reply_rate:.1f}%",
        )

        self.kpi_interest.set_value(
            f"{interested:,}",
            f"INTEREST RATE {interest_rate:.1f}%",
        )

        self.kpi_clients.set_value(
            f"{clients:,}",
            f"CLOSE RATE {self.analytics.client_rate():.1f}%",
        )

        ####################################################
        # HEALTH
        ####################################################

        if total == 0:

            state = "NO PIPELINE DATA"

        elif contacted == 0:

            state = "DISCOVERY PHASE"

        elif clients > 0:

            state = "CLOSING / REVENUE PHASE"

        elif interested > 0:

            state = "HIGH-VALUE OPPORTUNITIES"

        elif replied > 0:

            state = "ACTIVE CONVERSATIONS"

        else:

            state = "OUTREACH ACTIVE"

        self.health_label.setText(
            state
        )

        self.health_detail.setText(
            f"{total} opportunities  •  "
            f"{contacted} contacted  •  "
            f"{replied} replies  •  "
            f"{interested} interested  •  "
            f"{clients} clients"
        )

        ####################################################
        # REJECTIONS
        ####################################################

        website_rejections = (
            self.analytics.count(
                "REJECTED_WEBSITE"
            )
        )

        established_rejections = (
            self.analytics.count(
                "REJECTED_TOO_ESTABLISHED"
            )
        )

        skipped = (
            self.analytics.skipped()
        )

        self.rejection_label.setText(
            "WEBSITE "
            f"{website_rejections}"
            "   |   ESTABLISHED "
            f"{established_rejections}"
            "   |   SKIPPED "
            f"{skipped}"
        )

        ####################################################
        # CLOCK
        ####################################################

        self.time_label.setText(
            datetime.now().strftime(
                "%H:%M:%S"
            )
        )

        ####################################################
        # RECENT TAPE
        ####################################################

        self.deal_tape.refresh()

        ####################################################
        # REPAINT
        ####################################################

        self.update()