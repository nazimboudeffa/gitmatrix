"""Thèmes de GitMatrix.

Système de thèmes enrichi (tokens + QSS) :

* Un thème est défini par un fichier JSON ``{name, tokens, palette, qss}``.
* Les thèmes sont chargés depuis ::

    - ``assets/themes``      (thèmes prédéfinis fournis avec l'app)
    - ``~/.gitmatrix/themes``(thèmes ajoutés par l'utilisateur)

* Les tokens sont interpolés dans un template QSS : un utilisateur peut
  n'écraser qu'une partie des couleurs.  Le champ ``qss`` permet de
  fournir une feuille de style complète (remplace le template).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# Compatibilité QSettings : organisation définie dans app.py.
from PySide6.QtCore import QSettings

# ---------------------------------------------------------------------------
# Tokens par défaut — le « contrat » du template QSS.
# ---------------------------------------------------------------------------
DEFAULT_TOKENS: Dict[str, str] = {
    "bg": "#1e2127",              # fond principal
    "surface": "#22252b",         # panneaux / toolbar / statusbar
    "surface_hover": "#2d3138",   # survol toolbar, boutons, chips
    "surface_pressed": "#262a31", # pressé / chips / items
    "widget_hover": "#373c44",    # survol des boutons poussoirs
    "border": "#3a3f46",          # hairlines
    "border_soft": "#32363e",     # bordures des zones d'édition
    "border_hover": "#4a5058",    # hover scrollbar / boutons
    "input_bg": "#2a2e35",        # QLineEdit, splits
    "selection": "#2f4f6f",       # sélection de liste / menus
    "fg": "#d7dae0",              # texte principal
    "muted": "#9da5b4",           # texte secondaire
    "faint": "#6b7381",           # texte désactivé / auteur de commit
    "accent": "#e5c07b",          # accent doré (action primaire)
    "accent_hover": "#d4b06e",    # hover de l'accent
    "accent_pressed": "#c9a565",  # pressé de l'accent
    "accent_fg": "#1f2228",       # texte sur fond accent
    "danger": "#e06c75",          # actions dangereuses
    "focus": "#61afef",           # bordure de focus
    "white": "#ffffff",           # texte sur sélection / badges
    "warn": "#d19a66",            # chip « dirty », unstaged
}

DEFAULT_PALETTE: List[str] = [
    "#e06c75",  # rouge
    "#61afef",  # bleu
    "#98c379",  # vert
    "#e5c07b",  # jaune
    "#c678dd",  # violet
    "#56b6c2",  # cyan
    "#d19a66",  # orange
    "#ff7eb6",  # rose
    "#6c8cff",  # indigo
    "#7bd88f",  # vert clair
]

# Contribution minimale pour un thème personnalisé utile.
MINIMAL_TOKENS = {"bg", "fg", "accent", "palette"}


def render_qss(tokens: Dict[str, str]) -> str:
    """Génère la feuille de style QSS depuis le contrat de tokens."""
    merged = {**DEFAULT_TOKENS, **tokens}
    qss = _QSS_TEMPLATE
    for key, value in merged.items():
        qss = qss.replace("{" + key + "}", value)
    return qss


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class Theme:
    """Un thème GitMatrix."""

    name: str
    tokens: Dict[str, str] = field(default_factory=dict)
    palette: List[str] = field(default_factory=list)
    qss: Optional[str] = None

    def stylesheet(self) -> str:
        if self.qss:
            return self.qss
        return render_qss(self.tokens)

    def color(self, token: str, fallback: Optional[str] = None) -> str:
        return self.tokens.get(token, fallback or DEFAULT_TOKENS.get(token, ""))


# ---------------------------------------------------------------------------
# Emplacements des thèmes
# ---------------------------------------------------------------------------
BUNDLED_THEMES_DIR = Path(__file__).resolve().parent / "assets" / "themes"
USER_THEMES_DIR = Path.home() / ".gitmatrix" / "themes"

DEFAULT_THEME = "nightfall"


def theme_dirs() -> List[Path]:
    dirs: List[Path] = []
    if BUNDLED_THEMES_DIR.is_dir():
        dirs.append(BUNDLED_THEMES_DIR)
    dirs.append(USER_THEMES_DIR)
    return dirs


def list_themes() -> List[str]:
    """Noms des thèmes disponibles (prédéfinis puis utilisateur, dédupliqués)."""
    names: List[str] = []
    for d in theme_dirs():
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.json")):
            name = p.stem
            if name not in names:
                names.append(name)
    return names


def load_theme(name: str) -> Theme:
    """Charge un thème par son nom depuis les dossiers prédéfinis/utilisateur."""
    for d in theme_dirs():
        candidate = d / f"{name}.json"
        if candidate.is_file():
            data = json.loads(candidate.read_text(encoding="utf-8"))
            return Theme(
                name=data.get("name", name),
                tokens=data.get("tokens", {}),
                palette=data.get("palette", []),
                qss=data.get("qss"),
            )
    raise FileNotFoundError(f"Thème introuvable : {name}")


# ---------------------------------------------------------------------------
# État actif + persistance (QSettings)
# ---------------------------------------------------------------------------
_ACTIVE: Optional[Theme] = None


# ---------------------------------------------------------------------------
# Template QSS (le « contrat » référencé par les tokens)
# ---------------------------------------------------------------------------
_QSS_TEMPLATE = """
QMainWindow, QWidget {
    background-color: {bg};
    color: {fg};
    font-size: 13px;
}

