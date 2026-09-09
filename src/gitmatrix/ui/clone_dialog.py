"""Boîte de dialogue de clonage d'un dépôt distant."""

from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QFileDialog,
    QFormLayout,
)


class CloneDialog(QDialog):
    """Saisie d'une URL Git et d'un dossier de destination, puis clonage."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Cloner un dépôt")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._url = QLineEdit()
        self._url.setPlaceholderText("https://github.com/utilisateur/projet.git")
        self._url.textChanged.connect(self._on_url_changed)
        form.addRow("URL du dépôt :", self._url)

        row = QHBoxLayout()
        self._dest = QLineEdit()
        self._dest.setPlaceholderText(os.path.expanduser("~"))
        browse = QPushButton("Parcourir…")
        browse.clicked.connect(self._browse)
        row.addWidget(self._dest, 1)
        row.addWidget(browse)
        form.addRow("Emplacement :", row)

        layout.addLayout(form)

        self._hint = QLabel("")
        self._hint.setObjectName("Counter")
        self._hint.setWordWrap(True)
        layout.addWidget(self._hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_btn.setText("Cloner")
        self._ok_btn.setProperty("accent", True)
        self._ok_btn.setEnabled(False)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Dossier de destination")
        if path:
            self._dest.setText(path)

    def _on_url_changed(self, text: str) -> None:
        self._ok_btn.setEnabled(bool(text.strip()))
        self._hint.setText("")
        if text.strip() and not self._dest.text().strip():
            base = text.strip().rstrip("/")
            name = os.path.basename(base)
            if name.lower().endswith(".git"):
                name = name[:-4]
            if name:
                self._dest.setText(os.path.join(os.path.expanduser("~"), name))

    def values(self) -> tuple:
        return self._url.text().strip(), self._dest.text().strip()