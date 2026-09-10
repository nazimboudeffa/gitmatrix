"""Dialog for cloning a remote repository."""

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
    """Enter a Git URL and a destination folder, then clone."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Clone a repository")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._url = QLineEdit()
        self._url.setPlaceholderText("https://github.com/user/repo.git")
        self._url.textChanged.connect(self._on_url_changed)
        form.addRow("Repository URL:", self._url)

        row = QHBoxLayout()
        self._dest = QLineEdit()
        self._dest.setPlaceholderText(os.path.expanduser("~"))
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        row.addWidget(self._dest, 1)
        row.addWidget(browse)
        form.addRow("Location:", row)

        layout.addLayout(form)

        self._hint = QLabel("")
        self._hint.setObjectName("Counter")
        self._hint.setWordWrap(True)
        layout.addWidget(self._hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_btn.setText("Clone")
        self._ok_btn.setProperty("accent", True)
        self._ok_btn.setEnabled(False)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Destination folder")
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