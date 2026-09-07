"""Couche d'accès à Git basée sur GitPython.

Ce module encapsule toutes les interactions avec le dépôt Git afin que
l'interface (UI) reste complètement découplée des détails de Git.
"""

from __future__ import annotations

import collections
from dataclasses import dataclass, field
from typing import List, Optional

import git
from git import Repo


@dataclass
class CommitInfo:
    """Représentation allégée et indépendante d'un commit pour l'UI."""

    hexsha: str
    short_sha: str
    message: str
    subject: str
    author_name: str
    author_email: str
    authored_datetime: Optional[str]
    committed_datetime: Optional[str]
    parents: List[str] = field(default_factory=list)
    # indices de ligne (position Y) dans le graphe
    row: int = 0


@dataclass
class RefInfo:
    """Référence (branche, tag, HEAD) associée à un commit."""

    name: str
    kind: str  # "head", "branch", "tag", "remote"
    target: str  # hexsha du commit pointé


@dataclass
class FileChange:
    """Changement d'un fichier dans le working tree ou l'index."""

    path: str
    staged: bool
    status: str  # A: added, M: modified, D: deleted, R: renamed, U: untracked


@dataclass
class FileDiff:
    """Résultat d'un diff pour l'affichage."""

    path: str
    is_new: bool
    is_deleted: bool
    hunks: List[dict] = field(default_factory=list)  # lignes avec info +/-/contexte


class GitMatrixError(RuntimeError):
    """Erreur applicative liée à Git (message clair pour l'utilisateur)."""


