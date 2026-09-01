"""Panneau des branches (aperçu + actions)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QMenu, QInputDialog, QMessageBox

from gitmatrix.core.git_repo import RefInfo, GitMatrixError


class BranchPanel(QListWidget):
    """Liste des branches avec menu contextuel (créer, supprimer, checkout)."""

    branch_checked = Signal(str)  # nom de branche

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self.itemDoubleClicked.connect(
            lambda item: self.branch_checked.emit(item.text())
        )
        self._repo = None

    def set_repo(self, repo) -> None:
        self._repo = repo

    def refresh(self) -> None:
        self.clear()
        if self._repo is None:
            return
        active = self._repo.active_branch
        for b in self._repo.all_branches():
            item = QListWidgetItem(b.name)
            item.setData(Qt.ItemDataRole.UserRole, b)
            if b.name == active:
                item.setForeground(QBrush(QColor("#e5c07b")))
                item.setText(f"{b.name}  ★")
            self.addItem(item)

    def _show_menu(self, pos) -> None:
        item = self.itemAt(pos)
        menu = QMenu(self)
        menu.addAction("Nouvelle branche…", self._new_branch)
        if item is not None:
            branch = item.data(Qt.ItemDataRole.UserRole)
            if branch is not None and isinstance(branch, RefInfo):
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