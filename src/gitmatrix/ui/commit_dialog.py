"""Commit dialog box."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QLineEdit,
    QDialogButtonBox,
    QLabel,
)


class CommitDialog(QDialog):
    """Two-field commit message (subject + detail) with counter + validation."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create a commit")
        self.setMinimumWidth(480)
        self.setMinimumHeight(320)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Subject — main message:"))
        self._subject = QLineEdit()
        self._subject.setPlaceholderText("Summarize the change (50 chars recommended)")
        self._subject.setMaxLength(80)
        self._subject.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._subject)

        layout.addWidget(QLabel("Detail — optional:"))
        self._body = QPlainTextEdit()
        self._body.setPlaceholderText("Explain the motivation and details…")
        self._body.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._body, 1)

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
        subject = self._subject.text().strip()
        body = self._body.toPlainText()
        total = len(subject) + len(body)
        lbl = f"{total} character{'s' if total > 1 else ''}"
        if len(subject) > 50:
            lbl += " — long subject (50 chars recommended max)"
        self._counter.setText(lbl)
        self._ok_btn.setEnabled(bool(subject))

    def message(self) -> str:
        """Message complet : sujet + détail séparés par une ligne vide."""
        subject = self._subject.text().strip()
        body = self._body.toPlainText().strip()
        if body:
            return f"{subject}\n\n{body}"
        return subject