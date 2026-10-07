import math

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QPen


class ArcReactor(QWidget):

    def __init__(self):
        super().__init__()

        self.setMinimumSize(620, 620)

        ##################################################
        # Animation
        ##################################################

        self.outerAngle = 0
        self.middleAngle = 0
        self.innerAngle = 0
        
    ##################################################
    # ENERGY PULSE
    ##################################################

        self.pulse = 0
        
        ##################################################
# AI STATE
##################################################

        self.mode = "IDLE"

        self.rotationMultiplier = 1.0

        self.pulseMultiplier = 1.0

        self.flashFrames = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

    ##################################################

    def animate(self):

    ##################################################
    # ROTATION
    ##################################################

     speed = self.rotationMultiplier

     self.outerAngle += 0.35 * speed
     self.middleAngle -= 0.75 * speed
     self.innerAngle += 1.15 * speed
 
     self.radarAngle = getattr(self, "radarAngle", 0)
     self.radarAngle += 2.2 * speed

     self.nodeAngle = getattr(self, "nodeAngle", 0)
     self.nodeAngle -= 1.6 * speed

     self.holoAngle = getattr(self, "holoAngle", 0)
     self.holoAngle += 0.45 * speed

    ##################################################
    # ENERGY
    ##################################################

     self.pulse += 0.08 * self.pulseMultiplier

     if self.flashFrames > 0:
        self.flashFrames -= 1

     self.update()

    ##################################################

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        center = QPointF(
            self.width() / 2,
            self.height() / 2
        )

        self.drawGlow(painter, center)

        self.drawParticles(painter, center)

        self.drawHoloRings(painter, center)

        self.drawRadarSweep(painter, center)

        self.drawOrbitNodes(painter, center)

        self.drawOuterRing(painter, center)
        
        self.drawMiddleRing(painter, center)

        self.drawInnerRing(painter, center)

        self.drawCore(painter, center)

        painter.end()
        
        ##################################################
    # AI ENERGY GLOW
    ##################################################

    def drawGlow(self, painter, center):

        painter.setPen(Qt.NoPen)

        pulseRadius = math.sin(self.pulse) * 10

        ##################################################
        # OUTER BLOOM
        ##################################################

        for i in range(30):

            alpha = max(0, 18 - i)

            painter.setBrush(

                QColor(

                    0,

                    180,

                    255,

                    alpha

                )

            )

            painter.drawEllipse(

                center,

                305 - i * 8 + pulseRadius,

                305 - i * 8 + pulseRadius

            )

        ##################################################
        # INNER BLOOM
        ##################################################

        for i in range(20):

            alpha = max(0, 65 - i * 3)

            painter.setBrush(

                QColor(

                    120,

                    240,

                    255,

                    alpha

                )

            )

            painter.drawEllipse(

                center,

                120 - i * 3 + pulseRadius * 0.3,

                120 - i * 3 + pulseRadius * 0.3

            )
            
        ##################################################
    # MECHANICAL OUTER RING
    ##################################################

    def drawOuterRing(self, painter, center):

        painter.save()

        painter.translate(center)

        painter.rotate(self.outerAngle)

        ##################################################
        # OUTER GUIDE RING
        ##################################################

        painter.setPen(QPen(QColor(0,210,255,60),1))

        painter.drawEllipse(QPointF(0,0),240,240)

        ##################################################
        # MAIN SEGMENTS
        ##################################################

        segmentPen = QPen(QColor(170,245,255),4)

        painter.setPen(segmentPen)

        for i in range(36):

            painter.drawArc(
                -225,
                -225,
                450,
                450,
                0,
                5*16
            )

            painter.rotate(10)

        ##################################################
        # SECONDARY SEGMENTS
        ##################################################

        painter.setPen(
            QPen(QColor(60,210,255),2)
        )

        for i in range(72):

            painter.drawLine(
                212,
                0,
                225,
                0
            )

            painter.rotate(5)

        ##################################################
        # OUTER MICRO TICKS
        ##################################################

        painter.setPen(
            QPen(QColor(180,255,255,170),1)
        )

        for i in range(180):

            painter.drawLine(
                236,
                0,
                242,
                0
            )

            painter.rotate(2)

        ##################################################
        # LARGE MECHANICAL BLOCKS
        ##################################################

        blockPen = QPen(QColor(110,240,255),6)

        painter.setPen(blockPen)

        for i in range(12):

            painter.drawArc(
                -205,
                -205,
                410,
                410,
                0,
                8*16
            )

            painter.rotate(30)

        painter.restore()

        ##################################################
    # HOLOGRAPHIC MIDDLE RINGS
    ##################################################

    def drawMiddleRing(self, painter, center):

        painter.save()

        painter.translate(center)

        painter.rotate(self.middleAngle)

        ##################################################
        # MAIN HUD RING
        ##################################################

        painter.setPen(
            QPen(
                QColor(0,255,255),
                2
            )
        )

        painter.drawEllipse(
            QPointF(0,0),
            180,
            180
        )

        ##################################################
        # SECOND HUD RING
        ##################################################

        painter.setPen(
            QPen(
                QColor(80,220,255,150),
                1
            )
        )

        painter.drawEllipse(
            QPointF(0,0),
            170,
            170
        )

        painter.drawEllipse(
            QPointF(0,0),
            160,
            160
        )

        painter.drawEllipse(
            QPointF(0,0),
            150,
            150
        )

        ##################################################
        # ROTATING ARC SEGMENTS
        ##################################################

        painter.setPen(
            QPen(
                QColor(170,250,255),
                3
            )
        )

        for i in range(16):

            painter.drawArc(
                -180,
                -180,
                360,
                360,
                0,
                10*16
            )

            painter.rotate(22.5)

        ##################################################
        # SMALL ENERGY BARS
        ##################################################

        painter.setPen(
            QPen(
                QColor(100,235,255),
                2
            )
        )

        for i in range(32):

            painter.drawLine(
                142,
                0,
                160,
                0
            )

            painter.rotate(11.25)

        ##################################################
        # MICRO TICKS
        ##################################################

        painter.setPen(
            QPen(
                QColor(200,255,255,120),
                1
            )
        )

        for i in range(90):

            painter.drawLine(
                174,
                0,
                180,
                0
            )

            painter.rotate(4)

        painter.restore()

        ##################################################
    # MECHANICAL INNER RING
    ##################################################

    def drawInnerRing(self, painter, center):

        painter.save()

        painter.translate(center)

        painter.rotate(self.innerAngle)

        ##################################################
        # INNER GUIDE
        ##################################################

        painter.setPen(
            QPen(
                QColor(40,200,255,120),
                1
            )
        )

        painter.drawEllipse(
            QPointF(0,0),
            120,
            120
        )

        painter.drawEllipse(
            QPointF(0,0),
            108,
            108
        )

        ##################################################
        # MECHANICAL BLADES
        ##################################################

        bladePen = QPen(
            QColor(190,250,255),
            4
        )

        painter.setPen(bladePen)

        for i in range(24):

            painter.drawLine(
                72,
                0,
                110,
                0
            )

            painter.rotate(15)

        ##################################################
        # SMALL GEAR TEETH
        ##################################################

        toothPen = QPen(
            QColor(90,220,255),
            2
        )

        painter.setPen(toothPen)

        for i in range(48):

            painter.drawLine(
                110,
                0,
                120,
                0
            )

            painter.rotate(7.5)

        ##################################################
        # ENERGY NODES
        ##################################################

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor(
                160,
                255,
                255
            )
        )

        for i in range(12):

            painter.drawEllipse(
                QPointF(95,0),
                4,
                4
            )

            painter.rotate(30)

        ##################################################
        # INNER ENERGY RING
        ##################################################

        painter.setPen(
            QPen(
                QColor(0,255,255),
                2
            )
        )

        painter.drawEllipse(
            QPointF(0,0),
            78,
            78
        )

        painter.restore()
        
        ##################################################
    # ENERGY CORE V2
    ##################################################

    def drawCore(self, painter, center):

        painter.save()

        painter.translate(center)

        painter.setPen(Qt.NoPen)

        ##################################################
        # OUTER PLASMA
        ##################################################

        for i in range(14):

            painter.setBrush(
                QColor(
                    0,
                    220,
                    255,
                    18-i
                )
            )

            painter.drawEllipse(
                QPointF(0,0),
                90-i*3,
                90-i*3
            )

        ##################################################
        # ENERGY DISC
        ##################################################

        painter.setBrush(
            QColor(
                0,
                210,
                255,
                120
            )
        )

        painter.drawEllipse(
            QPointF(0,0),
            58,
            58
        )

        ##################################################
        # CONTAINMENT RING
        ##################################################

        painter.setPen(
            QPen(
                QColor(220,255,255),
                2
            )
        )

        painter.setBrush(Qt.NoBrush)

        painter.drawEllipse(
            QPointF(0,0),
            42,
            42
        )

        ##################################################
        # ROTATING ENERGY ARMS
        ##################################################

        painter.save()

        painter.rotate(self.innerAngle*1.8)

        painter.setPen(
            QPen(
                QColor(180,245,255),
                3
            )
        )

        for i in range(8):

            painter.drawLine(
                14,
                0,
                32,
                0
            )

            painter.rotate(45)

        painter.restore()

        ##################################################
        # INNER ENERGY
        ##################################################

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor(
                120,
                240,
                255
            )
        )

        painter.drawEllipse(
            QPointF(0,0),
            18,
            18
        )

        ##################################################
        # WHITE CORE
        ##################################################

        painter.setBrush(
            QColor(
                255,
                255,
                255
            )
        )

        painter.drawEllipse(
            QPointF(0,0),
            8,
            8
        )

        painter.restore()
        
        ##################################################
        # STARK RADAR SWEEP
        ##################################################

    def drawRadarSweep(self, painter, center):

        painter.save()

        painter.translate(center)

        painter.rotate(self.radarAngle)

        painter.setPen(Qt.NoPen)

        ##################################################
        # MAIN SCAN BEAM
        ##################################################

        for i in range(80):

            alpha = max(0, 90 - i)

            painter.setBrush(
                QColor(
                    0,
                    255,
                    255,
                    alpha
                )
            )

            painter.drawPie(
                -225,
                -225,
                450,
                450,
                0,
                2 * 16
            )

            painter.rotate(-0.55)

        ##################################################
        # INNER SCAN
        ##################################################

        for i in range(45):

            alpha = max(0, 70 - i)

            painter.setBrush(
                QColor(
                    120,
                    255,
                    255,
                    alpha
                )
            )

            painter.drawPie(
                -165,
                -165,
                330,
                330,
                0,
                3 * 16
            )

            painter.rotate(-0.65)

        ##################################################
        # BRIGHT LEADING EDGE
        ##################################################

        painter.setPen(
            QPen(
                QColor(220,255,255),
                3
            )
        )

        painter.drawLine(
            0,
            0,
            225,
            0
        )

        painter.restore()
        
        ##################################################
        # ORBITING ENERGY SATELLITES
        ##################################################

    def drawOrbitNodes(self, painter, center):

        painter.save()

        painter.translate(center)

        painter.rotate(self.nodeAngle)

        painter.setPen(Qt.NoPen)

        orbitData = [

            (95,4,QColor(220,255,255)),

            (135,5,QColor(120,245,255)),

            (175,6,QColor(0,210,255))

        ]

        for radius,size,color in orbitData:

            painter.save()

            ##################################################
            # TRAILS
            ##################################################

            for trail in range(18):

                alpha=max(0,80-trail*5)

                painter.setBrush(

                    QColor(

                        color.red(),

                        color.green(),

                        color.blue(),

                        alpha

                    )

                )

                painter.drawEllipse(

                    QPointF(radius,0),

                    size-trail*0.15,

                    size-trail*0.15

                )

                painter.rotate(-2.4)

            ##################################################
            # MAIN SATELLITE
            ##################################################

            painter.setBrush(color)

            painter.drawEllipse(

                QPointF(radius,0),

                size,

                size

            )

            ##################################################
            # REPEAT AROUND RING
            ##################################################

            painter.rotate(60)

            painter.setBrush(color)

            painter.drawEllipse(

                QPointF(radius,0),

                size,

                size

            )

            painter.rotate(60)

            painter.drawEllipse(

                QPointF(radius,0),

                size,

                size

            )

            painter.rotate(60)

            painter.drawEllipse(

                QPointF(radius,0),

                size,

                size

            )

            painter.rotate(60)

            painter.drawEllipse(

                QPointF(radius,0),

                size,

                size

            )

            painter.rotate(60)

            painter.drawEllipse(

                QPointF(radius,0),

                size,

                size

            )

            painter.restore()

        painter.restore()
        
        ##################################################
        # ENERGY PARTICLES
        ##################################################

    def drawParticles(self, painter, center):

        painter.save()

        painter.translate(center)

        painter.setPen(Qt.NoPen)

        for ring in range(8):

            radius = 120 + ring * 22

            for i in range(24):

                angle = math.radians(i * 15 + ring * 8 + self.outerAngle)

                x = math.cos(angle) * radius
                y = math.sin(angle) * radius

                alpha = 30 + (ring * 8)

                size = 1.5 + ring * 0.25

                painter.setBrush(
                    QColor(
                        120,
                        240,
                        255,
                        alpha
                    )
                )

                painter.drawEllipse(
                    QPointF(x, y),
                    size,
                    size
                )

        painter.restore()
        
            ##################################################
    # FLOATING HOLOGRAPHIC RINGS
    ##################################################

    def drawHoloRings(self, painter, center):

        painter.save()

        painter.translate(center)

        painter.rotate(self.holoAngle)

        rings = [

            (255, QColor(0,210,255,30), 1),

            (265, QColor(80,230,255,35), 1),

            (275, QColor(140,245,255,40), 2)

        ]

        for radius, color, width in rings:

            painter.setPen(
                QPen(
                    color,
                    width
                )
            )

            for i in range(18):

                painter.drawArc(

                    -radius,

                    -radius,

                    radius*2,

                    radius*2,

                    0,

                    9*16

                )

                painter.rotate(20)

        ##################################################

        painter.setPen(

            QPen(

                QColor(180,255,255,70),

                1

            )

        )

        for i in range(72):

            painter.drawLine(

                248,

                0,

                255,

                0

            )

            painter.rotate(5)

        painter.restore()
        
        ##################################################
        # AI STATE
        ##################################################

    def setState(self, state):

        state = str(state).upper()

        self.mode = state

        ##################################################
        # IDLE
        ##################################################

        if state == "IDLE":

            self.rotationMultiplier = 0.8
            self.pulseMultiplier = 1.0

        ##################################################
        # LISTENING
        ##################################################

        elif state == "LISTENING":

            self.rotationMultiplier = 1.2
            self.pulseMultiplier = 1.6

        ##################################################
        # THINKING
        ##################################################

        elif state == "THINKING":

            self.rotationMultiplier = 2.5
            self.pulseMultiplier = 2.0

        ##################################################
        # EXECUTING
        ##################################################

        elif state == "EXECUTING":

            self.rotationMultiplier = 4.0
            self.pulseMultiplier = 3.0

        ##################################################
        # COMPLETED
        ##################################################

        elif state == "COMPLETED":

            self.rotationMultiplier = 1.0
            self.pulseMultiplier = 2.5

            self.flashFrames = 15

        ##################################################
        # ERROR
        ##################################################

        elif state == "ERROR":

            self.rotationMultiplier = 0.3
            self.pulseMultiplier = 0.5

        ##################################################
        # UNKNOWN STATE
        ##################################################

        else:

            self.rotationMultiplier = 0.8
            self.pulseMultiplier = 1.0

        ##################################################
        # IMMEDIATE VISUAL UPDATE
        ##################################################

        self.update()