QToolBar {
    background-color: {surface};
    border-bottom: 1px solid {border};
    padding: 4px;
    spacing: 4px;
}
QToolBar QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 5px 11px;
    color: {fg};
    font-weight: 500;
}
QToolBar QToolButton:hover {
    background-color: {surface_hover};
    border-color: {border};
}
QToolBar QToolButton:pressed {
    background-color: {surface_pressed};
}
QToolBar QToolButton:disabled {
    color: {faint};
}

/* Bouton d'action primaire (Commit) dans la toolbar — accent doré */
QToolBar QToolButton#ActionCommit {
    background-color: {accent};
    border-color: {accent};
    color: {accent_fg};
    font-weight: 600;
    padding: 5px 16px;
}
QToolBar QToolButton#ActionCommit:hover {
    background-color: {accent_hover};
    border-color: {accent_hover};
}
QToolBar QToolButton#ActionCommit:pressed {
    background-color: {accent_pressed};
}
QToolBar QToolButton#ActionDanger {
    color: {danger};
}

/* Bouton de branche courant (sélecteur) dans la toolbar */
QToolBar QToolButton#ActionBranch {
    background-color: {surface_hover};
    border-color: {border};
    font-weight: 600;
}
QToolBar QToolButton#ActionBranch:hover {
    border-color: {muted};
}

/* Bouton Settings (menu déroulant engrenage) à droite de la toolbar */
QToolBar QToolButton#ActionSettings {
    color: {fg};
    font-weight: 500;
}
QToolBar QToolButton#ActionSettings:hover {
    background-color: {surface_hover};
    border-color: {border};
}
QToolBar QToolButton#ActionSettings:pressed {
    background-color: {surface_pressed};
}

QToolBar QToolButton::menu-indicator {
    image: none;
}

QTreeWidget, QListWidget, QPlainTextEdit {
    background-color: {surface};
    border: 1px solid {border_soft};
    border-radius: 4px;
    padding: 4px;
    selection-background-color: {selection};
    selection-color: {white};
}
QTreeWidget::item, QListWidget::item {
    border-radius: 3px;
}
QTreeWidget::item:hover, QListWidget::item:hover {
    background-color: {surface_pressed};
}

QSplitter::handle {
    background-color: {input_bg};
    width: 6px;
    height: 6px;
}
QSplitter::handle:hover {
    background-color: {border};
}

QStatusBar {
    background-color: {surface};
    color: {muted};
    border-top: 1px solid {border_soft};
}

QInputDialog, QInputDialog QLabel {
    background-color: {surface};
    color: {fg};
}

QMessageBox, QMessageBox QLabel {
    background-color: {surface};
    color: {fg};
}

QLineEdit {
    background-color: {input_bg};
    border: 1px solid {border};
    border-radius: 4px;
    padding: 5px 8px;
    color: {fg};
    selection-background-color: {selection};
}
QLineEdit:focus {
    border-color: {focus};
}

QDialog {
    background-color: {surface};
}

QPushButton {
    background-color: {surface_hover};
    border: 1px solid {border};
    border-radius: 4px;
    padding: 7px 16px;
    color: {fg};
    font-weight: 500;
}
QPushButton:hover {
    background-color: {widget_hover};
    border-color: {border_hover};
}
QPushButton:pressed {
    background-color: {surface_pressed};
}
QPushButton:disabled {
    color: {faint};
    background-color: {surface_pressed};
}
/* Bouton primaire (Committer) */
QPushButton[accent="true"] {
    background-color: {accent};
    border-color: {accent};
    color: {accent_fg};
    font-weight: 600;
}
QPushButton[accent="true"]:hover {
    background-color: {accent_hover};
    border-color: {accent_hover};
}

