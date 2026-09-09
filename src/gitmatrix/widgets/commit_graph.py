"""Widget du graphe des commits (rendu visuel de l'historique Git)."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QAbstractScrollArea, QToolTip

from gitmatrix.core.git_repo import CommitInfo, GitRepo, RefInfo
from gitmatrix.models.graph import GraphLayout, GraphNode
from gitmatrix.theme import COLOR_PALETTE

ROW_HEIGHT = 30
COLUMN_WIDTH = 22
LEFT_PADDING = 16
NODE_RADIUS = 8  # agrandi (6 → 8) pour une meilleure visée
SELECT_RING = 5  # anneau de sélection autour du nœud


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
        self._row_index: dict = {}  # hexsha -> index de ligne (rapide au dessin)
        self._commit_colors: dict = {}  # hexsha -> couleur de SA branche
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

    @property
    def hovered_commit(self) -> Optional[CommitInfo]:
        if self._hovered_sha is None or not self._entries:
            return None
        for e in self._entries:
            if e.commit.hexsha == self._hovered_sha:
                return e.commit
        return None

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------
    def _reload(self) -> None:
        self._entries = []
        self._row_index = {}
        self._hovered_sha = None
        if self._repo is None:
            self._update_geometry()
            return
        commits = self._repo.walk_commits()
        ref_map = self._repo.ref_map_by_commit()
        layout = GraphLayout(commits, ref_map)
        self._layout = layout

        for idx, commit in enumerate(commits):
            node = layout.nodes.get(commit.hexsha)
            if node is None:
                node = GraphNode(commit=commit, column=0)
            self._entries.append(node)
            self._row_index[commit.hexsha] = idx

        self._assign_colors(layout)

        self._colors.clear()
        for i in range(max(1, layout.max_columns)):
            self._colors[i] = QColor(COLOR_PALETTE[i % len(COLOR_PALETTE)])

        self._update_geometry()

    def _assign_colors(self, layout: GraphLayout) -> None:
        """Couleur stable PAR BRANCHE (façon GitKraken).

        Chaque extrémité de branche (commit porteur d'une ref branch/head)
        reçoit une couleur de la palette dans l'ordre où elle apparaît (le
        plus récent d'abord), puis cette couleur descend le long de sa lignée
        (premier parent). Un commit déjà coloré n'est pas recoloré.
        """
        if not self._entries:
            self._commit_colors = {}
            return
        palette = [QColor(h) for h in COLOR_PALETTE]
        commit_by_sha = {e.commit.hexsha: e.commit for e in self._entries}
        tips = [
            e
            for e in self._entries
            if any(r.kind in ("branch", "head") for r in e.refs)
        ]
        colors: dict = {}
        for i, tip in enumerate(tips):
            color = palette[i % len(palette)]
            sha = tip.commit.hexsha
            while sha in commit_by_sha and sha not in colors:
                colors[sha] = color
                parents = commit_by_sha[sha].parents
                sha = parents[0] if parents else None
        # filet de sécurité : commit sans branche visible (rare)
        for e in self._entries:
            if e.commit.hexsha not in colors:
                colors[e.commit.hexsha] = palette[e.column % len(palette)]
        self._commit_colors = colors

    def _color_of(self, entry: GraphNode) -> QColor:
        return self._commit_colors.get(
            entry.commit.hexsha, self._colors.get(entry.column, QColor("#61afef"))
        )

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
                "Aucun commit à afficher.",
            )
            return

        # Plage de rangées visibles (pour ne pas peindre les milliers d'autres)
        v = self.verticalScrollBar().value()
        first = max(0, v // ROW_HEIGHT - 1)
        last = min(len(self._entries), (v + self.viewport().height()) // ROW_HEIGHT + 1)
        visible = range(first, last)

        painter.translate(
            LEFT_PADDING - self.horizontalScrollBar().value(),
            -v,
        )

        self._paint_edges(painter, visible)
        for idx in visible:
            self._paint_node(painter, self._entries[idx], idx)

    def _paint_edges(self, painter: QPainter, visible_range) -> None:
        if not self._layout:
            return
        first = visible_range.start
        last = visible_range.stop
        for edge in self._layout.edges:
            child, parent = edge.child, edge.parent
            cy = self._row_index.get(child.commit.hexsha, 0) * ROW_HEIGHT + ROW_HEIGHT / 2
            py = self._row_index.get(parent.commit.hexsha, 0) * ROW_HEIGHT + ROW_HEIGHT / 2
            if (cy < (first - 1) * ROW_HEIGHT or cy > (last + 1) * ROW_HEIGHT) and (
                py < (first - 1) * ROW_HEIGHT or py > (last + 1) * ROW_HEIGHT
            ):
                continue
            cx = (child.column + 1) * COLUMN_WIDTH
            px = (parent.column + 1) * COLUMN_WIDTH

            color = self._color_of(child)
            pen = QPen(color, 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)

            if px == cx:
                # Ligne verticale directe (même lane)
                painter.drawLine(int(cx), int(cy), int(px), int(py))
                continue

            # Gabarit « carré » (à la GitKraken) : descente verticale, trait
            # horizontal à angle droit, puis remontée verticale jusqu'au parent.
            mid_y = (cy + py) / 2
            path = QPainterPath(QPointF(cx, cy))
            path.lineTo(cx, mid_y)
            path.lineTo(px, mid_y)
            path.lineTo(px, py)
            painter.drawPath(path)

    def _paint_node(self, painter: QPainter, entry: GraphNode, idx: int) -> None:
        row = self._row_index.get(entry.commit.hexsha, 0)
        y = row * ROW_HEIGHT + ROW_HEIGHT / 2
        x = (entry.column + 1) * COLUMN_WIDTH
        color = self._color_of(entry)

        # Anneau de sélection (or)
        if entry.commit.hexsha == self._selected_sha:
            painter.setPen(QPen(QColor("#e5c07b"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(
                QRectF(
                    x - NODE_RADIUS - SELECT_RING,
                    y - NODE_RADIUS - SELECT_RING,
                    (NODE_RADIUS + SELECT_RING) * 2,
                    (NODE_RADIUS + SELECT_RING) * 2,
                )
            )

        # Halo du survol (fond légèrement plus clair)
        if entry.commit.hexsha == self._hovered_sha and entry.commit.hexsha != self._selected_sha:
            painter.setPen(QPen(color.lighter(125), 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(
                QRectF(
                    x - NODE_RADIUS - SELECT_RING - 1,
                    y - NODE_RADIUS - SELECT_RING - 1,
                    (NODE_RADIUS + SELECT_RING + 1) * 2,
                    (NODE_RADIUS + SELECT_RING + 1) * 2,
                )
            )

        painter.setPen(QPen(color, 2))
        painter.setBrush(color.darker(140))
        painter.drawEllipse(
            QRectF(x - NODE_RADIUS, y - NODE_RADIUS, NODE_RADIUS * 2, NODE_RADIUS * 2)
        )

        # point central
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        inner = max(2, NODE_RADIUS - 3)
        painter.drawEllipse(QRectF(x - inner, y - inner, inner * 2, inner * 2))

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
        # Position des badges positionnée dynamiquement, après le texte du commit
        subject_w = painter.fontMetrics().horizontalAdvance(entry.commit.subject or "")
        label_x = x0 + min(subject_w + 60, 560)
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
        return self._row_index.get(entry.commit.hexsha, 0)

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
    # Tooltip
    # ------------------------------------------------------------------
    def _show_tooltip(self, sha: str) -> None:
        commit = self._find_commit(sha)
        if commit is None:
            return
        refs = ""
        for e in self._entries:
            if e.commit.hexsha == sha:
                labels = [
                    "HEAD" if r.kind == "head" else r.name for r in e.refs
                ]
                refs = f"  [{', '.join(labels)}]" if labels else ""
                break
        lines = [
            f"{commit.subject}",
            f"   {commit.author_name}  ·  {self._format_date(commit)}",
            f"   {commit.short_sha}{refs}",
        ]
        if len(commit.message) > len(commit.subject):
            extra = commit.message[len(commit.subject) :].strip()
            if extra:
                lines.append("   " + extra.replace("\n", "\n   "))
        QToolTip.showText(
            self.viewport().mapToGlobal(self.viewport().rect().center()),
            "\n".join(lines),
            self,
        )

    # ------------------------------------------------------------------
    # Événements
    # ------------------------------------------------------------------
    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.viewport().update()

    def scrollContentsBy(self, dx, dy) -> None:  # noqa: N802
        # Déplacement pixel des pixels déjà affichés : seules les bandes
        # nouvellement exposées sont repeintes (bien plus fluide au scroll).
        self.viewport().scroll(dx, dy)
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
            if sha is not None:
                self._show_tooltip(sha)
            else:
                QToolTip.hideText()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hovered_sha = None
        QToolTip.hideText()
        self.viewport().update()
        super().leaveEvent(event)

    def _update_scrollbars(self) -> None:
        self.verticalScrollBar().setRange(0, max(0, self._content_height - self.viewport().height()))
        self.horizontalScrollBar().setRange(0, max(0, self._content_width - self.viewport().width()))
