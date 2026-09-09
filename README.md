# GitMatrix

Un client Git **visuel**, pensé comme une alternative libre et open-source des clients Git existants.

## Fonctionnalités

- **Graphe de commits** : historique rendu en lignes colorées, avec branches,
  merges et refs (HEAD, branches, tags, distantes). Tooltip au survol,
  double-clic sur un commit → liste de ses fichiers avec diff fichier par
  fichier.
- **Zone de staging** : groupes *Staged* / *Changes* avec compteurs, statuts
  `A` / `M` / `D` / `U`, pastilles colorées, indexation / dé-indexation
  fichier par fichier ou en bloc.
- **Diff coloré** : working tree (y compris fichiers non suivis), fichier dans
  un commit.
- **Branches** : panneau (création, suppression, bascule, section
  *DISTANTES*, indicateurs ↑/↓ d'avance/retard) + sélecteur de branche dans la
  toolbar.
- **Remotes** : cloner un dépôt distant, fetch, pull et push (création de
  l'upstream si besoin), état amont (ahead / behind).
- **Commit** : message avec compteur de caractères, sujet/body, blocage des
  commits vides.
- **Toolbar** organisée par zones — *contexte* à gauche (cloner, ouvrir,
  actualiser, choisir la branche), *workflow* au centre (fetch, pull, staging,
  commit, push) — icônes + libellés, raccourcis clavier (Ctrl+O/R/S/P, Ctrl+Return).
- **Barre d'état** en chips : branche, état du working tree, indexé / non indexé.
- **Thème sombre** centralisé (tokens + palette de couleurs) et icônes SVG.

## Installation

Prérequis : [Python](https://www.python.org/) ≥ 3.9.

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## Lancer

Depuis un dossier de projet :

```bash
gitmatrix -r chemin\vers\mon\repo
```

Ou simplement `gitmatrix` : le dépôt courant est chargé automatiquement si le
dossier contient un `.git`, et la barre d'outils permet de **Cloner** ou
**Ouvrir** un dépôt.

## Documentation

- `doc/GUIDE.md` — guide Git & GitMatrix (installation, workflow, astuces).
- `doc/PLAN.md` — feuille de route.
- `CHANGELOG.md` — historique des versions.

## Structure

```
src/gitmatrix/
  app.py               # point d'entrée (argparse, chargement du dépôt)
  core/git_repo.py     # couche Git (GitPython)
  models/graph.py      # mise en page du graphe (colonnes, arêtes)
  widgets/             # widgets réutilisables (graph, diff, file list, branches)
  ui/                  # fenêtre principale + dialogues (clone, commit, à propos)
  assets/icons/        # icônes SVG
  theme.py             # thème sombre : tokens, palette, feuille de style QSS
```

## Licence

GNU GPL v3