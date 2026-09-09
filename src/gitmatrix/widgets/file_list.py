"""Liste des fichiers modifiés (staging / unstaging visuel)."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QHeaderView

from gitmatrix.core.git_repo import FileChange, FileDiff


class FileListWidget(QTreeWidget):
    """Affiche les fichiers staged et unstaged avec actions contextuelles."""

    file_selected = Signal(object)  # FileChange
    commit_file_selected = Signal(object)  # FileDiff (mode "commit")
    stage_requested = Signal(object)  # FileChange
    unstage_requested = Signal(object)  # FileChange
    stage_all_requested = Signal()
    unstage_all_requested = Signal()

    # (couleur, fond translucide, lettre)
    STATUS_STYLE = {
        "U": ("#61afef", QColor(97, 175, 239, 36), "U"),
        "A": ("#98c379", QColor(152, 195, 121, 36), "A"),
        "M": ("#d19a66", QColor(209, 154, 102, 36), "M"),
        "D": ("#e06c75", QColor(224, 108, 117, 36), "D"),
        "R": ("#61afef", QColor(97, 175, 239, 36), "R"),
        "C": ("#61afef", QColor(97, 175, 239, 36), "C"),
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setHeaderLabels(["Fichier", ""])
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self.itemClicked.connect(self._on_clicked)
        self._commit_mode: Optional[str] = None  # sha court en mode "fichiers d'un commit"

    # ------------------------------------------------------------------
    def set_changes(self, changes: List[FileChange]) -> None:
        """Mode working tree (normal)."""
        self._commit_mode = None
        self.clear()
        grouped: dict = {"staged": [], "unstaged": []}
        for c in changes:
            grouped["staged" if c.staged else "unstaged"].append(c)

        for key, label in (("staged", "Staged"), ("unstaged", "Changes")):
            group = grouped[key]
            root = QTreeWidgetItem([f"{label}  "])
            self._style_group_header(root, label, len(group))
            for c in group:
                root.addChild(self._change_item(c))
            self.addTopLevelItem(root)
            root.setExpanded(True)
            root.setFlags(Qt.ItemFlag.ItemIsEnabled)

    def set_commit_files(self, diffs: List[FileDiff], short_sha: str) -> None:
        """Mode « fichiers modifiés par un commit » (lecture seule)."""
        self._commit_mode = short_sha
        self.clear()
        root = QTreeWidgetItem([f"Commit {short_sha}"])
        self._style_group_header(root, f"Commit {short_sha}", len(diffs))
        for d in diffs:
            item = QTreeWidgetItem([d.path, ""])
            status = "D" if d.is_deleted else ("A" if d.is_new else "M")
            color, bg, _ = self.STATUS_STYLE.get(status, ("#d7dae0", QColor(0, 0, 0, 0), "?"))
            self._decorate(item, color, bg, status)
            item.setData(0, Qt.ItemDataRole.UserRole, d)
            root.addChild(item)
        self.addTopLevelItem(root)
        root.setExpanded(True)
        root.setFlags(Qt.ItemFlag.ItemIsEnabled)

    def _style_group_header(self, root: QTreeWidgetItem, label: str, count: int) -> None:
        root.setText(0, f"{label}")
        font = QFont(self.font())
        font.setPointSize(9)
        font.setBold(True)
        root.setFont(0, font)
        root.setForeground(0, QBrush(QColor("#9da5b4")))
        if count:
            root.setText(1, f" {count} ")

    def _change_item(self, c: FileChange) -> QTreeWidgetItem:
        item = QTreeWidgetItem([c.path, ""])
        color, bg, letter = self.STATUS_STYLE.get(
            c.status, ("#d7dae0", QColor(0, 0, 0, 0), c.status or "?")
        )
        self._decorate(item, color, bg, letter)
        item.setData(0, Qt.ItemDataRole.UserRole, c)
        return item

    def _decorate(self, item: QTreeWidgetItem, color: QColor, bg: QColor, letter: str) -> None:
        item.setForeground(1, QBrush(color))
        status_font = QFont(self.font())
        status_font.setBold(True)
        item.setFont(1, status_font)
        item.setText(1, letter)
        item.setBackground(1, QBrush(bg))
        item.setData(1, Qt.ItemDataRole.UserRole, letter)

    def _current_file(self) -> Optional[FileChange]:
        item = self.currentItem()
        if item is None:
            return None
        data = item.data(0, Qt.ItemDataRole.UserRole)
        return data if isinstance(data, FileChange) else None

    def _current_diff(self) -> Optional[FileDiff]:
        item = self.currentItem()
        if item is None:
            return None
        data = item.data(0, Qt.ItemDataRole.UserRole)
        return data if isinstance(data, FileDiff) else None

    def _on_clicked(self, item, column) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, FileChange):
            self.file_selected.emit(data)
        elif isinstance(data, FileDiff):
            self.commit_file_selected.emit(data)

    def _show_menu(self, pos) -> None:
        file_change = self._current_file()
        menu = QMenu(self)
        if file_change is not None and self._commit_mode is None:
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
