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

    from PySide6.QtCore import QEventLoop, QSettings

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("GitMatrix")
    app.setOrganizationName("GitMatrix")

    from gitmatrix.theme import apply_theme_to
    apply_theme_to(app)

    from gitmatrix.ui.main_window import MainWindow
    from gitmatrix.ui.splash_screen import create_splash

    splash = None
    if QSettings().value("enable_splash", True, type=bool):
        splash = create_splash(QSettings().value("splash", "") or "")
        splash.show()

    def progress(frac: float, text: str = "") -> None:
        if splash is not None:
            splash.set_progress(frac, text)
        app.processEvents()

    progress(0.1, "Chargement de l\u2019interface\u2026")

    window = MainWindow()

    progress(0.3, "Initialisation des widgets\u2026")

    target = args.repo or (os.getcwd() if os.path.isdir(".git") else None)
    if target is not None:
        progress(0.8, "Chargement du dépôt\u2026")
        window.load_repo(target)
        progress(0.95, f"Dépôt chargé \u2014 {window._repo.active_branch or ''}")

    progress(1.0, "Prêt")

    if splash is not None:
        loop = QEventLoop()
        splash.launched.connect(loop.quit)
        loop.exec()
        splash.close()

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
