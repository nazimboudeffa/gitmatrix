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

    from PySide6.QtWidgets import QApplication

    from gitmatrix.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("GitMatrix")
    app.setOrganizationName("GitMatrix")

    window = MainWindow()
    window.show()

    target = args.repo or (os.getcwd() if os.path.isdir(".git") else None)
    if target is not None:
        window.load_repo(target)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())