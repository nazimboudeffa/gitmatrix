"""Modèle de données et calcul de disposition pour le graphe des commits."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from gitmatrix.core.git_repo import CommitInfo, GitRepo, RefInfo


@dataclass
class GraphNode:
    """Nœud du graphe (un commit positionné)."""

    commit: CommitInfo
    column: int = 0
    refs: List[RefInfo] = field(default_factory=list)


@dataclass
class GraphEdge:
    """Arête reliant un commit enfant à son parent."""

    child: GraphNode
    parent: GraphNode
    child_column: int = 0
    parent_column: int = 0


class GraphLayout:
    """Attribue une colonne (lane) à chaque commit puis construit les arêtes.

    Algorithme façon ``git log --graph`` :
    - Une liste de lanes parcourue du haut vers le bas (fait le plus récent
      au plus ancien).
    - Chaque extrémité de branche (tip) ouvre une nouvelle lane.
    - Un parent est placé dans l'ancienne lane de son enfant ; les parents
      suivants (merges) ouvrent de nouvelles lanes.
    """

    def __init__(self, commits: List[CommitInfo], repo: Optional[GitRepo] = None):
        self.commits = commits
        self.repo = repo
        self.columns: Dict[str, int] = {}
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.max_columns = 0
        self._build()

    def _build(self) -> None:
        # lanes : liste de sha "attendus" dans une colonne ; None = libre
        lanes: List[Optional[str]] = []

        for commit in self.commits:
            sha = commit.hexsha

            # Emplacement de ce commit : première lane qui l'attend sinon nouvelle lane
            col = None
            for idx, waiting in enumerate(lanes):
                if waiting == sha:
                    col = idx
                    break
            if col is None:
                lanes.append(sha)
                col = len(lanes) - 1
            self.columns[sha] = col
            self.max_columns = max(self.max_columns, col + 1)

            lanes[col] = None  # la lane est consommée par ce commit

            # Parents : le premier hérite de la lane, les autres en ouvrent de nouvelles
            for parent_idx, parent_sha in enumerate(commit.parents):
                if parent_idx == 0:
                    lanes[col] = parent_sha
                else:
                    # lane libre la plus proche, sinon nouvelle
                    free = None
                    for i, w in enumerate(lanes):
                        if w is None:
                            free = i
                            break
                    if free is None:
                        lanes.append(parent_sha)
                        free = len(lanes) - 1
                    else:
                        lanes[free] = parent_sha
                    self.max_columns = max(self.max_columns, free + 1)

        # Construction des nœuds avec les refs
        for commit in self.commits:
            col = self.columns.get(commit.hexsha, 0)
            refs = self.repo.refs_of_sha(commit.hexsha) if self.repo else []
            self.nodes[commit.hexsha] = GraphNode(commit=commit, column=col, refs=refs)

        # Construction des arêtes
        for commit in self.commits:
            child = self.nodes.get(commit.hexsha)
            if child is None:
                continue
            cc = self.columns.get(commit.hexsha, 0)
            for parent_sha in commit.parents:
                parent = self.nodes.get(parent_sha)
                if parent is None:
                    continue
                pc = self.columns.get(parent_sha, 0)
                self.edges.append(
                    GraphEdge(
                        child=child,
                        parent=parent,
                        child_column=cc,
                        parent_column=pc,
                    )
                )