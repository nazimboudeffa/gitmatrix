"""Fenêtre de diff d'un fichier (double-clic dans Changes)."""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
)

from gitmatrix.core.git_repo import FileDiff
from gitmatrix.widgets.diff_viewer import DiffViewer


class DiffDialog(QDialog):
    """Affiche le diff d'un fichier (working tree ou index) dans une fenêtre."""

    def __init__(self, diff: Optional[FileDiff], title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(900, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QLabel(title)
        header.setObjectName("DiffDialogTitle")
        layout.addWidget(header)

        viewer = DiffViewer()
        viewer.setObjectName("DiffDialogViewer")
        viewer.show_diff(diff, title=title)
        layout.addWidget(viewer, 1)