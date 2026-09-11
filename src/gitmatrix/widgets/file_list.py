"""Liste des fichiers modifiés (staging / unstaging visuel).

Deux sections distinctes dans le panneau de droite : **Staged** (indexée) et
**Unstaged** (arbre de travail), chacune avec son compteur.
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QMenu,
    QHeaderView,
    QSplitter,
)

from gitmatrix.core.git_repo import FileChange


class FileListWidget(QWidget):
    """Deux listes (staged / unstaged) avec actions contextuelles par fichier."""

    file_activated = Signal(object)  # FileChange (double-clic → ouvre un diff)
    stage_requested = Signal(object)  # FileChange
    unstage_requested = Signal(object)  # FileChange

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

        self._staged_section, self._staged_list = self._section("Staged")
        self._unstaged_section, self._unstaged_list = self._section("Unstaged")

        self._splitter = QSplitter(Qt.Orientation.Vertical, self)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setHandleWidth(6)
        self._splitter.addWidget(self._staged_section)
        self._splitter.addWidget(self._unstaged_section)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._splitter)

        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 1)

    # ------------------------------------------------------------------
    def set_changes(self, changes: List[FileChange]) -> None:
        """Remplit les deux sections depuis la liste des changements."""
        staged = [c for c in changes if c.staged]
        unstaged = [c for c in changes if not c.staged]
        self._fill(self._staged_list, staged)
        self._fill(self._unstaged_list, unstaged)

    def _section(self, label: str) -> tuple:
        """Bloc section (en-tête + liste), hauteur égale pour chaque section."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.addWidget(self._group_header(label))
        tree = self._make_list()
        lay.addWidget(tree, 1)
        return w, tree

    def _group_header(self, label: str) -> QLabel:
        lbl = QLabel(label)
        lbl.setObjectName("GroupHeader")
        return lbl

    def _make_list(self) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setHeaderLabels(["File", ""])
        tree.setRootIsDecorated(False)
        tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(self._show_menu)
        tree.itemDoubleClicked.connect(self._on_double_clicked)
        return tree

    def _fill(self, tree: QTreeWidget, changes: List[FileChange]) -> None:
        tree.clear()
        for c in changes:
            item = QTreeWidgetItem([c.path, ""])
            color, bg, letter = self.STATUS_STYLE.get(
                c.status, ("#d7dae0", QColor(0, 0, 0, 0), c.status or "?")
            )
            item.setForeground(1, QBrush(color))
            status_font = QFont(self.font())
            status_font.setBold(True)
            item.setFont(1, status_font)
            item.setText(1, letter)
            item.setBackground(1, QBrush(bg))
            item.setData(0, Qt.ItemDataRole.UserRole, c)
            tree.addTopLevelItem(item)

    def _current_file(self) -> Optional[FileChange]:
        tree = self.sender()
        if not isinstance(tree, QTreeWidget):
            return None
        item = tree.currentItem()
        if item is None:
            return None
        data = item.data(0, Qt.ItemDataRole.UserRole)
        return data if isinstance(data, FileChange) else None

    def _on_double_clicked(self, item, column) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, FileChange):
            self.file_activated.emit(data)

    def _show_menu(self, pos) -> None:
        tree = self.sender()
        if not isinstance(tree, QTreeWidget):
            return
        item = tree.itemAt(pos)
        if item is None:
            return
        file_change = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(file_change, FileChange):
            return
        menu = QMenu(self)
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
        menu.exec(tree.viewport().mapToGlobal(pos))