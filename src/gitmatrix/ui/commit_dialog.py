"""Boîte de dialogue de commit."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPlainTextEdit,
    QDialogButtonBox,
    QLabel,
)


class CommitDialog(QDialog):
    """Saisie d'un message de commit multi-lignes."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Créer un commit")
        self.setMinimumWidth(440)
        self.setMinimumHeight(240)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Message de commit :"))
        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText("Résumé du changement…")
        layout.addWidget(self._editor)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Committer")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def message(self) -> str:
        return self._editor.toPlainText()