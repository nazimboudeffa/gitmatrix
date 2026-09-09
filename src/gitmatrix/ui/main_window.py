"""Fenêtre principale de GitMatrix."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QToolBar,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
    QPushButton,
    QToolButton,
)
from PySide6.QtGui import QKeySequence, QAction, QShortcut

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
        self._current_commit = None

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
        # Toolbar — actions regroupées par catégorie
        # ------------------------------------------------------------------
        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)
        self._toolbar = toolbar
        self.addToolBar(toolbar)

        spacer = QWidget()
        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # Groupe 1 : Fichier
        act_open = toolbar.addAction("Ouvrir", self._open_repo)
        self._set_shortcut(act_open, "Ctrl+O")
        act_refresh = toolbar.addAction("Actualiser", self._refresh)
        self._set_shortcut(act_refresh, "Ctrl+R")
        toolbar.addWidget(spacer)
        act_commit = toolbar.addAction("Commit", self._open_commit_dialog)
        self._commit_action = act_commit
        b = toolbar.widgetForAction(act_commit)
        if isinstance(b, QToolButton):
            b.setObjectName("ActionCommit")
            b.setToolTip("Créer un commit (Ctrl+Return)")
            self._set_shortcut(act_commit, "Ctrl+Return")

        # --- Séparateur puis groupe Sync ---
        toolbar.addSeparator()
        act_fetch = toolbar.addAction("Fetch", self._fetch)
        act_pull = toolbar.addAction("Pull", self._pull)
        act_push = toolbar.addAction("Push", self._push)
        self._set_shortcut(act_push, "Ctrl+P")

        # --- Groupe Staging ---
        toolbar.addSeparator()
        act_stage_all = toolbar.addAction("Stage All", self._stage_all)
        act_unstage_all = toolbar.addAction("Unstage All", self._unstage_all)
        self._mark_danger(act_unstage_all)
        self._set_shortcut(act_stage_all, "Ctrl+S")

        # --- Séparateur puis About (droite) ---
        toolbar.addSeparator()
        toolbar.addAction("À propos", self._open_about)

        # ------------------------------------------------------------------
        # Status bar
        # ------------------------------------------------------------------
        self.status = self.statusBar()
        self._status_label = QLabel()
        self.status.addWidget(self._status_label)

        # ------------------------------------------------------------------
        # État vide centralisé
        # ------------------------------------------------------------------
        self._build_empty_state()

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

        # Désactiver les actions tant qu'aucun dépôt n'est ouvert
        self._set_actions_enabled(False)
        self._update_status()

    # ------------------------------------------------------------------
    # Racourcis clavier
    # ------------------------------------------------------------------
    def _set_shortcut(self, action: QAction, seq: str) -> None:
        sc = QShortcut(QKeySequence(seq), self)
        sc.activated.connect(action.trigger)

    def _mark_danger(self, action: QAction) -> None:
        b = self._toolbar.widgetForAction(action)
        if isinstance(b, QToolButton):
            b.setObjectName("ActionDanger")

    def _set_actions_enabled(self, enabled: bool) -> None:
        for a in self._toolbar.actions():
            if a.isSeparator():
                continue
            a.setEnabled(enabled)

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

    def _build_empty_state(self) -> None:
        """Superpose un écran d'accueil par-dessus le graphe tant qu'aucun dépôt."""
        self._empty_container = QWidget(self.commit_graph)
        lay = QVBoxLayout(self._empty_container)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(10)

        title = QLabel("Bienvenue dans GitMatrix")
        title.setObjectName("EmptyStateTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text = QLabel(
            "Ouvrez un dépôt Git pour visualiser l'historique, "
            "gérer les branches et effectuer des commits."
        )
        text.setObjectName("EmptyStateText")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setWordWrap(True)

        btn = QPushButton("Ouvrir un dépôt…")
        btn.setObjectName("EmptyOpen")
        btn.clicked.connect(self._open_repo)

        lay.addWidget(title)
        lay.addWidget(text)
        btn_wrap = QWidget()
        hl = QHBoxLayout(btn_wrap)
        hl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(btn)
        lay.addWidget(btn_wrap)

        self._empty_container.raise_()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "_empty_container"):
            self._empty_container.setGeometry(self.commit_graph.rect())
            self._empty_container.raise_()

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
        self._set_actions_enabled(True)
        if hasattr(self, "_empty_container"):
            self._empty_container.hide()
        self._refresh()

    def _refresh(self) -> None:
        if self._repo is None:
            return
        try:
            self.commit_graph.set_repo(self._repo)
            self.branches.refresh()
            self.files.set_changes(self._repo.changes())
            # re-afficher le diff du commit sélectionné si présent
            self._refresh_commit_detail()
        except GitMatrixError as exc:
            QMessageBox.warning(self, "Erreur", str(exc))
        self._update_status()

    def _refresh_commit_detail(self) -> None:
        if self._current_commit is not None:
            self._show_commit_diff(self._current_commit)

    def _on_commit_selected(self, commit) -> None:
        self._current_commit = commit
        self._show_commit_diff(commit)
        self._update_status(commit=commit)

    def _show_commit_diff(self, commit) -> None:
        """Affiche le diff d'un commit (tous ses fichiers) dans le DiffViewer."""
        if self._repo is None:
            return
        try:
            diffs = self._repo.diff_commit(commit.hexsha)
        except GitMatrixError as exc:
            QMessageBox.warning(self, "Erreur", str(exc))
            return
        # Affiche le premier diff ; l'en-tête mentionne le nombre de fichiers
        if diffs:
            header = f"{commit.short_sha} · {len(diffs)} fichier(s) modifié(s)"
            self.diff_viewer.show_diff(diffs[0], title=header)
        else:
            self.diff_viewer.show_diff(None, title=f"{commit.short_sha} · aucun changement")

    def _on_file_selected(self, file_change: FileChange) -> None:
        if self._repo is None:
            return
        diff = self._repo.diff(file_change.path)
        self.diff_viewer.show_diff(diff, title=file_change.path)

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
                self._current_commit = self.commit_graph.selected_commit
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

    def _fetch(self) -> None:
        if self._repo is None:
            QMessageBox.information(self, "GitMatrix", "Ouvrez d'abord un dépôt.")
            return
        try:
            output = self._repo.fetch()
        except GitMatrixError as exc:
            QMessageBox.critical(self, "Erreur", str(exc))
            return
        self._refresh()
        self.status.showMessage(f"Fetch effectué : {output}", 8000)

    def _push(self) -> None:
        if self._repo is None:
            QMessageBox.information(self, "GitMatrix", "Ouvrez d'abord un dépôt.")
            return
        try:
            output = self._repo.push()
        except GitMatrixError as exc:
            QMessageBox.critical(self, "Erreur", str(exc))
            return
        self._refresh()
        self.status.showMessage(f"Push effectué : {output}", 8000)

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
            changes = self._repo.changes()
            n_staged = sum(1 for c in changes if c.staged)
            n_unstaged = sum(1 for c in changes if not c.staged)
            if self._repo.is_dirty():
                parts.append(f"● {n_staged}+ staged · {n_unstaged} unstaged")
        if commit is not None:
            parts.append(f"{commit.short_sha}  {commit.subject}")
        self._status_label.setText("   |   ".join(parts) if parts else "Aucun dépôt ouvert")
