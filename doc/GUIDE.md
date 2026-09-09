# Guide Git & GitMatrix

Ce guide s'adresse aux débutants comme aux curieux :
d'abord **comprendre Git** (les concepts), puis **utiliser GitMatrix** (l'outil visuel).

---

## Partie 1 — Git en général

### 1.1 C'est quoi Git ?

Git est un **système de gestion de versions** : il enregistre **chaque version**
de vos fichiers dans un historique, afin de :

- revenir en arrière à tout moment ;
- travailler à plusieurs sur les mêmes fichiers sans se marcher dessus ;
- expérimenter sans casser ce qui marche.

Contrairement au « copier-coller d'un dossier + version finale v2 »,
Git conserve **tout** : qui a modifié quoi, quand, et pourquoi (message de commit).

> Les concepts à retenir : **dépôt**, **commit**, **branche**, **zone de staging**,
> **remote**.

### 1.2 Le dépôt (repository / repo)

Un dépôt est un dossier spécial contenant tout l'historique (dossier caché `.git`).
Deux possibilités :

| Type | Exemple | Usage |
| ---- | ------- | ----- |
| Local | `C:\Projets\game`, dossier `.git` | Votre machine |
| Distant (remote) | `https://github.com/...` | Partage, sauvegarde |

GitMatrix ouvre un dépôt **local** ; les remotes (GitHub, GitLab…) servent à
synchroniser plusieurs dépôts locaux entre eux.

### 1.3 Le commit — une photo de l'état des fichiers

Un **commit** est un enregistrement : « à cet instant, les fichiers étaient exactement
comme ça ». Chaque commit possède :

- un **hash** unique (identifiant) : `3f8d2a1`… ;
- un **message** expliquant le changement ;
- un **auteur**, une **date** ;
- **zéro, un ou plusieurs parents** (le(s) commit(s) qui le précèdent).

Les commits forment donc une **chaîne** (le premier n'a pas de parent, un **merge**
en a deux).

### 1.4 La zone de staging (l'index)

`commit` ne sauvegarde pas directement vos fichiers :

```
Fichiers modifiés  --stage/add-->  Zone de staging  --commit-->  Historique
```

On *stage* les changements à inclure dans le prochain commit, puis on *commit*.
Cela permet de faire plusieurs commits précis avec un seul travail en cours.

### 1.5 Les branches — des lignes de travail parallèles

Une **branche** est un nom pointant vers un commit (et donc vers tout son historique).
Créer une branche = partir d'un commit existant pour travailler dessus sans
perturber l'original.

```
   main :   C1 --- C2 --- C3
                          \
  feature :                 C4 --- C5
```

Quand le travail est fini, on **fusionne** (`merge`) ou **rebate** (`rebase`).

### 1.6 Vocabulaire rapide

| Terme        | Signification courte |
| ------------ | -------------------- |
| `working tree` | Vos fichiers sur disque |
| `add` / `stage` | Déplacer un changement vers l'index |
| `commit`       | Enregistrer l'index dans l'historique |
| `branch`       | Ligne de travail nommée |
| `merge`        | Fusionner deux lignes |
| `rebase`       | Rejouer des commits sur une autre base |
| `push`         | Envoyer des commits vers le remote |
| `pull` / `fetch` | Récupérer des commits du remote |
| `clone`        | Copier un dépôt distant en local |
| `stash`        | Mettre de côté des changements provisoirement |
| `tag`          | Marquer un commit (ex. version `v1.0`) |
| `HEAD`         | « Où je suis » — la position courante |
| `origin`       | Nom de convention du remote principal |

---

## Partie 2 — GitMatrix en pratique

### 2.1 Installation et lancement

```bash
# 1. créer et activer l'environnement (une fois)
python -m venv .venv
.\.venv\Scripts\activate

# 2. installer (une fois)
pip install -e .

# 3. lancer
python -m gitmatrix -r chemin\vers\mon\repo
```

> Sans `-r`, GitMatrix s'ouvre vide : utilisez le bouton **Ouvrir…** de la barre
> d'outils pour choisir un dossier contenant un `.git`.

### 2.2 La fenêtre

