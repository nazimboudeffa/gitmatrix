"""Widget du graphe des commits (rendu visuel de l'historique Git)."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QAbstractScrollArea

from gitmatrix.core.git_repo import CommitInfo, GitRepo, RefInfo
from gitmatrix.models.graph import GraphLayout, GraphNode

ROW_HEIGHT = 30
COLUMN_WIDTH = 22
LEFT_PADDING = 16
NODE_RADIUS = 6
COLOR_PALETTE = [
    "#e06c75",  # rouge
    "#61afef",  # bleu
    "#98c379",  # vert
    "#e5c07b",  # jaune
    "#c678dd",  # violet
    "#56b6c2",  # cyan
    "#d19a66",  # orange
    "#ff7eb6",  # rose
    "#6c8cff",  # indigo
    "#7bd88f",  # vert clair
]


class CommitGraphWidget(QAbstractScrollArea):
    """Aire de défilement affichant le graphe des commits."""

    commit_selected = Signal(object)
    commit_activated = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.viewport().setMouseTracking(True)

        self._repo: Optional[GitRepo] = None
        self._layout: Optional[GraphLayout] = None
        self._entries: List[GraphNode] = []
        self._selected_sha: Optional[str] = None
        self._hovered_sha: Optional[str] = None
        self._colors: dict = {}
        self._content_width = 0
        self._content_height = 0

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------
    def set_repo(self, repo: GitRepo) -> None:
        self._repo = repo
        self._reload()
        self.viewport().update()

    def reload(self) -> None:
        self._reload()
        self.viewport().update()

    def select_commit(self, hexsha: Optional[str]) -> None:
        self._selected_sha = hexsha
        self.viewport().update()

    @property
    def selected_commit(self) -> Optional[CommitInfo]:
        if self._selected_sha is None or not self._entries:
            return None
        for e in self._entries:
            if e.commit.hexsha == self._selected_sha:
                return e.commit
        return None

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------
    def _reload(self) -> None:
        self._entries = []
        if self._repo is None:
            self._update_geometry()
            return
        commits = self._repo.walk_commits()
        layout = GraphLayout(commits, self._repo)
        self._layout = layout

        for commit in commits:
            node = layout.nodes.get(commit.hexsha)
            if node is None:
                node = GraphNode(commit=commit, column=0)
            self._entries.append(node)

        self._colors.clear()
        for i in range(max(1, layout.max_columns)):
            self._colors[i] = QColor(COLOR_PALETTE[i % len(COLOR_PALETTE)])

        self._update_geometry()

    def _update_geometry(self) -> None:
        if not self._layout or not self._entries:
            self._content_width = 0
            self._content_height = 0
            return
        max_cols = max(1, self._layout.max_columns)
        width = LEFT_PADDING + (max_cols + 3) * COLUMN_WIDTH + 700
        height = len(self._entries) * ROW_HEIGHT + ROW_HEIGHT
        self._content_width = width
        self._content_height = height
        self._update_scrollbars()

    def _update_scrollbars(self) -> None:
        self.verticalScrollBar().setRange(
            0, max(0, self._content_height - self.viewport().height())
        )
        self.horizontalScrollBar().setRange(
            0, max(0, self._content_width - self.viewport().width())
        )

    # ------------------------------------------------------------------
    # Rendu
    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.viewport().rect(), QColor("#1e2127"))

        if not self._layout or not self._entries:
            painter.setPen(QColor("#9da5b4"))
            painter.drawText(
                self.viewport().rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Ouvrez un dépôt Git pour afficher l'historique.",
            )
            return

        painter.translate(
            LEFT_PADDING - self.horizontalScrollBar().value(),
            -self.verticalScrollBar().value(),
        )

        self._paint_edges(painter)
        for idx, entry in enumerate(self._entries):
            self._paint_node(painter, entry, idx)

    def _paint_edges(self, painter: QPainter) -> None:
        if not self._layout:
            return
        for edge in self._layout.edges:
            child, parent = edge.child, edge.parent
            cy = self._row_of(child) * ROW_HEIGHT + ROW_HEIGHT / 2
            py = self._row_of(parent) * ROW_HEIGHT + ROW_HEIGHT / 2
            cx = (child.column + 1) * COLUMN_WIDTH
            px = (parent.column + 1) * COLUMN_WIDTH

            color = self._colors.get(parent.column, QColor("#555"))
            pen = QPen(color, 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)

            if px == cx:
                painter.drawLine(int(cx), int(cy), int(px), int(py))
                continue

            mid_y = (cy + py) / 2
            path = QPainterPath()
            path.moveTo(cx, cy)
            path.cubicTo(cx, mid_y, px, mid_y, px, py)
            painter.drawPath(path)

    def _paint_node(self, painter: QPainter, entry: GraphNode, idx: int) -> None:
        row = self._row_of(entry)
        y = row * ROW_HEIGHT + ROW_HEIGHT / 2
        x = (entry.column + 1) * COLUMN_WIDTH
        color = self._colors.get(entry.column, QColor("#61afef"))

        if entry.commit.hexsha == self._selected_sha:
            painter.setPen(QPen(QColor("#e5c07b"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(
                QRectF(x - NODE_RADIUS - 5, y - NODE_RADIUS - 5,
                       (NODE_RADIUS + 5) * 2, (NODE_RADIUS + 5) * 2)
            )

        painter.setPen(QPen(color, 2))
        painter.setBrush(color.darker(140))
        painter.drawEllipse(
            QRectF(x - NODE_RADIUS, y - NODE_RADIUS,
                   NODE_RADIUS * 2, NODE_RADIUS * 2)
        )

        text_x = x + NODE_RADIUS + 8
        if text_x > self._content_width:
            return

        font = QFont(self.font())
        font.setPointSize(10)
        is_head = any(r.kind == "head" for r in entry.refs)
        if is_head:
            font.setBold(True)
        painter.setFont(font)

        painter.setPen(QPen(QColor("#6b7381")))
        painter.drawText(
            QRectF(text_x, y - ROW_HEIGHT / 2 + 2, 420, 16),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            f"{entry.commit.author_name}  ·  {self._format_date(entry.commit)}",
        )

        painter.setPen(QPen(QColor("#d7dae0")))
        painter.drawText(
            QRectF(text_x, y - 2, 520, 22),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            entry.commit.subject or "…",
        )

        self._paint_refs(painter, entry, text_x, y)

    def _paint_refs(self, painter: QPainter, entry: GraphNode, x0: float, y: float) -> None:
        bg_map = {
            "head": QColor("#e5c07b"),
            "branch": QColor("#3f9e63"),
            "tag": QColor("#5c6470"),
            "remote": QColor("#7b61b8"),
        }
        fg_map = {
            "head": QColor("#1f2228"),
            "branch": QColor("#ffffff"),
            "tag": QColor("#ffffff"),
            "remote": QColor("#ffffff"),
        }

        offset = 0.0
        label_x = x0 + 250
        for ref in entry.refs:
            bg = bg_map.get(ref.kind, QColor("#5c6470"))
            fg = fg_map.get(ref.kind, QColor("#ffffff"))
            text = "HEAD" if ref.kind == "head" else ref.name

            m = painter.fontMetrics()
            w = m.horizontalAdvance(text) + 14
            h = m.height() + 4
            rect = QRectF(label_x + offset, y - h / 2, w, h)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(rect, 8, 8)

            painter.setPen(fg)
            painter.drawText(
                rect.adjusted(7, 0, -7, 0),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                text,
            )
            offset += w + 6

    # ------------------------------------------------------------------
    # Géométrie
    # ------------------------------------------------------------------
    def _row_of(self, entry: GraphNode) -> int:
        for idx, e in enumerate(self._entries):
            if e.commit.hexsha == entry.commit.hexsha:
                return idx
        return 0

    def _format_date(self, commit: CommitInfo) -> str:
        if not commit.committed_datetime:
            return ""
        return commit.committed_datetime[:10]

    def _sha_at(self, pos_y: float) -> Optional[str]:
        y = pos_y + self.verticalScrollBar().value()
        row = int(y // ROW_HEIGHT)
        if 0 <= row < len(self._entries):
            return self._entries[row].commit.hexsha
        return None

    def _find_commit(self, sha: str) -> Optional[CommitInfo]:
        for e in self._entries:
            if e.commit.hexsha == sha:
                return e.commit
        return None

    # ------------------------------------------------------------------
    # Événements
    # ------------------------------------------------------------------
    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.viewport().update()

    def scrollContentsBy(self, dx, dy) -> None:  # noqa: N802
        self.viewport().update()
        super().scrollContentsBy(dx, dy)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        sha = self._sha_at(event.position().y())
        if sha is not None:
            self._selected_sha = sha
            self.viewport().update()
            commit = self._find_commit(sha)
            if commit is not None:
                self.commit_selected.emit(commit)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        sha = self._sha_at(event.position().y())
        if sha is not None:
            commit = self._find_commit(sha)
            if commit is not None:
                self.commit_activated.emit(commit)
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        sha = self._sha_at(event.position().y())
        if sha != self._hovered_sha:
            self._hovered_sha = sha
            self.viewport().update()
        super().mouseMoveEvent(event)

    def _update_scrollbars(self) -> None:
        self.verticalScrollBar().setRange(0, max(0, self._content_height - self.viewport().height()))
        self.horizontalScrollBar().setRange(0, max(0, self._content_width - self.viewport().width()))