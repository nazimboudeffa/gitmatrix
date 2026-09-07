# Plan de développement de GitMatrix

Objectif : devenir une alternative libre, visuelle et intuitive à GitKraken —
chaque commande Git doit être accessible d'un clic, sans terminal.

Document d'organisation : chaque phase correspond à une version cible.
Cochez les cases au fur et à mesure.

---

## Phase 1 — Fondations solides (v0.2) · Priorité haute

Ci-dessous, les fondamentaux pour qu'un dépôt réel soit utilisable au quotidien.

### Remotes et synchronisation
- [x] `repo.remotes()` : liste des remotes (origin, etc.) dans la couche core
- [x] Afficher les branches distantes (`refs/remotes/`) dans le graphe
  - [x] badge violet « remote » distinct des branches locales
- [x] Actions toolbar : `Fetch`, `Pull`, `Push`
- [x] État amont (ahead/behind) affiché dans le panneau des branches

### Diff par commit
- [ ] Sélectionner un commit ⮕ afficher son diff complet (vs son parent)
- [ ] Double-clic : naviguer vers la liste des fichiers changés par ce commit
- [ ] Diff entre deux commits sélectionnés (Ctrl+clic)

### Interaction graphe
- [ ] Survol : tooltip avec message complet, auteur, date
- [ ] Recherche de commits (Ctrl+F) avec surlignage
- [ ] Zoom (Ctrl+mouse / touches + -)

---

## Phase 2 — Toutes les commandes Git visuelles (v0.3) · Priorité haute

Cœur de l'ambition « faire toutes les commandes git de manière visuelle ».

### Branches
- [ ] **Merge** (clic droit sur une branche → merge vers la branche active)
- [ ] **Rebase** (clic droit → rebase origin/…) avec options (--interactive plus tard)
- [ ] **Cherry-pick** (clic droit sur un commit → appliquer sur la branche active)
- [ ] **Reset** (soft/hard/mixed) en cliquant un commit
- [ ] **Rename de branche**, pousser/supprimer en remote
- [ ] Glisser-déposer une branche sur un commit pour rebaser (style GitKraken)

### Stash
- [ ] `git stash push` (avec message) et `git stash pop` depuis la toolbar
- [ ] Vue des stashes et de leur contenu

### Tags & releases
- [ ] Créer/supprimer un tag depuis la ref
- [ ] Voir le diff d'un tag vs branche

### Reflog
- [ ] Vues et restauration de commits « perdus » via reflog

### Amend & reword
- [ ] `--amend` sur le dernier commit
- [ ] Réécrire le message d'un commit (reword)

---

## Phase 3 — Confort et performance (v0.4) · Priorité moyenne

Mise au niveau GitKraken en termes d'UX.

- [ ] Onglet « Changements » détaché : aperçu live du working tree
- [ ] Barre d'activité latérale (style VSCode) regroupant : graphe, branches, remotes, stash, tags, paramètres
- [ ] Filtres du graphe : une branche, une période, un auteur
- [ ] Thème clair + bascule de thème
- [ ] Raccourcis clavier (Ctrl+Return commit, Ctrl+Shift+S stash, Ctrl+P push…)
- [ ] Historique paginé / chargement paresseux (walk_commits limité → « plus de commits »)
- [ ] Traitement asynchrone (QThread) des opérations longues (fetch/push) sans bloquer l'UI

---

## Phase 4 — Solidité et distribution (v0.5) · Priorité moyenne

- [ ] Tests unitaires :
  - [ ] `pytest` sur la couche core (stage/commit/branch/diff)
  - [ ] Tests du layout du graphe (structure lanes / arêtes sur des topologies de test)
  - [ ] Smoke test UI offscreen (déjà utilisé manuellement → automatisé)
- [ ] Lint/typing : `ruff` + `mypy`
- [ ] Package autonome : `PyInstaller` → `.exe` Windows
- [ ] Installateur (Inno Setup ou MSIX) avec icône
- [ ] Mise à jour automatique (comparaison de version GitHub)
- [ ] Logs + rapport de crash (fichier dans %APPDATA%/gitmatrix)
- [ ] CI (GitHub Actions) : tests sur Windows/Linux/macOS

---

## Idées long terme (backlog)

- Git LFS display
- Git submodules
- Signatures GPG / signature des commits
- Support plugins (scripts externes dans le menu contextuel)
- Export du graphe en image/PDF
- Mode « GitKraken look » : filtre de branche animé, courbes douces
- i18n : anglais/français (fichiers de traduction Qt `.ts`)
- Préférences persistantes (`QSettings`) : thème, colonnes, repo récent

---

## Architecture & conventions (rappel)

| Couche        | Rôle                                             | Emplacement                  |
| ------------- | ------------------------------------------------ | ---------------------------- |
| Core          | Toute la logique Git (GitPython), sans Qt        | `src/gitmatrix/core/`        |
| Modèles       | Structure du graphe (GraphLayout, GraphEdge…)    | `src/gitmatrix/models/`      |
| Widgets       | Composants UI réutilisables (graph, diff, …)     | `src/gitmatrix/widgets/`     |
| UI            | Fenêtres et dialogues                            | `src/gitmatrix/ui/`          |

**Règles**
1. Le core ne dépend jamais de Qt (testable sans affichage).
2. Toute erreur Git se propage via `GitMatrixError` → convertie en `QMessageBox` dans l'UI.
3. Layout `src/` : le module s'importe comme `gitmatrix.*` (déjà installé en mode éditable).
4. Graphe : l'algorithme des lanes est dans `models/graph.py` (logique pure, testable).

**Commandes utiles**
```bash
python run.py -r <repo>      # lancer l'app
.\.venv\Scripts\python -m pytest doc/../tests  # (une fois la phase 4 entamée)
```