QLabel#PanelTitle {
    font-weight: 600;
    color: {muted};
    background-color: transparent;
    border: none;
    padding: 4px 2px;
    font-size: 12px;
    letter-spacing: 0.03em;
}

QMenu {
    background-color: {surface};
    border: 1px solid {border};
    padding: 4px;
}
QMenu::item {
    padding: 6px 22px;
    border-radius: 3px;
}
QMenu::item:selected {
    background-color: {selection};
    color: {white};
}
QMenu::item:disabled {
    color: {faint};
}

QScrollBar:vertical {
    background: {bg};
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: {border};
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: {border_hover};
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* Tooltip natif */
QToolTip {
    background-color: {surface_hover};
    color: {fg};
    border: 1px solid {border};
    padding: 6px 10px;
}

/* En-tête de panneau mono majuscules (façon maquette) */
QLabel#PanelHeaderMono {
    font-family: "Cascadia Mono", "JetBrains Mono", "Consolas", monospace;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: {muted};
    background-color: transparent;
    border: none;
    padding: 10px 14px 8px;
    border-bottom: 1px solid {border_soft};
}

/* Compteur dans un en-tête (pastille arrondie) */
QLabel#HeaderCount {
    background-color: {surface_hover};
    color: {muted};
    border-radius: 8px;
    padding: 1px 7px;
    font-size: 10px;
    font-family: "Cascadia Mono", "JetBrains Mono", "Consolas", monospace;
}

/* Status bar : texte principal */
QStatusBar QLabel#StatusBarText {
    color: {muted};
    font-size: 12px;
    background-color: transparent;
}

/* Status bar : chip (branche / staged / unstaged) */
QLabel#StatusChip {
    background-color: {surface_pressed};
    border: 1px solid {border_soft};
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
}
QLabel#StatusChip[chip="branch"] {
    color: {accent};
    font-weight: 600;
}
QLabel#StatusChip[chip="dirty"] {
    color: {warn};
}

/* Pastille ronde dans les chips de la status bar */
QLabel#StatusDot {
    background-color: transparent;
}
"""


# ---------------------------------------------------------------------------
# État actif + persistance
# ---------------------------------------------------------------------------
def current_theme_name() -> str:
    settings = QSettings()
    name = settings.value("theme", DEFAULT_THEME)
    if name not in list_themes():
        return DEFAULT_THEME
    return name


def set_current_theme(name: str) -> None:
    QSettings().setValue("theme", name)


def current_theme() -> Theme:
    """Thème actif (mis en cache)."""
    global _ACTIVE
    name = current_theme_name()
    if _ACTIVE is None or _ACTIVE.name != name:
        _ACTIVE = load_theme(name)
    return _ACTIVE


def current_qss() -> str:
    return current_theme().stylesheet()


def current_palette() -> List[str]:
    theme = current_theme()
    return theme.palette if theme.palette else DEFAULT_PALETTE


def current_color(token: str) -> str:
    return current_theme().color(token)


# Signal notifiant tout widget d'un changement de thème actif.
from PySide6.QtCore import QObject, Signal as _Signal


class _ThemeSignals(QObject):
    changed = _Signal()


_theme_signals = _ThemeSignals()
themeChanged = _theme_signals.changed


def apply_theme_to(app, name: str = "") -> None:
    """Applique le thème sur toute l'application (widgets déjà créés compris).

    ``app`` doit être l'instance QApplication (pas une fenêtre) pour que le
    QSS se propage à toutes les fenêtres, y compris les dialogues ouverts.
    Repolish toutes les top-level widgets puis émet ``themeChanged`` pour que
    les widgets qui cachent des couleurs (graphe, branches) se rechargent.
    """
    if name:
        set_current_theme(name)
    global _ACTIVE
    _ACTIVE = None  # force le rechargement
    app.setStyleSheet(current_qss())
    for w in app.topLevelWidgets():
        w.style().unpolish(w)
        w.style().polish(w)
        w.update()
    themeChanged.emit()


# ---------------------------------------------------------------------------
# Compatibilité : les anciens noms restent disponibles (palette par défaut).
# ---------------------------------------------------------------------------
BG = DEFAULT_TOKENS["bg"]
SURFACE = DEFAULT_TOKENS["surface"]
FG = DEFAULT_TOKENS["fg"]
MUTED = DEFAULT_TOKENS["muted"]
BORDER = DEFAULT_TOKENS["border"]
ACCENT = DEFAULT_TOKENS["accent"]
COLOR_PALETTE = list(DEFAULT_PALETTE)
DARK_QSS = render_qss({})