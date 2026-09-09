"""Panneau des branches (aperçu + actions)."""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap, QFont
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QMenu,
    QInputDialog,
    QMessageBox,
    QWidget,
    QHBoxLayout,
    QLabel,
)

from gitmatrix.core.git_repo import RefInfo, GitMatrixError
from gitmatrix.theme import COLOR_PALETTE, ACCENT


def _dot_icon(color: str, size: int = 8) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(color))
    p.drawEllipse(0, 0, size, size)
    p.end()
    return pm


class BranchPanel(QListWidget):
    """Liste des branches avec menu contextuel (créer, supprimer, checkout)."""

    branch_checked = Signal(str)  # nom de branche

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self.itemDoubleClicked.connect(self._on_double_click)
        self._repo = None

    def _on_double_click(self, item) -> None:
        branch = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(branch, RefInfo) and branch.kind == "branch":
            self.branch_checked.emit(branch.name)

    def set_repo(self, repo) -> None:
        self._repo = repo

    def refresh(self) -> None:
        self.clear()
        if self._repo is None:
            return
        active = self._repo.active_branch
        for i, b in enumerate(self._repo.all_branches()):
            is_active = b.name == active
            dot = ACCENT if is_active else COLOR_PALETTE[i % len(COLOR_PALETTE)]
            self._add_branch(b, dot, is_active)

        # Branches distantes (affichage seul, non modifiables)
        remotes = self._repo.all_remote_branches()
        if remotes:
            sep = QListWidgetItem("DISTANTES")
            sep.setFlags(Qt.ItemFlag.NoItemFlags)
            sep.setForeground(QColor("#7b61b8"))
            f = QFont(self.font())
            f.setPointSize(9)
            f.setBold(True)
            sep.setFont(f)
            self.addItem(sep)
            for r in sorted(remotes, key=lambda x: x.name):
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, r)
                row = self._row_widget(r.name, "#7b61b8", False, None)
                item.setSizeHint(row.sizeHint())
                self.addItem(item)
                self.setItemWidget(item, row)

    def _add_branch(self, b: RefInfo, dot: str, is_active: bool) -> None:
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, b)
        status = self._repo.upstream_status(b.name)
        row = self._row_widget(
            b.name,
            dot,
            is_active,
            status if not is_active else None,
        )
        item.setSizeHint(row.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, row)

    @staticmethod
    def _row_widget(name: str, dot: str, active: bool, status):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 4, 14, 4)
        lay.setSpacing(8)

        dot_lbl = QLabel()
        dot_lbl.setFixedSize(8, 8)
        dot_lbl.setPixmap(_dot_icon(dot, 8))
        lay.addWidget(dot_lbl)

        name_lbl = QLabel(name)
        if active:
            name_lbl.setStyleSheet(
                f"color:{ACCENT}; font-weight:600; background:transparent;"
            )
        lay.addWidget(name_lbl)

        if status is not None:
            ahead, behind = status
            stat = QHBoxLayout()
            stat.setSpacing(4)
            if ahead:
                a = QLabel(f"↑{ahead}")
                a.setStyleSheet("color:#98c379; background:transparent;")
                stat.addWidget(a)
            if behind:
                b = QLabel(f"↓{behind}")
                b.setStyleSheet("color:#e06c75; background:transparent;")
                stat.addWidget(b)
            lay.addLayout(stat)

        stretch = QLabel()
        lay.addWidget(stretch, 1)
        return w

    def _show_menu(self, pos) -> None:
        item = self.itemAt(pos)
        menu = QMenu(self)
        menu.addAction("Nouvelle branche…", self._new_branch)
        if item is not None:
            branch = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(branch, RefInfo) and branch.kind == "branch":
                menu.addAction(
                    "Basculer (checkout)", lambda: self.branch_checked.emit(branch.name)
                )
                menu.addAction("Supprimer", lambda: self._delete_branch(branch.name))
        menu.exec(self.mapToGlobal(pos))

    def _new_branch(self) -> None:
        if self._repo is None:
            return
        name, ok = QInputDialog.getText(self, "Nouvelle branche", "Nom de la branche :")
        if ok and name.strip():
            try:
                self._repo.create_branch(name.strip())
                self.refresh()
            except GitMatrixError as exc:
                QMessageBox.critical(self, "Erreur", str(exc))

    def _delete_branch(self, name: str) -> None:
        res = QMessageBox.question(
            self,
            "Supprimer la branche",
            f"Supprimer définitivement la branche « {name} » ?",
        )
        if res == QMessageBox.StandardButton.Yes:
            try:
                self._repo.delete_branch(name)
                self.refresh()
            except GitMatrixError as exc:
                QMessageBox.critical(self, "Erreur", str(exc))