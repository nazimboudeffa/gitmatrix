"""Aperçu d'un splash screen depuis la fenêtre des paramètres.

Permet de visualiser le rendu en plein écran (animation comprise) sans
avoir à redémarrer le logiciel.  Le splash est montré directement prêt —
la gauge affiche « Prêt » et le bouton LANCER est immédiatement visible —
et la fonction bloque (boucle d'événements locale) jusqu'au clic dessus.
"""

from __future__ import annotations

from PySide6.QtCore import QEventLoop

from gitmatrix.ui.splash_screen import create_splash


def preview_splash(name: str) -> None:
    """Affiche le splash ``name`` en plein écran, prêt à être lancé.

    Le splash est montré à 100 % (statut « Prêt », bouton LANCER visible)
    pour que l'on voie tout de suite l'apparence finale ; l'appel ne rend
    la main qu'après le clic sur LANCER, dont l'aperçu se ferme.
    """
    splash = create_splash(name)
    splash.set_progress(1.0, "Prêt")
    splash.show()
    loop = QEventLoop()
    splash.launched.connect(loop.quit)
    loop.exec()