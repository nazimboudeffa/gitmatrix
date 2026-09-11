"""Fenêtre de détail d'un commit : fichiers modifiés, stats et diff navigable."""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from gitmatrix.core.git_repo import CommitInfo, FileDiff
from gitmatrix.widgets.diff_viewer import DiffViewer

STATUS_COLORS = {
    "A": "#98c379",
    "M": "#d19a66",
    "D": "#e06c75",
    "R": "#61afef",
    "C": "#61afef",
}


def _file_stats(d: FileDiff) -> tuple:
    """Compte les lignes ajoutées/supprimées depuis les hunks du diff."""
    added = sum(1 for h in d.hunks if h["type"] == "add")
    deleted = sum(1 for h in d.hunks if h["type"] == "del")
    return added, deleted


def _mono_font() -> QFont:
    f = QFont("Cascadia Mono")
    f.setStyleHint(QFont.StyleHint.Monospace)
    f.setPointSize(9)
    return f


class CommitDetailDialog(QDialog):
    """Liste les fichiers d'un commit avec leurs statistiques et un diff navigable."""

    def __init__(self, commit: CommitInfo, diffs: List[FileDiff], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Commit {commit.short_sha}")
        self.resize(960, 600)
        self._diffs = diffs

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        subject = QLabel(commit.subject)
        subject.setObjectName("CommitDetailDialogSubject")
        subject.setWordWrap(True)
        layout.addWidget(subject)

        total_add = sum(_file_stats(d)[0] for d in diffs)
        total_del = sum(_file_stats(d)[1] for d in diffs)
        meta = QLabel(
            f"{commit.short_sha}  ·  {commit.author_name}  ·  "
            f"{commit.authored_datetime or '-'}  ·  {len(diffs)} file(s)  ·  "
            f"+{total_add}  −{total_del}"
        )
        meta.setObjectName("CommitDetailDialogMeta")
        layout.addWidget(meta)

        split = QSplitter(Qt.Orientation.Horizontal)
        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._show_file)
        split.addWidget(self._list)
        self._diff = DiffViewer()
        split.addWidget(self._diff)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 3)
        layout.addWidget(split, 1)

        self._populate()
        if diffs:
            self._list.setCurrentRow(0)

    # ------------------------------------------------------------------
    def _populate(self) -> None:
        for d in self._diffs:
            status = "D" if d.is_deleted else ("A" if d.is_new else "M")
            added, deleted = _file_stats(d)
            row = self._make_row(d.path, status, added, deleted)
            item = QListWidgetItem()
            item.setSizeHint(row.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, row)

    @staticmethod
    def _make_row(path: str, status: str, added: int, deleted: int) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(10, 4, 10, 4)
        lay.setSpacing(8)

        letter = QLabel(status)
        letter.setFont(_mono_font())
        letter.setStyleSheet(
            f"color:{STATUS_COLORS.get(status, '#d7dae0')}; font-weight:700; background:transparent;"
        )
        lay.addWidget(letter)

        path_lbl = QLabel(path)
        path_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        lay.addWidget(path_lbl, 1)

        if added or deleted:
            stats = QHBoxLayout()
            stats.setSpacing(4)
            add_lbl = QLabel(f"+{added}")
            add_lbl.setStyleSheet("color:#98c379; background:transparent;")
            del_lbl = QLabel(f"−{deleted}")
            del_lbl.setStyleSheet("color:#e06c75; background:transparent;")
            for lbl in (add_lbl, del_lbl):
                lbl.setFont(_mono_font())
                stats.addWidget(lbl)
            lay.addLayout(stats)
        else:
            bin_lbl = QLabel("bin")
            bin_lbl.setFont(_mono_font())
            bin_lbl.setStyleSheet("color:#9da5b4; background:transparent;")
            lay.addWidget(bin_lbl)

        return w

    def _show_file(self, row: int) -> None:
        if not (0 <= row < len(self._diffs)):
            return
        d = self._diffs[row]
        added, deleted = _file_stats(d)
        self._diff.show_diff(d, title=f"{d.path}  +{added}  −{deleted}")