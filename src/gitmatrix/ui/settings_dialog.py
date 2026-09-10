"""Dialogue des paramètres du logiciel."""

from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
)

import gitmatrix
from gitmatrix.theme import (
    apply_theme_to,
    current_theme_name,
    list_themes,
)
from gitmatrix.ui.splash_screen import DEFAULT_SPLASH, list_splashes


class SettingsDialog(QDialog):
    """Paramètres du logiciel GitMatrix.

    Choisissez le thème (appliqué immédiatement) et le splash screen
    (au prochain lancement).  Les thèmes viennent de ``assets/themes``
    et ``~/.gitmatrix/themes`` ; les splash de ``assets/splashscreens``
    et ``~/.gitmatrix/splashscreens``.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Paramètres du logiciel")
        self.setFixedWidth(440)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        title = QLabel("Paramètres du logiciel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e5c07b;")
        layout.addWidget(title)

        version = QLabel(f"GitMatrix {gitmatrix.__version__}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #9da5b4;")
        layout.addWidget(version)

        # --- Thème -----------------------------------------------------
        layout.addWidget(self._label("Thème"))
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(list_themes())
        self._theme_combo.setCurrentText(current_theme_name())
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)
        layout.addWidget(self._theme_combo)

        layout.addWidget(
            self._hint(
                "Ajoutez des thèmes dans ~/.gitmatrix/themes (fichiers JSON)."
            )
        )

        # --- Splash screen ---------------------------------------------
        layout.addWidget(self._label("Splash screen"))
        row = QHBoxLayout()
        row.setSpacing(8)
        self._splash_combo = QComboBox()
        self._splash_combo.addItems(list_splashes())
        settings = QSettings()
        cached = settings.value("splash", DEFAULT_SPLASH)
        if cached in list_splashes():
            self._splash_combo.setCurrentText(cached)
        self._splash_combo.currentTextChanged.connect(self._on_splash_changed)
        preview_btn = QPushButton("Aperçu")
        preview_btn.setToolTip("Voir le splash en plein écran, sans redémarrer.")
        preview_btn.clicked.connect(self._on_preview_clicked)
        row.addWidget(self._splash_combo, 1)
        row.addWidget(preview_btn)
        layout.addLayout(row)

        layout.addWidget(
            self._hint(
                "Ajoutez des splash screens dans "
                "~/.gitmatrix/splashscreens (fichiers JSON).\n"
                "Le changement s'applique au prochain lancement ; "
                "cliquez sur « Aperçu » pour voir le rendu."
            )
        )

        self._splash_enabled = QCheckBox("Activer le splash screen au démarrage")
        self._splash_enabled.setChecked(
            QSettings().value("enable_splash", True, type=bool)
        )
        self._splash_enabled.toggled.connect(
            lambda on: QSettings().setValue("enable_splash", on)
        )
        layout.addWidget(self._splash_enabled)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close_btn)
        row.addStretch(1)
        layout.addLayout(row)

    @staticmethod
    def _label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #9da5b4; font-weight: 600; font-size: 12px;")
        return lbl

    @staticmethod
    def _hint(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #6b7381; font-size: 11px;")
        return lbl

    def _on_theme_changed(self, name: str) -> None:
        if not name:
            return
        apply_theme_to(QApplication.instance(), name)

    def _on_splash_changed(self, name: str) -> None:
        if name:
            QSettings().setValue("splash", name)

    def _on_preview_clicked(self) -> None:
        from gitmatrix.ui.splash_preview import preview_splash

        preview_splash(self._splash_combo.currentText())