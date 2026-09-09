# Changelog

Toutes les modifications notables de GitMatrix sont documentées ici.

## v0.1.1 — 2026-09-09

**Intégration du redesign v2**

- Toolbar réorganisée par groupes avec icônes + libellés et raccourcis clavier :
  `Ouvrir` / `Actualiser`, `Fetch` / `Pull` / `Push`, `Stage All` / `Unstage All`,
  `Commit` (doré), `À propos`
- Suppression de l'écran « Bienvenue » au lancement
- Status bar en chips : branche, état du working tree, fichiers indexés /
  non indexés avec pastilles colorées
- Branches : pastilles colorées, branche active en doré, indicateurs ↑/↓
  (ahead/behind) colorés, section **DISTANTES**
- Liste de fichiers : groupes `Staged` / `Changes` avec compteurs, fonds colorés
  par statut ; double-clic sur un commit → liste de ses fichiers avec diff
  fichier par fichier
- Thème centralisé (tokens + palette de couleurs) et icônes SVG dans
  `assets/icons`

**Fonctionnalités Git**

- `Pull`, `Fetch`, `Push` de la branche active
- État amont (ahead/behind) affiché
- Blocage des commits vides

**Corrections**

- Diff du working tree enfin fonctionnel (génération des patches + chemins
  corrects dans `git status --porcelain`) ; contenu des fichiers non suivis
  affiché
- Activation des boutons de la toolbar au lancement lorsque le dépôt se charge
  automatiquement
- Tooltip des commits affiché sous le curseur au lieu du centre de la fenêtre

## v0.1.0 — première version

**Client Git visuel (première version publique)**

- Graphe de commits personnalisé : un cercle par commit, lignes colorées,
  badges `HEAD` / branches / tags, rendu optimisé pour les gros dépôts
- Zone de staging : indexer / dé-indexer fichier par fichier ou tout en une
  fois, statuts `A` / `M` / `D` / `U` affichés
- Vue diff d'un fichier (additions en vert, suppressions en rouge)
- Branches : liste locale, branche active marquée ★, création et bascule
- Créer un commit depuis l'interface (avec compteur de caractères du message)
- Thème sombre ; dialogue « À propos » avec lien de soutien
- Documentation : `doc/GUIDE.md`, `doc/PLAN.md`, licence