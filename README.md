# GitMatrix

Un client Git **visuel** pour Python (PySide6 + GitPython), pensé comme une alternative open-source à GitKraken.

## Fonctionnalités

- **Commit graph visuel** : l'historique Git rendu comme des lignes colorées avec branches, merges et refs (HEAD, branches, tags).
- Sélection et navigation dans les commits.
- Staging / unstaging des fichiers.
- Vue diff colorée.
- Gestion des branches.
- Thème sombre.

## Installation

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1 
pip install -r requirements.txt
```

## Lancer

```bash
gitmatrix 
```

## Structure

```
src/gitmatrix/
  app.py            # point d'entrée
  core/git_repo.py  # couche Git (GitPython)
  models/           # modèles de données (Commit, Ref, ...)
  widgets/          # widgets réutilisables (graph, diff, ...)
  ui/               # fenêtres / panneaux
```
