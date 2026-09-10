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
- [x] Sélectionner un commit ⮕ afficher son diff complet (vs son parent)
- [x] Double-clic : naviguer vers la liste des fichiers changés par ce commit
- [ ] Diff entre deux commits sélectionnés (Ctrl+clic)

### Interaction graphe
- [x] Survol : tooltip avec message complet, auteur, date
- [ ] Recherche de commits (Ctrl+F) avec surlignage
- [ ] Zoom (Ctrl+mouse / touches + -)

---

## Phase 2 — Toutes les commandes Git visuelles (v0.4) · Priorité haute

Cœur de l'ambition « faire toutes les commandes git de manière visuelle ».

**Ordre recommandé : Stash → Amend → Merge/Rebase → Tags → Reset/Cherry-pick → Reflog**

### Stash — premier à livrer (usage quotidien)
- [ ] `git stash push` (avec message) et `git stash pop` depuis la toolbar
- [ ] Vue des stashes et de leur contenu

### Amend & reword
- [ ] `--amend` sur le dernier commit (réutilise le dialog de commit pré-rempli)
- [ ] Réécrire le message d'un commit (reword)

### Branches — merge/rebase
- [ ] **Merge** (clic droit sur une branche → merge vers la branche active)
- [ ] **Rebase** (clic droit → rebase origin/…) avec options (--interactive plus tard)
- [ ] **Reset** (soft/hard/mixed) en cliquant un commit
- [ ] **Cherry-pick** (clic droit sur un commit → appliquer sur la branche active)
- [ ] **Rename de branche**, pousser/supprimer en remote
- [ ] Glisser-déposer une branche sur un commit pour rebaser (style GitKraken)

### Tags & releases
- [ ] Créer/supprimer un tag depuis la ref (le graphe affiche déjà les badges tags)
- [ ] Voir le diff d'un tag vs branche

### Reflog
- [ ] Vues et restauration de commits « perdus » via reflog

---

## Phase 3 — Confort et performance (v0.5) · Priorité moyenne

Mise au niveau GitKraken en termes d'UX.

- [ ] Onglet « Changements » détaché : aperçu live du working tree
- [ ] Barre d'activité latérale (style VSCode) regroupant : graphe, branches, remotes, stash, tags, paramètres
- [ ] Filtres du graphe : une branche, une période, un auteur
- [x] Thèmes multiples + bascule (Nightfall / Matrix Void / Daylight — extensible JSON)
- [ ] Raccourcis clavier (Ctrl+Return commit, Ctrl+Shift+S stash, Ctrl+P push…)
- [ ] Historique paginé / chargement paresseux (walk_commits limité → « plus de commits »)
- [ ] Traitement asynchrone (QThread) des opérations longues (fetch/push) sans bloquer l'UI

---

## Phase 4 — Solidité et distribution (v0.6) · Priorité moyenne

- [ ] Tests unitaires :
  - [ ] `pytest` sur la couche core (stage/commit/branch/diff)
  - [ ] Tests du layout du graphe (`models/graph.py` — logique pure, idéal pour commencer)
  - [ ] Smoke test UI offscreen (déjà utilisé manuellement → automatisé)
- [ ] Lint/typing : `ruff` + `mypy`
- [ ] Package autonome : `PyInstaller` → `.exe` Windows
- [ ] Installateur (Inno Setup ou MSIX) avec icône
- [ ] Mise à jour automatique (comparaison de version GitHub)
- [ ] Logs + rapport de crash (fichier dans %APPDATA%/gitmatrix)
- [ ] CI (GitHub Actions) : tests sur Windows/Linux/macOS

---

## Phase Design — Identité visuelle « Matrix » · Priorité haute

Le nom *GitMatrix* doit porter une identité visuelle forte. Cette phase
s'intercale entre les phases fonctionnelles — chaque version doit embarquer
« un peu plus de Matrix ».

### Splash screen (fait, v0.3.1)
- [x] Animation Matrix rain (katakana + chiffres) au lancement
- [x] Gauge de progression liée au chargement réel (pas de timer cosmétique)
- [x] Bouton « Lancer » (apparaît à 100 %, l'animation continue)
- [x] Clic n'importe où = skip
- [x] Message intégré au splash qui se « décrypte » cellule par cellule (glyphes aléatoires → texte clair, en haut à gauche)

### Système de thèmes et de splash screens (fait, v0.3.1)
- [x] **Thèmes** chargés en JSON depuis `assets/themes` + `~/.gitmatrix/themes` (tokens + palette, template QSS généré, override complet possible)
- [x] **Splash screens** configurés en JSON depuis `assets/splashscreens` + `~/.gitmatrix/splashscreens` (couleurs, caractères, densité, vitesse, message)
- [x] 3 thèmes prédéfinis : Nightfall (défaut), Matrix Void, Daylight
- [x] 3 splash prédéfinis : Matrix Rain (défaut), Gold Rain, Minimal
- [x] Paramètres : sélecteurs thème + splash, persistés via `QSettings`, thème appliqué à chaud
- [x] Aperçu du splash en plein écran depuis les paramètres, sans redémarrer (fenêtre de paramètres non-modale)
- [x] Option « Activer le splash au démarrage » (désactivable, persistée via `QSettings`)
- [ ] Nouveaux thèmes/splash : documenter le format JSON (exemples + guide)

### Effets visuels — à faire
- [ ] **Rayon** matrix en filigrane sur les panneaux ou l'état vide du graphe
- [ ] **Scan line** ou lueur verte sur la ligne du commit sélectionné
- [ ] Transitions fluides entre panels (fade) au changement de dépôt
- [ ] Curseur / pointillés verts inspirés du film (accent secondaire discret)
- [ ] Icône de l'application (branche verte + pluie matrix)
- [ ] Combiner le filtre du graphe avec un effet « ralentissement de la pluie »

---

## Idées long terme (backlog)

- Git LFS display
- Git submodules
- Signatures GPG / signature des commits
- Support plugins (scripts externes dans le menu contextuel)
- Export du graphe en image/PDF
- Mode « GitKraken look » : filtre de branche animé, courbes douces
- i18n : ~~anglais/français~~ (abandonné) — interface unilingue en **anglais**, traduite complètement ; le français reste réservé aux documents et aux commentaires du code
- Préférences persistantes (`QSettings`) enrichies : colonnes, repo récent
  (thème + splash déjà persistés)

---

## Architecture & conventions (rappel)

| Couche        | Rôle                                             | Emplacement                  |
| ------------- | ------------------------------------------------ | ---------------------------- |
| Core          | Toute la logique Git (GitPython), sans Qt        | `src/gitmatrix/core/`        |
| Modèles       | Structure du graphe (GraphLayout, GraphEdge…)    | `src/gitmatrix/models/`      |
| Widgets       | Composants UI réutilisables (graph, diff, …)     | `src/gitmatrix/widgets/`     |
| UI            | Fenêtres, dialogues et splash screen             | `src/gitmatrix/ui/`          |

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