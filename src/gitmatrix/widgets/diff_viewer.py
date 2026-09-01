"""Visionneuse de diff colorée (lecture seule)."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor, QFont
from PySide6.QtWidgets import QPlainTextEdit

from gitmatrix.core.git_repo import FileDiff


class DiffViewer(QPlainTextEdit):
    """Affiche un diff unifié avec coloration syntaxique (+, -, @@)."""

    COLORS = {
        "add": QColor("#98c379"),
        "del": QColor("#e06c75"),
        "hunk": QColor("#61afef"),
        "meta": QColor("#5c6470"),
        "ctx": QColor("#abb2bf"),
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        mono = QFont("Cascadia Mono")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setPointSize(9)
        self.setFont(mono)
        self.document().setDefaultStyleSheet("")
        self.setPlaceholderText("Sélectionnez un fichier pour voir son diff.")

    def show_diff(self, diff: Optional[FileDiff]) -> None:
        self.clear()
        if diff is None:
            return
        if not diff.hunks:
            self.appendPlainText(
                "(aucun contenu textuel à afficher — fichier binaire ou vide)"
            )
            return

        cursor = self.textCursor()
        cursor.beginEditBlock()
        for line in diff.hunks:
            fmt = QTextCharFormat()
            fmt.setForeground(self.COLORS.get(line["type"], self.COLORS["ctx"]))
            if line["type"] in ("add", "del", "hunk"):
                fmt.setFontWeight(QFont.Weight.DemiBold)
            cursor.setCharFormat(fmt)
            cursor.insertText(line["text"] + "\n")
        cursor.endEditBlock()
        self.setTextCursor(QTextCursor(self.document()))