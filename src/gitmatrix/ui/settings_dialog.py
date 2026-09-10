"""Dialogue des paramètres du logiciel."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

import gitmatrix


class SettingsDialog(QDialog):
    """Paramètres du logiciel GitMatrix.

    Les réglages réels (thème, raccourcis, colonnes…) arriveront avec la
    phase « Confort & performance » ; ce dialogue pose le cadre visuel.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Paramètres du logiciel")
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Paramètres du logiciel")
        title.setObjectName("AboutTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e5c07b;")
        layout.addWidget(title)

        version = QLabel(f"GitMatrix {gitmatrix.__version__}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #9da5b4;")
        layout.addWidget(version)

        note = QLabel(
            "Les préférences (thème, raccourcis clavier, colonnes du graphe,\n"
            "dépôts récents) seront disponibles dans une prochaine version."
        )
        note.setWordWrap(True)
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet("color: #9da5b4;")
        layout.addWidget(note)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close_btn)
        row.addStretch(1)
        layout.addLayout(row)