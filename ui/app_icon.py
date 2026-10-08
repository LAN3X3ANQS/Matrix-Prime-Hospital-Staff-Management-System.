import sys
from pathlib import Path

from PySide6.QtGui import QIcon


def get_app_icon():
    if getattr(sys, "frozen", False):
        app_root = Path(
            getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent)
        )
    else:
        app_root = Path(__file__).resolve().parent.parent
    return QIcon(str(app_root / "assets" / "matrix-prime-hospital.ico"))
