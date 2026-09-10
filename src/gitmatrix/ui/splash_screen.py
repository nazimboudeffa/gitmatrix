"""Splash screens de GitMatrix — écran de lancement avec pluie de caractères.

Système de variantes configurées par JSON (``assets/splashscreens`` et
``~/.gitmatrix/splashscreens``).  Le moteur de rendu est générique :
couleurs, jeu de caractères, densité et vitesse de la pluie sont pilotés
par la configuration, ce qui permet aux utilisateurs de créer leurs
propres splash screens sans toucher au code.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QPoint, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QSplashScreen, QApplication

CHAR_SETS: Dict[str, str] = {
    "katakana": (
        "ア イ ウ エ オ カ キ ク ケ コ サ シ ス セ ソ "
        "タ チ ツ テ ト ナ ニ ヌ ネ ノ ハ ヒ フ ヘ ホ "
        "マ ミ ム メ モ ヤ ユ ヨ ラ リ ル レ ロ ワ ヰ "
        "ヱ ヲ ン ァ ィ ァ ェ ォ ッ"
    ),
    "hex": "0123456789ABCDEF",
    "latin": "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "binary": "01",
}

DEFAULT_SPLASH = "matrix-rain"

BTN_W = 180
BTN_H = 44
BTN_RADIUS = 8


@dataclass
class SplashConfig:
    """Paramètres visuels d'un splash screen."""

    name: str
    background: str = "#0d0d0d"
    char_set: str = "katakana"          # clé de CHAR_SETS ou chaîne littérale
    head_color: str = "#00ff41"         # tête des colonnes (pleine opacité)
    body_color: str = "#00c832"         # base du dégradé des corps
    title: str = "GitMatrix"
    title_color: str = "#e5c07b"
    subtitle: str = "Client Git visuel"
    subtitle_color: str = "#9da5b4"
    message: str = ""                   # phrase horizontale écrite avec contraste
    status_color: str = "#00ff41"
    button_text: str = "LANCER"
    button_fill: str = "#1e232a"
    button_fill_hover: str = "#262c34"
    button_border: str = "#00ff41"
    button_text_color: str = "#00ff41"
    hint_text: str = "Cliquez pour continuer"
    hint_color: str = "#00ff41"
    density: float = 1.0
    speed_min: int = 2
    speed_max: int = 6
    length_min: int = 8
    length_max: int = 22
    col_spacing: int = 22
    font_size: int = 14
    fps_ms: int = 50

    def characters(self) -> List[str]:
        if self.char_set in CHAR_SETS:
            src = CHAR_SETS[self.char_set]
            return src.split() if " " in src else list(src)
        return list(self.char_set)

    def col_spacing_effective(self) -> int:
        return max(1, int(self.col_spacing * (1.0 / max(0.1, self.density))))


def load_splash_config(name: str) -> SplashConfig:
    """Charge la configuration d'un splash depuis prédéfinis/utilisateur."""
    for d in _splash_dirs():
        candidate = d / f"{name}.json"
        if candidate.is_file():
            data = json.loads(candidate.read_text(encoding="utf-8"))
            keys = dict(SplashConfig.__dataclass_fields__)
            cfg = SplashConfig(name=data.get("name", name))
            for k, v in data.items():
                if k == "name":
                    continue
                if k in keys:
                    setattr(cfg, k, v)
            return cfg
    raise FileNotFoundError(f"Splash introuvable : {name}")


def list_splashes() -> List[str]:
    """Noms des splash screens disponibles (prédéfinis puis utilisateur)."""
    names: List[str] = []
    for d in _splash_dirs():
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.json")):
            if p.stem not in names:
                names.append(p.stem)
    return names


def _splash_dirs() -> List[Path]:
    bundled = Path(__file__).resolve().parent.parent / "assets" / "splashscreens"
    user = Path.home() / ".gitmatrix" / "splashscreens"
    dirs: List[Path] = []
    if bundled.is_dir():
        dirs.append(bundled)
    dirs.append(user)
    return dirs


def create_splash(name: str = "") -> "MatrixRainSplash":
    """Fabrique un splash screen par son nom (défaut si vide)."""
    chosen = name or DEFAULT_SPLASH
    config = load_splash_config(chosen)
    return MatrixRainSplash(config)


