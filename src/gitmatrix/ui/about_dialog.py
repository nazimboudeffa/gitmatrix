"""Dialogue « À propos » avec lien Tipeee."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

import gitmatrix

# >>> À remplacer par ton lien Tipeee réel <<<
TIPEEE_URL = "https://fr.tipeee.com/nazimboudeffa"
TIPEEE_LABEL = "Faire un don sur Tipeee"


class AboutDialog(QDialog):
    """Petite fenêtre présentant l'application et un lien de soutien."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("À propos de GitMatrix")
        self.setFixedWidth(380)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("GitMatrix")
        title.setObjectName("AboutTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e5c07b;")
        layout.addWidget(title)

        version = QLabel(f"Version {gitmatrix.__version__}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #9da5b4;")
        layout.addWidget(version)

        desc = QLabel(
            "Un client Git visuel et léger, pensé comme une alternative "
            "libre et open-source à GitKraken."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # Lien Tipeee (ouvre le navigateur)
        if TIPEEE_URL and TIPEEE_URL != "https://fr.tipeee.com/ton-pseudo":
            link = QLabel(
                f'<a style="color:#61afef" href="{TIPEEE_URL}">{TIPEEE_LABEL}</a>'
            )
        else:
            link = QLabel(f'<a style="color:#61afef" href="#">{TIPEEE_LABEL}</a>')
        link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link.setOpenExternalLinks(True)
        link.linkActivated.connect(self._open_tipeee)
        layout.addWidget(link)

        # Bouton de fermeture
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close_btn)
        row.addStretch(1)
        layout.addLayout(row)

    def _open_tipeee(self, url: str) -> None:
        real = TIPEEE_URL if TIPEEE_URL != "https://fr.tipeee.com/ton-pseudo" else url
        QDesktopServices.openUrl(QUrl(real))