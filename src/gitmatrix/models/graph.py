"""Modèle de données et calcul de disposition pour le graphe des commits."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from gitmatrix.core.git_repo import CommitInfo, RefInfo


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

    Algorithme inspiré de ``git log --graph``, adapté pour rester propre même
    quand plusieurs personnes travaillent sur le dépôt :

    - Les commits arrivent en **ordre topologique** (un commit avant ses parents).
    - Une lane est une « attente » : elle contient le hash du commit attendu
      plus bas. ``None`` = lane libre.
    - Chaque commit prend la première lane qui l'attend ; sinon il ouvre une
      nouvelle lane.
    - Quand un commit est consommé, **toutes** les lanes qui l'attendaient sont
      libérées (évite les lignes fantômes héritées d'un parent partagé).
    - Le premier parent hérite de la lane du commit ; les parents suivants
      réutilisent une lane qui attend déjà ce hash, sinon prennent la lane
      libre la plus proche à droite, sinon une nouvelle lane à la fin.
    """

    def __init__(
        self,
        commits: List[CommitInfo],
        ref_map: Optional[Dict[str, List[RefInfo]]] = None,
    ):
        self.commits = commits
        self.ref_map = ref_map or {}
        self.columns: Dict[str, int] = {}
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.max_columns = 0
        self._build()

    def _build(self) -> None:
        lanes: List[Optional[str]] = []

        for commit in self.commits:
            sha = commit.hexsha

            # 1. Lane qui attend ce commit ; sinon nouvelle lane
            col = self._find_lane(lanes, sha)
            if col is None:
                lanes.append(sha)
                col = len(lanes) - 1
            self.columns[sha] = col
            self.max_columns = max(self.max_columns, col + 1)

            # 2. Consommer TOUTES les lanes qui attendaient ce commit
            #    (une même branche peut avoir réservé le parent plusieurs fois).
            freeing = [i for i, w in enumerate(lanes) if w == sha]
            for i in freeing:
                lanes[i] = None

            # 3. Réserver les parents
            for pi, parent in enumerate(commit.parents):
                if pi == 0:
                    # Premier parent : reprend la lane du commit
                    if lanes[col] is None:
                        lanes[col] = parent
                        continue
                    # case rare : la lane a été reprise entre-temps
                    lanes[self._take_slot(lanes, col)] = parent
                else:
                    # Parents merge : réutiliser une lane qui les attend déjà
                    existing = self._find_lane(lanes, parent)
                    if existing is None:
                        lanes[self._take_slot(lanes, col)] = parent

        # 4. Nœuds avec leurs refs
        for commit in self.commits:
            col = self.columns.get(commit.hexsha, 0)
            refs = self.ref_map.get(commit.hexsha, [])
            self.nodes[commit.hexsha] = GraphNode(commit=commit, column=col, refs=refs)

        # 5. Arêtes
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

    def _find_lane(self, lanes: List[Optional[str]], sha: str) -> Optional[int]:
        """Index de la première lane qui attend ce sha, sinon None."""
        for i, w in enumerate(lanes):
            if w == sha:
                return i
        return None

    def _find_free_lane(self, lanes: List[Optional[str]], prefer: Optional[int] = None) -> Optional[int]:
        """Lane libre la plus proche de `prefer` (d'abord à droite, puis à gauche)."""
        if not lanes:
            return None
        if prefer is not None and lanes[prefer] is None:
            return prefer
        n = len(lanes)
        for offset in range(1, n):
            right = prefer + offset if prefer is not None else offset
            left = prefer - offset if prefer is not None else None
            if right is not None and right < n and lanes[right] is None:
                return right
            if left is not None and left >= 0 and lanes[left] is None:
                return left
        return None

    def _take_slot(self, lanes: List[Optional[str]], prefer: int) -> int:
        """Réserve un emplacement pour un parent : lane libre proche, sinon nouvelle lane."""
        slot = self._find_free_lane(lanes, prefer)
        if slot is None:
            lanes.append(None)
            slot = len(lanes) - 1
        self.max_columns = max(self.max_columns, slot + 1)
        return slot