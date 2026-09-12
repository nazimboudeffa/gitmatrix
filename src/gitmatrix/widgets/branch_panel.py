"""Branch panel (overview + actions)."""

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
    QAbstractItemView,
)

from gitmatrix.core.git_repo import RefInfo, GitMatrixError
from gitmatrix.theme import current_color, branch_color_map, graph_color


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


class _SectionHeader(QWidget):
    """En-tête cliquable pour masquer / afficher une section."""

    clicked = Signal()

    def __init__(self, name: str, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("SectionHeader")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 14, 6)
        lay.setSpacing(8)
        muted = current_color("muted")
        self._arrow = QLabel("▾")
        self._arrow.setFixedWidth(8)
        self._arrow.setStyleSheet(
            f"color:{muted}; font-size:10px; font-weight:700; background:transparent;"
        )
        lay.addWidget(self._arrow)
        self._label = QLabel(name)
        f = QFont(self.font())
        f.setPointSize(10)
        f.setBold(True)
        self._label.setFont(f)
        self._label.setStyleSheet(f"color:{muted}; background:transparent;")
        lay.addWidget(self._label)
        lay.addStretch(1)

    def set_state(self, shown: bool) -> None:
        self._arrow.setText("▾" if shown else "▸")

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)


class BranchPanel(QListWidget):
    """Liste des branches avec menu contextuel (créer, supprimer, checkout)."""

    branch_checked = Signal(str)  # nom de branche

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self.itemDoubleClicked.connect(self._on_double_click)
        self._repo = None
        self._sections: dict = {}
        self._current_section: str = ""

    def _on_double_click(self, item) -> None:
        branch = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(branch, RefInfo) and branch.kind == "branch":
            self.branch_checked.emit(branch.name)

    def _toggle_section(self, name: str) -> None:
        sec = self._sections.get(name)
        if sec is None:
            return
        sec["shown"] = not sec["shown"]
        sec["header"].set_state(sec["shown"])
        for row in sec["rows"]:
            row.setHidden(not sec["shown"])
        self.scrollToItem(sec["item"], QAbstractItemView.ScrollHint.PositionAtTop)

    def _begin_section(self, name: str) -> None:
        self._current_section = name
        item = QListWidgetItem()
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        header = _SectionHeader(name)
        item.setSizeHint(header.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, header)
        header.clicked.connect(lambda n=name: self._toggle_section(n))
        self._sections[name] = {
            "header": header,
            "item": item,
            "rows": [],
            "shown": True,
        }
        item.setData(Qt.ItemDataRole.UserRole + 1, name)

    def _register_row(self, item) -> None:
        sec = self._sections.get(self._current_section)
        item.setData(Qt.ItemDataRole.UserRole + 1, self._current_section)
        if sec is not None:
            sec["rows"].append(item)

    def set_repo(self, repo) -> None:
        self._repo = repo

    def refresh(self) -> None:
        self.clear()
        if self._repo is None:
            return
        secondary = current_color("muted")
        self._begin_section("Local branches")
        active = self._repo.active_branch
        br_list = self._repo.all_branches()
        remotes = sorted(self._repo.all_remote_branches(), key=lambda x: x.name)
        color_map = branch_color_map(
            [b.name for b in br_list if b.name != active]
            + [r.name for r in remotes]
        )
        for b in br_list:
            is_active = b.name == active
            dot = (
                graph_color("accent")
                if is_active
                else color_map.get(b.name, secondary)
            )
            self._add_branch(b, dot, is_active)

        # Remote branches (display only, not editable)
        self._add_display_section(
            "Remotes",
            remotes,
            lambda name: color_map.get(name, secondary),
        )
        # Tags (display only, not editable)
        self._add_display_section(
            "Tags",
            sorted(self._repo.all_tags(), key=lambda x: x.name),
            secondary,
        )

    def _add_display_section(self, title: str, refs, color) -> None:
        if not refs:
            return
        self._begin_section(title)
        for r in refs:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, r)
            dot = color(r.name) if callable(color) else color
            row = self._row_widget(r.name, dot, False, None)
            item.setSizeHint(row.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, row)
            self._register_row(item)

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
        self._register_row(item)

    @staticmethod
    def _row_widget(name: str, dot: str, active: bool, status):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 6, 14, 6)
        lay.setSpacing(8)

        dot_lbl = QLabel()
        dot_lbl.setFixedSize(8, 8)
        dot_lbl.setPixmap(_dot_icon(dot, 8))
        lay.addWidget(dot_lbl)

        name_lbl = QLabel(name)
        if active:
            name_lbl.setStyleSheet(
                f"color:{graph_color('accent')}; font-weight:600; background:transparent;"
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
        section = None
        if item is not None:
            section = item.data(Qt.ItemDataRole.UserRole + 1)
        if section == "Local branches":
            menu.addAction("New branch…", self._new_branch)
        if item is not None:
            branch = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(branch, RefInfo) and branch.kind == "branch":
                menu.addAction(
                    "Switch (checkout)", lambda: self.branch_checked.emit(branch.name)
                )
                menu.addAction("Delete", lambda: self._delete_branch(branch.name))
        if menu.actions():
            menu.exec(self.mapToGlobal(pos))

    def _new_branch(self) -> None:
        if self._repo is None:
            return
        name, ok = QInputDialog.getText(self, "New branch", "Branch name:")
        if ok and name.strip():
            try:
                self._repo.create_branch(name.strip())
                self.refresh()
            except GitMatrixError as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def _delete_branch(self, name: str) -> None:
        res = QMessageBox.question(
            self,
            "Delete branch",
            f'Permanently delete branch "{name}"?',
        )
        if res == QMessageBox.StandardButton.Yes:
            try:
                self._repo.delete_branch(name)
                self.refresh()
            except GitMatrixError as exc:
                QMessageBox.critical(self, "Error", str(exc))