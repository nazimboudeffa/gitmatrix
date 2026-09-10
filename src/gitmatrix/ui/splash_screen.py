"""Splash screen Matrix Rain pour le lancement de GitMatrix."""

from __future__ import annotations

import random

from PySide6.QtCore import QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QSplashScreen, QApplication

KATAKANA = (
    "ア イ ウ エ オ カ キ ク ケ コ サ シ ス セ ソ "
    "タ チ ツ テ ト ナ ニ ヌ ネ ノ ハ ヒ フ ヘ ホ "
    "マ ミ ム メ モ ヤ ユ ヨ ラ リ ル レ ロ ワ ヰ "
    "ヱ ヲ ン ァ ィ ァ ェ ォ ッ"
)
CHARS = KATAKANA.split() + list("0123456789ABCDEF") + list("gitmatrix")

BG_COLOR = QColor("#0d0d0d")
HEAD_COLOR = QColor("#00ff41")
TITLE_COLOR = QColor("#e5c07b")
SUBTITLE_COLOR = QColor("#9da5b4")
PROGRESS_BG = QColor(40, 40, 40)

COL_SPACING = 22
FPS_MS = 50

BTN_W = 180
BTN_H = 44
BTN_RADIUS = 8


class _Column:
    """Une colonne de caractères qui défile."""

    __slots__ = ("x", "y", "speed", "chars", "length")

    def __init__(self, x: int, height: int) -> None:
        self.x = x
        self.y = random.randint(-height, 0)
        self.speed = random.randint(2, 6)
        self.length = random.randint(8, 22)
        self.chars = [random.choice(CHARS) for _ in range(self.length)]

    def tick(self, height: int) -> None:
        self.y += self.speed
        if self.y - self.length * COL_SPACING > height:
            self.y = random.randint(-height // 2, 0)
            self.speed = random.randint(2, 6)
            self.length = random.randint(8, 22)
            self.chars = [random.choice(CHARS) for _ in range(self.length)]
        if random.random() < 0.15:
            idx = random.randint(0, self.length - 1)
            self.chars[idx] = random.choice(CHARS)


class MatrixRainSplash(QSplashScreen):
    """Splash screen avec animation Matrix Rain et logo GitMatrix.

    La progression est pilotée par ``set_progress(fraction, text)`` depuis
    l'extérieur (app.py).  À 100 %, un bouton « Lancer » apparaît ;
    le splash ne se ferme qu'au clic dessus.
    """

    launched = Signal()

    def __init__(self) -> None:
        self._progress = 0.0
        self._status = "Initialisation\u2026"
        self._ready = False
        self._btn_rect = QRect()

        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()
        w, h = geo.width(), geo.height()

        pixmap = QPixmap(w, h)
        pixmap.fill(BG_COLOR)
        super().__init__(pixmap)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self._cols: list[_Column] = []
        n_cols = w // COL_SPACING + 1
        for i in range(n_cols):
            self._cols.append(_Column(i * COL_SPACING, h))

        self._font = QFont("Consolas")
        self._font.setPixelSize(14)

        self._title_font = QFont("Cascadia Mono, Consolas, monospace")
        self._title_font.setPixelSize(48)
        self._title_font.setBold(True)

        self._sub_font = QFont("Cascadia Mono, Consolas, monospace")
        self._sub_font.setPixelSize(16)

        self._status_font = QFont("Cascadia Mono, Consolas, monospace")
        self._status_font.setPixelSize(11)

        self._btn_font = QFont("Cascadia Mono, Consolas, monospace")
        self._btn_font.setPixelSize(14)
        self._btn_font.setBold(True)

        self._hovering = False
        self.setMouseTracking(True)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(FPS_MS)

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------
    def set_progress(self, fraction: float, text: str = "") -> None:
        """Met à jour la gauge (0.0 → 1.0) et le texte de statut."""
        self._progress = min(1.0, max(0.0, fraction))
        if text:
            self._status = text
        if self._progress >= 1.0 and not self._ready:
            self._ready = True
            self._status = "Prêt"
        self._tick()

    # ------------------------------------------------------------------
    # Événements
    # ------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:  # noqa: N802
        if self._ready and self._btn_rect.contains(event.position().toPoint()):
            self._timer.stop()
            self.launched.emit()
            self.close()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._ready:
            was = self._hovering
            self._hovering = self._btn_rect.contains(event.position().toPoint())
            if was != self._hovering:
                self._tick()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        if self._hovering:
            self._hovering = False
            self._tick()
        super().leaveEvent(event)

    # ------------------------------------------------------------------
    # Rendu
    # ------------------------------------------------------------------
    def _tick(self) -> None:
        geo = self.geometry()
        w, h = geo.width(), geo.height()

        for col in self._cols:
            col.tick(h)

        pixmap = QPixmap(w, h)
        pixmap.fill(BG_COLOR)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        painter.setFont(self._font)
        for col in self._cols:
            for i, ch in enumerate(col.chars):
                cy = col.y - i * COL_SPACING
                if cy < -COL_SPACING or cy > h + COL_SPACING:
                    continue
                if i == 0:
                    painter.setPen(QColor(0, 255, 65, 255))
                elif i < 3:
                    painter.setPen(QColor(0, 255, 65, max(0, 255 - i * 60)))
                else:
                    painter.setPen(QColor(0, 200, 50, max(0, 180 - i * 12)))
                painter.drawText(col.x, cy, ch)

        painter.setPen(TITLE_COLOR)
        painter.setFont(self._title_font)
        painter.drawText(
            QRect(0, h // 2 - 60, w, 60),
            Qt.AlignmentFlag.AlignCenter,
            "GitMatrix",
        )

        painter.setPen(SUBTITLE_COLOR)
        painter.setFont(self._sub_font)
        painter.drawText(
            QRect(0, h // 2 + 10, w, 30),
            Qt.AlignmentFlag.AlignCenter,
            "Client Git visuel",
        )

        bar_w = 200
        bar_h = 3
        bx = (w - bar_w) // 2
        by = h // 2 + 55
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(PROGRESS_BG)
        painter.drawRoundedRect(bx, by, bar_w, bar_h, 1, 1)
        painter.setBrush(HEAD_COLOR)
        painter.drawRoundedRect(bx, by, int(bar_w * self._progress), bar_h, 1, 1)

        if self._ready:
            self._paint_button(painter, w, h)
        else:
            painter.setPen(QColor(0, 255, 65, 180))
            painter.setFont(self._status_font)
            painter.drawText(
                QRect(0, h // 2 + 68, w, 20),
                Qt.AlignmentFlag.AlignCenter,
                self._status,
            )

        painter.end()
        self.setPixmap(pixmap)

    def _paint_button(self, painter: QPainter, w: int, h: int) -> None:
        bx = (w - BTN_W) // 2
        by = h // 2 + 70
        self._btn_rect = QRect(bx, by, BTN_W, BTN_H)

        glow = QColor(0, 255, 65, 20 if self._hovering else 12)
        for i in range(3, 0, -1):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            r = BTN_RADIUS + i * 3
            painter.drawRoundedRect(
                QRectF(bx - i * 3, by - i * 3, BTN_W + i * 6, BTN_H + i * 6),
                r, r,
            )

        path = QPainterPath()
        path.addRoundedRect(QRectF(bx, by, BTN_W, BTN_H), BTN_RADIUS, BTN_RADIUS)

        btn_fill = QColor(30, 35, 42) if not self._hovering else QColor(38, 44, 52)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(btn_fill)
        painter.drawPath(path)

        border_alpha = 160 if self._hovering else 100
        painter.setPen(QPen(QColor(0, 255, 65, border_alpha), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(
            QRectF(bx + 1, by + 1, BTN_W - 2, BTN_H - 2),
            BTN_RADIUS, BTN_RADIUS,
        )

        text_alpha = 220 if self._hovering else 170
        painter.setPen(QColor(0, 255, 65, text_alpha))
        painter.setFont(self._btn_font)
        painter.drawText(
            QRect(bx, by + 2, BTN_W, BTN_H),
            Qt.AlignmentFlag.AlignCenter,
            "\u25b6  LANCER",
        )

        hint_color = QColor(0, 255, 65, 100) if self._hovering else QColor(0, 255, 65, 60)
        painter.setPen(hint_color)
        painter.setFont(self._status_font)
        painter.drawText(
            QRect(0, by + BTN_H + 14, w, 20),
            Qt.AlignmentFlag.AlignCenter,
            "Cliquez pour continuer",
        )
