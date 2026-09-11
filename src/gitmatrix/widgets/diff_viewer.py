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
        "meta": QColor("#6b7381"),
        "ctx": QColor("#abb2bf"),
    }
    # fonds des bandes +/- / hunk
    BG = {
        "add": QColor("#1f3c2a"),
        "del": QColor("#3d2226"),
        "hunk": QColor("#1d2d44"),
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        mono = QFont("Cascadia Mono")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setPointSize(9)
        mono.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.2)
        self.setFont(mono)
        self.setPlaceholderText("Select a file to see its diff.")

    def show_diff(self, diff: Optional[FileDiff], title: Optional[str] = None) -> None:
        """Affiche un FileDiff ; ``title`` optionnel pour l'en-tête de fichier."""
        self.show_diffs([diff] if diff is not None else [], title or "")

    def show_diffs(self, diffs: List[FileDiff], title: Optional[str] = None) -> None:
        """Affiche plusieurs FileDiff (diff complet d'un commit) à la suite."""
        self.clear()
        if not diffs:
            return

        cursor = self.textCursor()
        cursor.beginEditBlock()
        if title:
            self._line(cursor, f"━━ {title} ━━", "meta")
        for diff in diffs:
            self._line(cursor, f"━━ {diff.path} ━━", "meta")
            if not diff.hunks:
                self._line(cursor, "", "ctx")
                self._line(
                    cursor,
                    "(no text content to show — binary or empty file)",
                    "meta",
                )
                continue
            for line in diff.hunks:
                self._line(cursor, line["text"], line["type"])
        cursor.endEditBlock()
        self.setTextCursor(QTextCursor(self.document()))

    def _line(self, cursor: QTextCursor, text: str, kind: str) -> None:
        """Insère une ligne avec couleur + éventuel fond de bande."""
        fmt = QTextCharFormat()
        fmt.setForeground(self.COLORS.get(kind, self.COLORS["ctx"]))
        if kind in ("add", "del", "hunk"):
            fmt.setFontWeight(QFont.Weight.DemiBold)
            fmt.setBackground(self.BG[kind])
        cursor.setCharFormat(fmt)
        cursor.insertText(text + "\n")
