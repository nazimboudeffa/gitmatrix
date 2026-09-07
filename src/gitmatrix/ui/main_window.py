"""Fenêtre principale de GitMatrix."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QWidget,
    QVBoxLayout,
    QLabel,
    QToolBar,
    QFileDialog,
    QMessageBox,
    QHBoxLayout,
    QSizePolicy,
)

from gitmatrix.core.git_repo import GitMatrixError, GitRepo, FileChange
from gitmatrix.theme import DARK_QSS
from gitmatrix.widgets.commit_graph import CommitGraphWidget
from gitmatrix.widgets.file_list import FileListWidget
from gitmatrix.widgets.diff_viewer import DiffViewer
from gitmatrix.widgets.branch_panel import BranchPanel
from gitmatrix.ui.commit_dialog import CommitDialog
from gitmatrix.ui.about_dialog import AboutDialog


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GitMatrix")
        self.resize(1280, 780)
        self.setStyleSheet(DARK_QSS)

        self._repo: Optional[GitRepo] = None

        # ------------------------------------------------------------------
        # Widgets centraux
        # ------------------------------------------------------------------
        self.commit_graph = CommitGraphWidget()

        self.files = FileListWidget()
        self.diff_viewer = DiffViewer()
        self.branches = BranchPanel()

        # Panneau de droite : liste des fichiers + diff
        right_side = QSplitter(Qt.Orientation.Vertical)
        right_side.addWidget(self._titled("Modifications", self.files))
        right_side.addWidget(self._titled("Diff", self.diff_viewer))
        right_side.setStretchFactor(0, 1)
        right_side.setStretchFactor(1, 2)

        # Splitter principal : branches | graphe | fichiers+diff
        main_split = QSplitter(Qt.Orientation.Horizontal)
        main_split.addWidget(self._titled("Branches", self.branches))
        main_split.addWidget(self.commit_graph)
        main_split.addWidget(right_side)
        main_split.setStretchFactor(0, 0)
        main_split.setStretchFactor(1, 3)
        main_split.setStretchFactor(2, 2)
        main_split.setSizes([220, 620, 440])

        self.setCentralWidget(main_split)

        # ------------------------------------------------------------------
        # Toolbar
        # ------------------------------------------------------------------
        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.addAction("Ouvrir…", self._open_repo)
        toolbar.addAction("Actualiser", self._refresh)
        toolbar.addAction("Pull", self._pull)
        toolbar.addSeparator()
        toolbar.addAction("Stage All", self._stage_all)
        toolbar.addAction("Unstage All", self._unstage_all)
        toolbar.addSeparator()
        act_commit = toolbar.addAction("Commit…", self._open_commit_dialog)
        self._commit_action = act_commit

        # Espace poussant le bouton About vers la droite
        spacer = QWidget()
        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        toolbar.addWidget(spacer)
        toolbar.addAction("À propos", self._open_about)

        # ------------------------------------------------------------------
        # Status bar
        # ------------------------------------------------------------------
        self.status = self.statusBar()
        self._status_label = QLabel()
        self.status.addWidget(self._status_label)

        # ------------------------------------------------------------------
        # Connexions
        # ------------------------------------------------------------------
        self.commit_graph.commit_selected.connect(self._on_commit_selected)
        self.files.file_selected.connect(self._on_file_selected)
        self.files.stage_requested.connect(self._stage_file)
        self.files.unstage_requested.connect(self._unstage_file)
        self.files.stage_all_requested.connect(self._stage_all)
        self.files.unstage_all_requested.connect(self._unstage_all)
        self.branches.branch_checked.connect(self._checkout_branch)

        self._update_status()

    # ------------------------------------------------------------------
    # Constructeurs de panneaux
    # ------------------------------------------------------------------
    def _titled(self, title: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        label = QLabel(title)
        label.setObjectName("PanelTitle")
        layout.addWidget(label)
        layout.addWidget(widget, 1)
        return container

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _open_repo(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choisir un dépôt Git")
        if not path:
            return
        try:
            repo = GitRepo(path)
        except GitMatrixError as exc:
            QMessageBox.critical(self, "GitMatrix", str(exc))
            return
        self._repo = repo
        self.branches.set_repo(repo)
        self._refresh()

    def _refresh(self) -> None:
        if self._repo is None:
            return
        try:
            self.commit_graph.set_repo(self._repo)
            self.branches.refresh()
            self.files.set_changes(self._repo.changes())
        except GitMatrixError as exc:
            QMessageBox.warning(self, "Erreur", str(exc))
        self._update_status()

    def _on_commit_selected(self, commit) -> None:
        self._update_status(commit=commit)

    def _on_file_selected(self, file_change: FileChange) -> None:
        if self._repo is None:
            return
        diff = self._repo.diff(file_change.path)
        self.diff_viewer.show_diff(diff)

    def _stage_file(self, file_change: FileChange) -> None:
        if self._repo is None:
            return
        self._repo.stage(file_change.path)
        self._refresh()

    def _unstage_file(self, file_change: FileChange) -> None:
        if self._repo is None:
            return
        self._repo.unstage(file_change.path)
        self._refresh()

    def _stage_all(self) -> None:
        if self._repo is None:
            return
        self._repo.stage_all()
        self._refresh()

    def _unstage_all(self) -> None:
        if self._repo is None:
            return
        self._repo.unstage_all()
        self._refresh()

    def _open_commit_dialog(self) -> None:
        if self._repo is None:
            QMessageBox.information(self, "GitMatrix", "Ouvrez d'abord un dépôt.")
            return
        dialog = CommitDialog(self)
        if dialog.exec():
            try:
                new_sha = self._repo.commit_all(dialog.message())
                self.commit_graph.select_commit(new_sha)
            except GitMatrixError as exc:
                QMessageBox.critical(self, "Erreur", str(exc))
        self._refresh()

    def _checkout_branch(self, name: str) -> None:
        if self._repo is None:
            return
        try:
            self._repo.checkout(name)
        except GitMatrixError as exc:
            QMessageBox.critical(self, "Erreur", str(exc))
        self._refresh()

    def _pull(self) -> None:
        if self._repo is None:
            QMessageBox.information(self, "GitMatrix", "Ouvrez d'abord un dépôt.")
            return
        try:
            output = self._repo.pull()
        except GitMatrixError as exc:
            QMessageBox.critical(self, "Erreur", str(exc))
            return
        self._refresh()
        self.status.showMessage(f"Pull effectué : {output}", 8000)

    def _open_about(self) -> None:
        AboutDialog(self).exec()

    def _update_status(self, commit=None) -> None:
        parts = []
        if self._repo is not None:
            branch = self._repo.active_branch or "(détaché)"
            parts.append(f"Branche : {branch}")
            if self._repo.is_dirty():
                parts.append("● modifications")
        if commit is not None:
            parts.append(f"{commit.short_sha}  {commit.subject}")
        self._status_label.setText("   |   ".join(parts) if parts else "Aucun dépôt ouvert")