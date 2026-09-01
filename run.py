"""Lanceur simple : python run.py [--repo chemin]"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from gitmatrix.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())