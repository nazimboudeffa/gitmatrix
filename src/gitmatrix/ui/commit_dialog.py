"""Commit dialog box."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QDialogButtonBox,
    QLabel,
    QPushButton,
)


class CommitDialog(QDialog):
    """Multi-line commit message input with counter + validation."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create a commit")
        self.setMinimumWidth(480)
        self.setMinimumHeight(280)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Commit message:"))
        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText("Summary of changes…")
        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor)

        # Character counter + subject/body hint
        self._counter = QLabel("0 character")
        self._counter.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._counter.setObjectName("Counter")
        layout.addWidget(self._counter)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Commit")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        self._ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_btn.setProperty("accent", True)
        self._ok_btn.setEnabled(False)
        self._style_ok()
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _style_ok(self) -> None:
        # La propriété QSS [accent="true"] est appliquée via repolish
        self._ok_btn.style().unpolish(self._ok_btn)
        self._ok_btn.style().polish(self._ok_btn)

    def _on_text_changed(self) -> None:
        text = self._editor.toPlainText()
        subject = text.splitlines()[0] if text.splitlines() else ""
        body = text[len(subject) :].strip()
        n = len(text)
        lbl = f"{n} character{'s' if n > 1 else ''}"
        if len(subject) > 50:
            lbl += " — long subject (50 chars recommended max)"
        self._counter.setText(lbl)
        # Le bouton n'est activable que si un sujet non vide est présent
        self._ok_btn.setEnabled(bool(subject.strip()))
        self._style_ok()

    def message(self) -> str:
        return self._editor.toPlainText()
