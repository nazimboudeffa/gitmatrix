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
        help="Path to the Git repository to open at launch",
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

    progress(0.1, "Loading interface…")

    window = MainWindow()

    progress(0.3, "Initializing widgets…")

    target = args.repo or (os.getcwd() if os.path.isdir(".git") else None)
    if target is not None:
        progress(0.8, "Loading repository…")
        window.load_repo(target)
        progress(0.95, f"Repository loaded — {window._repo.active_branch or ''}")

    progress(1.0, "Ready")

    if splash is not None:
        loop = QEventLoop()
        splash.launched.connect(loop.quit)
        loop.exec()
        splash.close()

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
