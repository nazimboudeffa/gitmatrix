"""Point d'entrée de GitMatrix."""

from __future__ import annotations

import argparse
import os
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="gitmatrix", description="Client Git visuel")
    parser.add_argument(
        "-r",
        "--repo",
        help="Chemin vers le dépôt Git à ouvrir au lancement",
    )
    args = parser.parse_args(argv)

    from PySide6.QtCore import QEventLoop

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("GitMatrix")
    app.setOrganizationName("GitMatrix")

    from gitmatrix.ui.splash_screen import MatrixRainSplash

    splash = MatrixRainSplash()
    splash.show()
    app.processEvents()

    splash.set_progress(0.1, "Chargement de l\u2019interface\u2026")
    app.processEvents()

    from gitmatrix.ui.main_window import MainWindow

    splash.set_progress(0.3, "Initialisation des widgets\u2026")
    app.processEvents()

    window = MainWindow()

    splash.set_progress(0.6, "Connexion signaux\u2026")
    app.processEvents()

    target = args.repo or (os.getcwd() if os.path.isdir(".git") else None)
    if target is not None:
        splash.set_progress(0.8, "Chargement du dépôt\u2026")
        app.processEvents()
        window.load_repo(target)
        splash.set_progress(0.95, f"Dépôt chargé \u2014 {window._repo.active_branch or ''}")
        app.processEvents()

    splash.set_progress(1.0, "Prêt")
    app.processEvents()

    loop = QEventLoop()
    splash.launched.connect(loop.quit)
    loop.exec()

    window.show()
    splash.close()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