class _Column:
    """Une colonne de caractères qui défile."""

    __slots__ = ("x", "y", "speed", "chars", "length")

    def __init__(self, x: int, height: int, cfg: SplashConfig) -> None:
        self.x = x
        self.y = random.randint(-height, 0)
        self.speed = random.randint(cfg.speed_min, cfg.speed_max)
        self.length = random.randint(cfg.length_min, cfg.length_max)
        chars = cfg.characters()
        self.chars = [random.choice(chars) for _ in range(self.length)]

    def tick(self, height: int, cfg: SplashConfig) -> None:
        self.y += self.speed
        spacing = cfg.col_spacing_effective()
        if self.y - self.length * spacing > height:
            self.y = random.randint(-height // 2, 0)
            self.speed = random.randint(cfg.speed_min, cfg.speed_max)
            self.length = random.randint(cfg.length_min, cfg.length_max)
            chars = cfg.characters()
            self.chars = [random.choice(chars) for _ in range(self.length)]
        if random.random() < 0.15:
            chars = cfg.characters()
            idx = random.randint(0, self.length - 1)
            self.chars[idx] = random.choice(chars)


class MatrixRainSplash(QSplashScreen):
    """Splash screen à pluie de caractères, piloté par ``SplashConfig``.

    La progression est contrôlée par ``set_progress(fraction, text)`` depuis
    l'extérieur.  À 100 %, un bouton « Lancer » apparaît ; le splash ne se
    ferme qu'au clic dessus (signal ``launched``).
    """

    launched = Signal()

    def __init__(self, config: Optional[SplashConfig] = None) -> None:
        self.cfg = config or SplashConfig(name=DEFAULT_SPLASH)
        self._progress = 0.0
        self._status = "Initialisation\u2026"
        self._ready = False
        self._btn_rect = QRect()
        self._hovering = False

        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()
        w, h = geo.width(), geo.height()

        pixmap = QPixmap(w, h)
        pixmap.fill(QColor(self.cfg.background))
        super().__init__(pixmap)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMouseTracking(True)

        spacing = self.cfg.col_spacing_effective()
        n_cols = w // spacing + 1
        self._cols: List[_Column] = [
            _Column(i * spacing, h, self.cfg) for i in range(n_cols)
        ]

        self._font = QFont("Consolas")
        self._font.setPixelSize(self.cfg.font_size)

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

        self._typed = 0          # nb de caractères du message décryptés
        self._msg_ticks = 0      # compteur de la vitesse de décryptage

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(self.cfg.fps_ms)

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
        cfg = self.cfg
        geo = self.geometry()
        w, h = geo.width(), geo.height()
        spacing = cfg.col_spacing_effective()

        for col in self._cols:
            col.tick(h, cfg)

        if cfg.message:
            self._tick_message()

        pixmap = QPixmap(w, h)
        pixmap.fill(QColor(cfg.background))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        head = QColor(cfg.head_color)
        body = QColor(cfg.body_color)

        painter.setFont(self._font)
        for col in self._cols:
            for i, ch in enumerate(col.chars):
                cy = col.y - i * spacing
                if cy < -spacing or cy > h + spacing:
                    continue
                if i == 0:
                    painter.setPen(QColor(head.red(), head.green(), head.blue(), 255))
                elif i < 3:
                    alpha = max(0, 255 - i * 60)
                    painter.setPen(QColor(head.red(), head.green(), head.blue(), alpha))
                else:
                    alpha = max(0, 180 - i * 12)
                    painter.setPen(QColor(body.red(), body.green(), body.blue(), alpha))
                painter.drawText(col.x, cy, ch)

        painter.setPen(QColor(cfg.title_color))
        painter.setFont(self._title_font)
        painter.drawText(
            QRect(0, h // 2 - 60, w, 60),
            Qt.AlignmentFlag.AlignCenter,
            cfg.title,
        )

        painter.setPen(QColor(cfg.subtitle_color))
        painter.setFont(self._sub_font)
        painter.drawText(
            QRect(0, h // 2 + 10, w, 30),
            Qt.AlignmentFlag.AlignCenter,
            cfg.subtitle,
        )

        bar_w = 200
        bar_h = 3
        bx = (w - bar_w) // 2
        by = h // 2 + 55
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(40, 40, 40))
        painter.drawRoundedRect(bx, by, bar_w, bar_h, 1, 1)
        painter.setBrush(head)
        painter.drawRoundedRect(bx, by, int(bar_w * self._progress), bar_h, 1, 1)

        if self._ready:
            self._paint_button(painter, w, h)
        else:
            painter.setPen(QColor(cfg.status_color))
            painter.setFont(self._status_font)
            painter.drawText(
                QRect(0, h // 2 + 68, w, 20),
                Qt.AlignmentFlag.AlignCenter,
                self._status,
            )

        if cfg.message:
            self._paint_message(painter, w, h)

        painter.end()
        self.setPixmap(pixmap)

    def _tick_message(self) -> None:
        """Avance le décryptage de la phrase (de gauche à droite)."""
        self._msg_ticks += 1
        if self._typed >= len(self.cfg.message):
            return
        if self._msg_ticks % 3 == 0:
            self._typed += 1

    def _paint_message(self, painter: QPainter, w: int, h: int) -> None:
        """Dessine la phrase qui se décrypte, en haut à gauche."""
        cfg = self.cfg
        msg = cfg.message
        painter.setFont(self._font)
        fm = painter.fontMetrics()

        step = cfg.col_spacing_effective()  # même espacement que les colonnes
        left = int(w * 0.08)
        base_y = int(h * 0.10) + fm.ascent()

        head = QColor(cfg.head_color)
        body = QColor(cfg.body_color)
        chips = cfg.characters()

        for i, target in enumerate(msg):
            x = left + i * step
            if i < self._typed:
                # lettre décryptée : nette, contrastée, avec un léger halo
                painter.setPen(QColor(head.red(), head.green(), head.blue(), 60))
                painter.drawText(QPoint(x + 1, base_y + 1), target)
                painter.setPen(QColor(head.red(), head.green(), head.blue(), 255))
                painter.drawText(QPoint(x, base_y), target)
            elif i == self._typed:
                # caractère en cours de résolution : glyphes qui clignotent
                painter.setPen(QColor(head.red(), head.green(), head.blue(), 255))
                painter.drawText(QPoint(x, base_y), random.choice(chips))
            else:
                # texte encore chiffré : glyphes faiblement visible
                painter.setPen(QColor(body.red(), body.green(), body.blue(), 80))
                painter.drawText(QPoint(x, base_y), random.choice(chips))

    def _paint_button(self, painter: QPainter, w: int, h: int) -> None:
        cfg = self.cfg
        bx = (w - BTN_W) // 2
        by = h // 2 + 70
        self._btn_rect = QRect(bx, by, BTN_W, BTN_H)

        border = QColor(cfg.button_border)
        glow = QColor(border.red(), border.green(), border.blue(), 20 if self._hovering else 12)
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

        fill = QColor(cfg.button_fill_hover if self._hovering else cfg.button_fill)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        painter.drawPath(path)

        border_alpha = 160 if self._hovering else 100
        painter.setPen(QPen(QColor(border.red(), border.green(), border.blue(), border_alpha), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(bx + 1, by + 1, BTN_W - 2, BTN_H - 2), BTN_RADIUS, BTN_RADIUS)

        txt = QColor(cfg.button_text_color)
        text_alpha = 220 if self._hovering else 170
        painter.setPen(QColor(txt.red(), txt.green(), txt.blue(), text_alpha))
        painter.setFont(self._btn_font)
        painter.drawText(
            QRect(bx, by + 2, BTN_W, BTN_H),
            Qt.AlignmentFlag.AlignCenter,
            f"\u25b6  {cfg.button_text}",
        )

        hint = QColor(cfg.hint_color)
        hint_alpha = 100 if self._hovering else 60
        painter.setPen(QColor(hint.red(), hint.green(), hint.blue(), hint_alpha))
        painter.setFont(self._status_font)
        painter.drawText(
            QRect(0, by + BTN_H + 14, w, 20),
            Qt.AlignmentFlag.AlignCenter,
            cfg.hint_text,
        )