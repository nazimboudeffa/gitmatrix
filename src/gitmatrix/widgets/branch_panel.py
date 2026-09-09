"""Panneau des branches (aperçu + actions)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QMenu, QInputDialog, QMessageBox

from gitmatrix.core.git_repo import RefInfo, GitMatrixError


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
        for b in self._repo.all_branches():
            item = QListWidgetItem(b.name)
            item.setData(Qt.ItemDataRole.UserRole, b)
            if b.name == active:
                # Branche active : fond doré discret + texte accent + gras
                item.setForeground(QBrush(QColor("#e5c07b")))
                font = QFont(self.font())
                font.setBold(True)
                item.setFont(font)
                item.setBackground(QBrush(QColor("#2a2e26")))
                item.setText(f"{b.name}  ★")
            status = self._repo.upstream_status(b.name)
            if status is not None:
                ahead, behind = status
                parts = " ".join(
                    p
                    for p in (
                        f"↑{ahead}" if ahead else "",
                        f"↓{behind}" if behind else "",
                    )
                    if p
                )
                if parts:
                    item.setText(f"{item.text()}  {parts}".strip())
            self.addItem(item)

        # Branches distantes (affichage seul, non modifiables)
        remotes = self._repo.all_remote_branches()
        if remotes:
            sep = QListWidgetItem("Distantes")
            sep.setFlags(Qt.ItemFlag.NoItemFlags)
            sep.setForeground(QBrush(QColor("#7b61b8")))
            self.addItem(sep)
            for r in remotes:
                item = QListWidgetItem(r.name)
                item.setData(Qt.ItemDataRole.UserRole, r)
                item.setForeground(QBrush(QColor("#b9b4d6")))
                self.addItem(item)

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
