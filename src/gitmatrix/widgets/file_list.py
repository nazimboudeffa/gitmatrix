"""Liste des fichiers modifiés (staging / unstaging visuel)."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QHeaderView

from gitmatrix.core.git_repo import FileChange


class FileListWidget(QTreeWidget):
    """Affiche les fichiers staged et unstaged avec actions contextuelles."""

    file_selected = Signal(object)  # FileChange
    stage_requested = Signal(object)  # FileChange
    unstage_requested = Signal(object)  # FileChange
    stage_all_requested = Signal()
    unstage_all_requested = Signal()

    STATUS_STYLE = {
        "U": ("#d19a66", "?"),
        "A": ("#98c379", "A"),
        "M": ("#d19a66", "M"),
        "D": ("#e06c75", "D"),
        "R": ("#61afef", "R"),
        "C": ("#61afef", "C"),
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setHeaderLabels(["Fichier", ""])
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self.itemClicked.connect(self._on_clicked)
        self._root_staged = None
        self._root_unstaged = None

    # ------------------------------------------------------------------
    def set_changes(self, changes: List[FileChange]) -> None:
        self.clear()
        self._root_staged = QTreeWidgetItem(["Staged"])
        self._root_unstaged = QTreeWidgetItem(["Changes"])
        for c in changes:
            item = QTreeWidgetItem([c.path, ""])
            color, letter = self.STATUS_STYLE.get(
                c.status, ("#d7dae0", c.status or "?")
            )
            # Pastille de statut : lettre colorée en gras (colonne 1)
            item.setForeground(1, QBrush(QColor(color)))
            status_font = QFont(self.font())
            status_font.setBold(True)
            item.setFont(1, status_font)
            item.setText(1, letter)
            # Le nom de fichier : légère teinte selon staged/unstaged
            name_color = "#98c379" if c.staged else "#e06c75"
            item.setForeground(0, QBrush(QColor(name_color)))
            item.setData(0, Qt.ItemDataRole.UserRole, c)
            (self._root_staged if c.staged else self._root_unstaged).addChild(item)
        self.addTopLevelItem(self._root_staged)
        self.addTopLevelItem(self._root_unstaged)
        self._root_staged.setExpanded(True)
        self._root_unstaged.setExpanded(True)

    def _current_file(self) -> Optional[FileChange]:
        item = self.currentItem()
        if item is None:
            return None
        data = item.data(0, Qt.ItemDataRole.UserRole)
        return data if isinstance(data, FileChange) else None

    def _on_clicked(self, item, column) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, FileChange):
            self.file_selected.emit(data)

    def _show_menu(self, pos) -> None:
        file_change = self._current_file()
        menu = QMenu(self)
        if file_change is not None:
            if file_change.staged:
                a = menu.addAction("Unstage")
                a.triggered.connect(
                    lambda _=False, fc=file_change: self.unstage_requested.emit(fc)
                )
            else:
                a = menu.addAction("Stage")
                a.triggered.connect(
                    lambda _=False, fc=file_change: self.stage_requested.emit(fc)
                )
        menu.addSeparator()
        menu.addAction("Stage All", self.stage_all_requested.emit)
        menu.addAction("Unstage All", self.unstage_all_requested.emit)
        menu.exec(self.viewport().mapToGlobal(pos))