```
┌──────────┬─────────────────────────────┬──────────────────────┐
│ Branches │   GRAPHE DES COMMITS        │  Modifications       │
│          │  (cercles + lignes colorées)│  (liste des fichiers)│
│          │                             ├──────────────────────┤
│          │                             │  Diff (aperçu code)  │
└──────────┴─────────────────────────────┴──────────────────────┘
```

- **Graphe** : chaque cercle = un commit ; les lignes colorées relient un commit à
  son parent. Plusieurs couleurs = plusieurs lignes de travail parallèles.
- **Badges** à droite des commits : 🟨 **HEAD** (position courante),
  🟩 branche locale (`main`), 🟫 tag (`v1.0`).
- **Branches** (gauche) : la branche active porte une étoile **★**.
- **Modifications** (haut droite) : deux groupes, *Staged* (prêtes à committer)
  et *Changes* (non indexées, `U` = fichier non suivi).
- **Diff** (bas droite) : le contenu du fichier sélectionné, additions en vert,
  suppressions en rouge.

### 2.3 Barre d'outils

| Bouton        | Raccourci    | Effet |
| ------------- | ------------ | ----- |
| Ouvrir        | Ctrl+O       | Ouvre un dépôt |
| Actualiser    | Ctrl+R       | Recharge graphe + changements |
| Fetch         | —            | Récupère les branches de tous les remotes |
| Pull          | —            | Récupère et fusionne les changements du remote |
| Push          | Ctrl+P       | Pousse la branche active (crée l'upstream si besoin) |
| Stage All     | Ctrl+S       | Indexe tous les changements |
| Unstage All   | —            | Dé-indexe tout |
| Commit        | Ctrl+Retour  | Ouvre la fenêtre de commit |
| À propos      | —            | Info + lien de soutien |

> La barre d'outils regroupe les actions par catégorie (fichier, synchronisation,
> staging) avec icônes ; **Commit** est le bouton principal à droite.

### 2.4 Le workflow typique

1. Ouvrez le dépôt.
2. Dans **Modifications**, vérifiez ce qui a changé.
3. Cliquez un fichier → son **Diff** s'affiche en bas.
4. Cliquez-droit sur un fichier → **Stage** (ou passez la souris sur **Stage All**).
5. Cliquez **Commit…**, écrivez un message, validez.
6. Le nouveau commit apparaît dans le **graphe**.
7. Dans le graphe, **cliquez** un commit pour voir le diff qu'il a introduit,
   **double-cliquez** pour lister les fichiers modifiés par ce commit dans le
   panneau *Modifications* (un clic sur un de ces fichiers affiche son diff).
8. La **barre d'état** montre en permanence la branche active, le dépôt est-il
   modifié, et les nombres *staged* / *unstaged*.

### 2.5 Gérer les branches

Dans le panneau de gauche :

- **double-clic** → basculer (checkout) ;
- **clic droit** → créer une branche, la supprimer, ou basculer dessus.

La branche active est en **doré** ; chaque branche porte une pastille de couleur
et son éventuel état amont **↑** (à pousser) / **↓** (à tirer). Les branches
distantes (`origin/…`) sont regroupées sous *DISTANTES* en violet.

### 2.6 Les erreurs

Une erreur Git (dépôt invalide, branch à supprimer non fusionnée…) s'affiche dans
une fenêtre « Erreur » avec un message clair. En cas de doute sur une commande,
le guide de référence Git reste :

```bash
git --help
```

### 2.7 Limites actuelles — et la suite

Cette première version couvre : graphe, staging, diff, branches, commit,
**fetch/pull/push**, ahead/behind dans le panneau des branches.
Les **fusions/rebase**, le **stash** et les **tags** sont à l'étape Phase 1/2 des
plans → voir [`doc/PLAN.md`](PLAN.md).

### 2.8 Repos de test

Un dépôt de test est disponible en ligne pour essayer GitMatrix (multi-contributeurs,
branches, tags, gros historique) :

- Repo : <https://github.com/nazimboudeffa/gitmatrix-tests>

```bash
git clone https://github.com/nazimboudeffa/gitmatrix-tests.git
python -m gitmatrix -r gitmatrix-tests
```

---

## Annexes

- Architecture et conventions : [`doc/PLAN.md`](PLAN.md)
- Prog/tech : PySide6 (interface) + GitPython (moteur Git), thème sombre.