class GitRepo:
    """Façade orientée UI autour d'un dépôt Git."""

    def __init__(self, path: str) -> None:
        self.path = path
        try:
            self._repo = Repo(path)
        except git.InvalidGitRepositoryError:
            raise GitMatrixError(
                f"Aucun dépôt git trouvé à : {path}"
            ) from None
        except git.NoSuchPathError:
            raise GitMatrixError(f"Chemin invalide : {path}") from None

    # ------------------------------------------------------------------
    # Informations générales
    # ------------------------------------------------------------------
    def refs_of_sha(self, hexsha: str) -> List[RefInfo]:
        """Refs pointant vers un commit identifié par son hash."""
        try:
            commit = self._repo.commit(hexsha)
        except Exception:
            return []
        return self.refs_of(commit)

    @property
    def active_branch(self) -> Optional[str]:
        try:
            if self._repo.head.is_detached:
                return None
            return self._repo.active_branch.name
        except Exception:
            return None

    @property
    def repo_root(self) -> str:
        return self._repo.working_tree_dir or self._repo.git_dir

    def is_dirty(self) -> bool:
        return self._repo.is_dirty(untracked_files=True)

    # ------------------------------------------------------------------
    # Commits
    # ------------------------------------------------------------------
    def _commit_info(self, commit: git.Commit, row: int) -> CommitInfo:
        return CommitInfo(
            hexsha=commit.hexsha,
            short_sha=commit.hexsha[:8],
            message=commit.message.strip(),
            subject=(commit.message.strip().splitlines() or [""])[0],
            author_name=commit.author.name if commit.author else "?",
            author_email=commit.author.email if commit.author else "",
            authored_datetime=(
                commit.authored_datetime.isoformat()
                if commit.authored_datetime
                else None
            ),
            committed_datetime=(
                commit.committed_datetime.isoformat()
                if commit.committed_datetime
                else None
            ),
            parents=[p.hexsha for p in commit.parents],
            row=row,
        )

    def walk_commits(self, count: int = 1000) -> List[CommitInfo]:
        """Commits (plus récent en premier) couvrant toutes les refs.

        L'ordre utilise ``--topo-order`` : un commit est toujours listé avant
        ses parents, et les lignes de travail ne sont pas entremêlées. C'est
        indispensable à un rendu propre du graphe quand plusieurs personnes
        poussent sur le dépôt.
        """
        commits: List[CommitInfo] = []
        try:
            if self._repo.head.is_valid():
                for row, commit in enumerate(
                    self._repo.iter_commits(
                        rev="--all",
                        topo_order=True,
                        max_count=count,
                    )
                ):
                    commits.append(self._commit_info(commit, row))
        except Exception as exc:  # dépôt vide ou erreur
            if self._repo.head.is_valid():
                raise GitMatrixError(f"Impossible de lire l'historique : {exc}")
        return commits

    def commit(self, commit: git.Commit) -> CommitInfo:
        return self._commit_info(commit, 0)

    # ------------------------------------------------------------------
    # Refs (branches / HEAD / tags)
    # ------------------------------------------------------------------
    def refs_of(self, commit: git.Commit) -> List[RefInfo]:
        """Retourne les refs (branche, tag, HEAD) pointant vers ce commit."""
        refs: List[RefInfo] = []
        try:
            if self._repo.head.commit == commit:
                name = self.active_branch or "HEAD"
                refs.append(RefInfo(name=name, kind="head", target=commit.hexsha))
        except Exception:
            pass
        for branch in self._repo.branches:
            try:
                if branch.commit == commit:
                    refs.append(
                        RefInfo(name=branch.name, kind="branch", target=commit.hexsha)
                    )
            except Exception:
                continue
        for tag in self._repo.tags:
            try:
                target = tag.commit
                if target == commit:
                    refs.append(
                        RefInfo(name=tag.name, kind="tag", target=commit.hexsha)
                    )
            except Exception:
                continue
        return refs

    def all_branches(self) -> List[RefInfo]:
        result: List[RefInfo] = []
        for branch in self._repo.branches:
            try:
                result.append(
                    RefInfo(
                        name=branch.name,
                        kind="branch",
                        target=branch.commit.hexsha,
                    )
                )
            except Exception:
                continue
        return result

    def all_tags(self) -> List[RefInfo]:
        result: List[RefInfo] = []
        for tag in self._repo.tags:
            try:
                result.append(
                    RefInfo(name=tag.name, kind="tag", target=tag.commit.hexsha)
                )
            except Exception:
                continue
        return result

    # ------------------------------------------------------------------
    # Etat du working tree / index
    # ------------------------------------------------------------------
    def changes(self) -> List[FileChange]:
        """Liste des changements (staged + unstaged + untracked)."""
        result: List[FileChange] = []
        # Index vs HEAD (staged)
        try:
            for item in self._repo.index.diff("HEAD"):
                result.append(FileChange(path=item.a_path, staged=True, status=_status(item)))
        except Exception:
            pass
        # Working tree vs index (unstaged)
        try:
            for item in self._repo.index.diff(None):
                result.append(FileChange(path=item.a_path, staged=False, status=_status(item)))
        except Exception:
            pass
        # Untracked
        for uf in self._repo.untracked_files:
            result.append(FileChange(path=uf, staged=False, status="U"))
        return result

    # ------------------------------------------------------------------
    # Diff
    # ------------------------------------------------------------------
    def diff(self, path: str) -> FileDiff:
        """Diff d'un fichier (working tree vs HEAD si staged, sinon vs index)."""
        try:
            diffs = list(self._repo.index.diff(None, paths=[path]))
            is_staged = False
        except Exception:
            diffs = []
            is_staged = True
        if not diffs:
            try:
                diffs = list(self._repo.index.diff("HEAD", paths=[path]))
                is_staged = True
            except Exception:
                diffs = []

        if not diffs:
            return FileDiff(path=path, is_new=False, is_deleted=False)

        d = diffs[0]
        raw = d.diff
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        return FileDiff(
            path=path,
            is_new=bool(d.new_file),
            is_deleted=bool(d.deleted_file),
            hunks=_parse_diff(raw),
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def stage(self, path: str) -> None:
        self._repo.index.add([path])

    def unstage(self, path: str) -> None:
        try:
            self._repo.git.reset("HEAD", "--", path)
        except Exception as exc:
            raise GitMatrixError(f"Impossible de unstager {path} : {exc}")

    def stage_all(self) -> None:
        self._repo.git.add("-A")

    def unstage_all(self) -> None:
        try:
            self._repo.git.reset("HEAD")
        except Exception as exc:
            raise GitMatrixError(f"Impossible de tout unstager : {exc}")

    def commit_all(self, message: str) -> str:
        if not message.strip():
            raise GitMatrixError("Le message de commit ne peut pas être vide.")
        try:
            new_commit = self._repo.index.commit(message.strip())
        except Exception as exc:
            raise GitMatrixError(f"Échec du commit : {exc}")
        return new_commit.hexsha

    def create_branch(self, name: str, base: Optional[str] = None) -> None:
        try:
            self._repo.create_head(name, base or "HEAD")
        except Exception as exc:
            raise GitMatrixError(f"Impossible de créer la branche {name} : {exc}")

    def delete_branch(self, name: str) -> None:
        try:
            self._repo.delete_head(name, force=True)
        except Exception as exc:
            raise GitMatrixError(f"Impossible de supprimer la branche {name} : {exc}")

    def checkout(self, name: str) -> None:
        try:
            self._repo.git.checkout(name)
        except Exception as exc:
            raise GitMatrixError(f"Impossible de basculer sur {name} : {exc}")

    def init_or_open(path: str) -> "GitRepo":
        return GitRepo(path)


def _status(item) -> str:
    if getattr(item, "new_file", False):
        return "A"
    if getattr(item, "deleted_file", False):
        return "D"
    if getattr(item, "renamed_file", False):
        return "R"
    return "M"


def _parse_diff(text: str) -> List[dict]:
    """Transforme un diff unifié en liste de lignes annotées pour coloration."""
    lines: List[dict] = []
    old_line = 0
    new_line = 0
    for raw in text.splitlines():
        if raw.startswith("@@") and ("-" in raw[:6] or "+" in raw[:6]):
            lines.append({"text": raw, "type": "hunk"})
            # décodage du header @@ -a,b +c,d @@
            header = raw[raw.index("@", 1) + 1 : raw.rindex("@")]
            import re

            m = re.match(r"\s*-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?", header)
            if m:
                old_line = int(m.group(1) or 0)
                new_line = int(m.group(3) or 0)
            continue
        if raw.startswith("+++") or raw.startswith("---"):
            lines.append({"text": raw, "type": "meta"})
            continue
        if (
            raw.startswith("diff --git")
            or raw.startswith("index ")
            or raw.startswith("new file")
            or raw.startswith("deleted file")
            or raw.startswith("similarity index")
            or raw.startswith("rename from")
            or raw.startswith("rename to")
            or raw.startswith("old mode")
            or raw.startswith("new mode")
        ):
            lines.append({"text": raw, "type": "meta"})
            continue
        if raw.startswith("+"):
            lines.append({"text": raw, "type": "add", "new_line": new_line})
            new_line += 1
        elif raw.startswith("-"):
            lines.append({"text": raw, "type": "del", "old_line": old_line})
            old_line += 1
        else:
            lines.append({"text": raw, "type": "ctx", "old_line": old_line, "new_line": new_line})
            old_line += 1
            new_line += 1
    return lines
