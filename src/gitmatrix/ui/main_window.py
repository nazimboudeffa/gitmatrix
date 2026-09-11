"""Fenêtre principale de GitMatrix."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QToolBar,
    QFrame,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
    QToolButton,
    QMenu,
)
from PySide6.QtGui import QIcon, QKeySequence, QAction, QShortcut

from gitmatrix.core.git_repo import GitMatrixError, GitRepo, FileChange
from gitmatrix.theme import current_qss, themeChanged
from gitmatrix.widgets.commit_graph import CommitGraphWidget
from gitmatrix.widgets.file_list import FileListWidget
from gitmatrix.widgets.branch_panel import BranchPanel
from gitmatrix.ui.commit_dialog import CommitDialog
from gitmatrix.ui.commit_detail_dialog import CommitDetailDialog
from gitmatrix.ui.diff_dialog import DiffDialog
from gitmatrix.ui.about_dialog import AboutDialog
from gitmatrix.ui.clone_dialog import CloneDialog
from gitmatrix.ui.settings_dialog import SettingsDialog

_ICONS = Path(__file__).resolve().parent.parent / "assets" / "icons"


def _icon(name: str) -> QIcon:
    return QIcon(str(_ICONS / f"{name}.svg"))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GitMatrix")
        self.resize(1280, 780)
        self.setStyleSheet(current_qss())

        self._repo: Optional[GitRepo] = None

        # ------------------------------------------------------------------
        # Widgets centraux
        # ------------------------------------------------------------------
        self.commit_graph = CommitGraphWidget()

        self.files = FileListWidget()
        self.branches = BranchPanel()

        # Panneau de droite : Changes + workflow (stage → commit → push)
        right_side = self._build_right_panel()

        # Splitter principal : branches | graphe | fichiers
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
        # Toolbar — groupes conformes à la maquette (icône + texte)
        # ------------------------------------------------------------------
        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(15, 15))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self._toolbar = toolbar
        self.addToolBar(toolbar)

        # Groupe 1 : Fichier (à gauche)
        act_clone = toolbar.addAction(_icon("clone"), "Clone", self._clone_repo)
        act_clone.setToolTip("Clone a remote repository")
        act_open = toolbar.addAction(_icon("open"), "Open", self._open_repo)
        act_open.setToolTip("Open a repository (Ctrl+O)")
        self._set_shortcut(act_open, "Ctrl+O")
        act_refresh = toolbar.addAction(_icon("refresh"), "Refresh", self._refresh)
        act_refresh.setToolTip("Reload graph (Ctrl+R)")
        self._set_shortcut(act_refresh, "Ctrl+R")

        # Groupe 2 : Branche (contexte) — sélecteur, à côté d'Actualiser
        toolbar.addSeparator()
        self._branch_btn = self._make_branch_button()
        toolbar.addWidget(self._branch_btn)

        # Espaceur gauche : centre le bloc réseau
        toolbar.addWidget(self._stretch())

        # Groupe 3 : Réseau (milieu) — fetch / pull
        act_fetch = toolbar.addAction(_icon("fetch"), "Fetch", self._fetch)
        act_pull = toolbar.addAction(_icon("pull"), "Pull", self._pull)

        # Espaceur droit : équilibre le bloc central
        toolbar.addWidget(self._stretch())

        # Groupe 7 : Paramètres (à droite) — menu déroulant engrenage
        self._settings_btn = self._make_settings_button()
        toolbar.addWidget(self._settings_btn)
        self._actions_to_keep = {act_clone}

        # ------------------------------------------------------------------
        # Status bar — chips (branche / dirty) + infos droites (staged/unstaged)
        # ------------------------------------------------------------------
        self.status = self.statusBar()

        self._sb_branch = self._chip("", "branch")
        self._sb_dirty = self._chip("", "dirty")
        self._sb_commit = QLabel()
        self._sb_commit.setObjectName("StatusBarText")

        self._sb_staged_w, self._sb_staged = self._chip_dot("#98c379")
        self._sb_unstaged_w, self._sb_unstaged = self._chip_dot("#d19a66")

        self.status.addWidget(self._sb_branch)
        self.status.addWidget(self._sb_dirty)
        self.status.addWidget(self._sb_commit)
        self.status.addPermanentWidget(self._sb_staged_w)
        self.status.addPermanentWidget(self._sb_unstaged_w)

        # ------------------------------------------------------------------
        # État vide : graphe seul (aucune superposition)
        # ------------------------------------------------------------------
        self.commit_graph.setMinimumSize(600, 400)

        # ------------------------------------------------------------------
        # Connexions
        # ------------------------------------------------------------------
        self.commit_graph.commit_selected.connect(self._on_commit_selected)
        self.commit_graph.commit_activated.connect(self._open_commit_detail)
        self.files.file_activated.connect(self._open_file_diff)
        self.files.stage_requested.connect(self._stage_file)
        self.files.unstage_requested.connect(self._unstage_file)
        self.branches.branch_checked.connect(self._checkout_branch)
        themeChanged.connect(self._on_theme_changed)

        # Raccourcis du workflow (gardés quand les boutons quittent la toolbar)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self._stage_all)
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(
            lambda: self._open_commit_dialog() if self._repo is not None else None
        )
        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(
            lambda: self._push() if self._repo is not None else None
        )

        # Désactiver les actions tant qu'aucun dépôt n'est ouvert
        self._set_actions_enabled(False)
        self._update_status()

    @staticmethod
    def _stretch() -> QWidget:
        w = QWidget()
        w.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        return w

    def _set_shortcut(self, action: QAction, seq: str) -> None:
        sc = QShortcut(QKeySequence(seq), self)
        sc.activated.connect(action.trigger)

    def _make_branch_button(self) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("ActionBranch")
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn.setIconSize(QSize(15, 15))
        btn.setIcon(_icon("branch"))
        btn.setText("Branch")
        btn.setToolTip("Active branch — switch menu")
        btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        btn.setMenu(QMenu(self))
        btn.setEnabled(False)
        return btn

    def _make_settings_button(self) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("ActionSettings")
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn.setIconSize(QSize(15, 15))
        btn.setIcon(_icon("settings"))
        btn.setText("Settings")
        btn.setToolTip("Settings and information")
        btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self)

        act_settings = menu.addAction(_icon("settings"), "Software Settings…")
        act_settings.triggered.connect(self._open_settings)

        menu.addSeparator()

        act_about = menu.addAction(_icon("about"), "About")
        act_about.triggered.connect(self._open_about)

        btn.setMenu(menu)
        return btn

    def _refresh_branch_menu(self) -> None:
        menu = self._branch_btn.menu()
        menu.clear()
        if self._repo is None:
            return
        active = self._repo.active_branch
        for b in self._repo.all_branches():
            a = menu.addAction(b.name)
            a.setCheckable(True)
            a.setChecked(b.name == active)
            if b.name != active:
                a.triggered.connect(
                    lambda _=False, n=b.name: self._checkout_branch(n)
                )

    @staticmethod
    def _chip(text: str, kind: str = "") -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("StatusChip")
        if kind:
            lbl.setProperty("chip", kind)
        lbl.setVisible(False)
        return lbl

    @staticmethod
    def _chip_dot(color: str):
        """Chip avec pastille colorée : renvoie (conteneur, label du texte)."""
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        dot = QLabel()
        dot.setObjectName("StatusDot")
        dot.setFixedSize(6, 6)
        dot.setStyleSheet(
            f"QLabel#StatusDot {{ background-color: {color}; border-radius: 3px; }}"
        )
        txt = QLabel("")
        txt.setObjectName("StatusChip")
        lay.addWidget(dot)
        lay.addWidget(txt)
        w.setVisible(False)
        return w, txt

    def _set_actions_enabled(self, enabled: bool) -> None:
        for a in self._toolbar.actions():
            if a.isSeparator():
                continue
            if not a.text():
                continue  # action de widget (spacer)
            if a in self._actions_to_keep:
                continue
            a.setEnabled(enabled)
        self._branch_btn.setEnabled(enabled)
        for btn in (
            self._btn_stage_all,
            self._btn_unstage_all,
            self._btn_commit,
            self._btn_push,
        ):
            btn.setEnabled(enabled)

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

    def _build_right_panel(self) -> QWidget:
        """Panneau de droite : Changes + workflow (Index → Commit → Push)."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(6)
        title = QLabel("Changes")
        title.setObjectName("PanelTitle")
        header.addWidget(title)
        self._changes_count = QLabel("0")
        self._changes_count.setObjectName("HeaderCount")
        self._changes_count.setVisible(False)
        header.addWidget(self._changes_count)
        header.addStretch(1)

        self._btn_stage_all = self._push_btn(
            _icon("stage-all"), "Stage All", "Stage all changes (Ctrl+S)"
        )
        self._btn_stage_all.setObjectName("PanelAction")
        self._btn_stage_all.clicked.connect(self._stage_all)
        self._btn_unstage_all = self._push_btn(
            _icon("unstage-all"), "Unstage All", "Unstage all changes"
        )
        self._btn_unstage_all.setObjectName("PanelAction")
        self._btn_unstage_all.clicked.connect(self._unstage_all)
        header.addWidget(self._btn_stage_all)
        header.addWidget(self._btn_unstage_all)
        layout.addLayout(header)

        layout.addWidget(self.files, 1)

        box = QFrame()
        box.setObjectName("WorkflowBox")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(12, 8, 12, 10)
        box_layout.setSpacing(8)

        strip = QHBoxLayout()
        strip.setSpacing(6)
        self._wf_labels: dict = {}
        for key, text in (
            ("index", "1 · Index"),
            ("commit", "2 · Commit"),
            ("push", "3 · Push"),
        ):
            lbl = QLabel(text)
            lbl.setObjectName("WorkflowStep")
            strip.addWidget(lbl)
            self._wf_labels[key] = lbl
            if key != "push":
                arr = QLabel("→")
                arr.setObjectName("WorkflowArrow")
                strip.addWidget(arr)
        strip.addStretch(1)
        box_layout.addLayout(strip)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self._btn_commit = self._push_btn(
            _icon("commit"), "Commit", "Create a commit (Ctrl+Return)"
        )
        self._btn_commit.setObjectName("PanelCommit")
        self._btn_commit.clicked.connect(self._open_commit_dialog)
        self._btn_push = self._push_btn(
            _icon("push"), "Push", "Push local commits (Ctrl+P)"
        )
        self._btn_push.setObjectName("PanelPush")
        self._btn_push.clicked.connect(self._push)
        actions.addWidget(self._btn_commit, 2)
        actions.addWidget(self._btn_push, 1)
        box_layout.addLayout(actions)

        layout.addWidget(box)
        return panel

    @staticmethod
    def _push_btn(icon: QIcon, text: str, tip: str) -> QPushButton:
        btn = QPushButton(icon, text)
        btn.setToolTip(tip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _update_workflow(self, unstaged: int, staged: int) -> None:
        """Met en évidence l'étape suivante du workflow dans le panneau droit."""
        steps = {"index": unstaged > 0, "commit": staged > 0, "push": False}
        if self._repo is not None:
            status = self._repo.upstream_status()
            if status:
                steps["push"] = status[0] > 0
        for key, lbl in self._wf_labels.items():
            lbl.setProperty("active", steps[key])
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)

    def load_repo(self, path: str) -> bool:
        """Charge un dépôt : active la toolbar puis rafraîchit l'affichage."""
        try:
            repo = GitRepo(path)
        except GitMatrixError as exc:
            QMessageBox.critical(self, "GitMatrix", str(exc))
            return False
        self._repo = repo
        self.branches.set_repo(repo)
        self._set_actions_enabled(True)
        self._refresh()
        return True

    def _open_repo(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose a Git repository")
        if path:
            self.load_repo(path)

    def _clone_repo(self) -> None:
        dialog = CloneDialog(self)
        if not dialog.exec():
            return
        url, dest = dialog.values()
        if not url or not dest:
            QMessageBox.warning(
                self, "Clone", "URL and destination are required."
            )
            return
        try:
            repo = GitRepo.clone(url, dest)
        except GitMatrixError as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return
        self.load_repo(repo.path)

    def _refresh(self) -> None:
        if self._repo is None:
            return
        try:
            self.commit_graph.set_repo(self._repo)
            self.branches.refresh()
            self._refresh_branch_menu()
            self.files.set_changes(self._repo.changes())
        except GitMatrixError as exc:
            QMessageBox.warning(self, "Error", str(exc))
        self._update_status()

    def _on_commit_selected(self, commit) -> None:
        self._update_status(commit=commit)

    def _open_commit_detail(self, commit) -> None:
        """Double-clic sur un commit : fenêtre détaillée (fichiers + stats + diff)."""
        if self._repo is None:
            return
        try:
            diffs = self._repo.diff_commit(commit.hexsha)
        except GitMatrixError as exc:
            QMessageBox.warning(self, "Error", str(exc))
            return
        dialog = CommitDetailDialog(commit, diffs, self)
        dialog.exec()

    def _open_file_diff(self, file_change: FileChange) -> None:
        """Double-clic sur un fichier : ouvre son diff dans une fenêtre."""
        if self._repo is None:
            return
        diff = self._repo.diff(file_change.path)
        scope = "staged" if file_change.staged else "working tree"
        DiffDialog(diff, f"{file_change.path}  ({scope})", self).exec()

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
            QMessageBox.information(self, "GitMatrix", "Open a repository first.")
            return
        if not any(c.staged for c in self._repo.changes()):
            QMessageBox.information(
                self,
                "GitMatrix",
                "No staged changes to commit.\nStage some files first (Step 1 · Index).",
            )
            return
        dialog = CommitDialog(self)
        if dialog.exec():
            try:
                new_sha = self._repo.commit_all(dialog.message())
                self.commit_graph.select_commit(new_sha)
            except GitMatrixError as exc:
                QMessageBox.critical(self, "Error", str(exc))
        self._refresh()

    def _checkout_branch(self, name: str) -> None:
        if self._repo is None:
            return
        try:
            self._repo.checkout(name)
        except GitMatrixError as exc:
            QMessageBox.critical(self, "Error", str(exc))
        self._refresh()

    def _fetch(self) -> None:
        if self._repo is None:
            QMessageBox.information(self, "GitMatrix", "Open a repository first.")
            return
        try:
            output = self._repo.fetch()
        except GitMatrixError as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return
        self._refresh()
        self.status.showMessage(f"Fetch completed: {output}", 8000)

    def _push(self) -> None:
        if self._repo is None:
            QMessageBox.information(self, "GitMatrix", "Open a repository first.")
            return
        status = self._repo.upstream_status()
        if status is not None and status[0] <= 0:
            QMessageBox.information(
                self, "GitMatrix", "Nothing to push — local branch is up to date."
            )
            return
        try:
            output = self._repo.push()
        except GitMatrixError as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return
        self._refresh()
        self.status.showMessage(f"Push completed: {output}", 8000)

    def _pull(self) -> None:
        if self._repo is None:
            QMessageBox.information(self, "GitMatrix", "Open a repository first.")
            return
        try:
            output = self._repo.pull()
        except GitMatrixError as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return
        self._refresh()
        self.status.showMessage(f"Pull completed: {output}", 8000)

    def _open_about(self) -> None:
        AboutDialog(self).exec()

    def _on_theme_changed(self) -> None:
        """Recharge les couleurs cachées (graphe, branches) après un changement."""
        self.setStyleSheet(current_qss())
        if self._repo is not None:
            self._refresh()

    def _open_settings(self) -> None:
        # Fenêtre non-modale : une fenêtre modale (exec) active la boucle
        # modale native de l'OS qui bloque l'entrée de toute autre fenêtre —
        # l'aperçu splash plein écran ne pourrait jamais recevoir le clic
        # « Lancer ».  Avec show(), le splash est cliquable et fonctionne.
        if getattr(self, "_settings_dialog", None) is not None:
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
            return
        dlg = SettingsDialog(self)
        self._settings_dialog = dlg
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dlg.destroyed.connect(lambda: setattr(self, "_settings_dialog", None))
        dlg.show()

    def _update_status(self, commit=None) -> None:
        if self._repo is None:
            self._sb_commit.setText("No repository open")
            self._sb_branch.setVisible(False)
            self._sb_dirty.setVisible(False)
            self._sb_staged_w.setVisible(False)
            self._sb_unstaged_w.setVisible(False)
            return

        branch = self._repo.active_branch or "(detached)"
        self._sb_branch.setText(branch)
        self._sb_branch.setVisible(True)
        self._branch_btn.setText(self._repo.active_branch or "Branch")

        changes = self._repo.changes()
        n_staged = sum(1 for c in changes if c.staged)
        n_unstaged = len(changes) - n_staged

        if self._repo.is_dirty():
            total = n_staged + n_unstaged
            self._sb_dirty.setText(f"● {total} modification{'s' if total > 1 else ''}")
            self._sb_dirty.setVisible(True)
        else:
            self._sb_dirty.setText("")
            self._sb_dirty.setVisible(False)

        self._sb_staged.setText(f"{n_staged} staged")
        self._sb_unstaged.setText(f"{n_unstaged} unstaged")
        self._sb_staged_w.setVisible(n_staged > 0)
        self._sb_unstaged_w.setVisible(n_unstaged > 0)

        total = n_staged + n_unstaged
        self._changes_count.setText(str(total))
        self._changes_count.setVisible(total > 0)
        self._update_workflow(n_unstaged, n_staged)

        if commit is not None:
            self._sb_commit.setText(f"{commit.short_sha}  {commit.subject}")
        else:
            self._sb_commit.setText("")
