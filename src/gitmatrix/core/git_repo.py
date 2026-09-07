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
    def ref_map_by_commit(self) -> dict:
        """Dictionnaire {hexsha_commit: [RefInfo, ...]} calculé en UNE commande git.

        Évite l'appel subprocess par commit (performances sur les gros dépôts :
        Phaser, kernels, etc. sont impossibles à charger autrement).
        """
        mapping: dict = {}
        try:
            lines = self._repo.git.for_each_ref(
                "--format=%(refname)%00%(objectname)%00%(*objectname)"
            ).splitlines()
        except Exception:
            lines = []
        for line in lines:
            parts = line.split("\x00")
            if len(parts) < 3:
                continue
            refname, obj, obj_peeled = parts[0], parts[1], parts[2]
            kind, name = self._classify_ref(refname)
            target = obj_peeled or obj
            mapping.setdefault(target, []).append(
                RefInfo(name=name, kind=kind, target=target)
            )
        # HEAD (position courante)
        try:
            head_sha = self._repo.head.commit.hexsha
            mapping.setdefault(head_sha, []).append(
                RefInfo(
                    name=self.active_branch or "HEAD",
                    kind="head",
                    target=head_sha,
                )
            )
        except Exception:
            pass
        return mapping

    @staticmethod
    def _classify_ref(refname: str):
        """(kind, nom) à partir d'une référence complète 'refs/heads/xxx'."""
        if refname.startswith("refs/heads/"):
            return "branch", refname[len("refs/heads/") :]
        if refname.startswith("refs/remotes/"):
            return "remote", refname[len("refs/remotes/") :]
        if refname.startswith("refs/tags/"):
            return "tag", refname[len("refs/tags/") :]
        return "", refname

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
    def all_branches(self) -> List[RefInfo]:
        """Branches locales, déduites de la map de refs (1 seule commande git)."""
        result: List[RefInfo] = []
        seen = set()
        for refs in self.ref_map_by_commit().values():
            for r in refs:
                if r.kind == "branch" and r.name not in seen:
                    seen.add(r.name)
                    result.append(r)
        return result
    def changes(self) -> List[FileChange]:
        """Liste des changements (staged + unstaged + untracked).

        Calculée par UN seul ``git status --porcelain -z`` (rapide même sur
        un dépôt comptant des milliers de fichiers).
        """
        result: List[FileChange] = []
        try:
            raw = self._repo.git.status(
                "--porcelain", "-z", "--untracked-files=all"
            )
        except Exception as exc:
            raise GitMatrixError(f"Impossible de lire l'état du dépôt : {exc}")

        records = raw.split("\0")
        i = 0
        while i < len(records):
            rec = records[i]
            i += 1
            if not rec:
                continue
            st, path = rec[:2], rec[2:]
            if "R" in st and i < len(records) and records[i]:
                path = records[i]
                i += 1
            x, y = st[0], st[1]
            if st == "??":
                result.append(FileChange(path=path, staged=False, status="U"))
                continue
            if x != " " and x != "?":
                result.append(FileChange(path=path, staged=True, status=self._code(x)))
            if y != " " and y != "?":
                result.append(FileChange(path=path, staged=False, status=self._code(y)))
        return result

    @staticmethod
    def _code(ch: str) -> str:
        return {"A": "A", "M": "M", "D": "D", "R": "R", "C": "C"}.get(ch, "M")

    def is_dirty(self) -> bool:
        try:
            out = self._repo.git.status("--porcelain", "--untracked-files=all")
            return bool(out.strip())
        except Exception:
            return False

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
