import sys
from pathlib import Path

from PySide6.QtGui import QIcon


def get_app_icon():
    if getattr(sys, "frozen", False):
        return QIcon(str(Path(sys.executable)))
    return QIcon(
        str(Path(__file__).resolve().parent.parent / "assets" / "matrix-prime-hospital.ico")
    )
