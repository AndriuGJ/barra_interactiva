from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

import qtawesome as qta


# =========================================================
# RUTAS
# =========================================================

BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

APP_ICON_PATH = (
    BASE_DIR / "assets" / "icons" / "Icono.png"
)


# =========================================================
# APARIENCIA
# =========================================================

ICON_COLOR = "#ffffff"

ICON_SIZE = 18


# =========================================================
# NOMBRES DE ICONOS (Font Awesome 6)
# =========================================================

DRAG_ICON = "fa6s.grip"

CLOSE_ICON = "fa6s.xmark"

CUSTOM_COLOR_ICON = "fa6s.palette"

MINIMIZE_ICON = "fa6s.window-minimize"

EXPAND_ICON = "fa6s.window-maximize"

UNDO_ICON = "fa6s.arrow-rotate-left"

CLEAR_ICON = "fa6s.trash-can"

SCREENSHOT_ICON = "fa6s.camera"

TOOL_ICONS = {
    "hand": "fa6s.arrow-pointer",
    "pencil": "fa6s.pencil",
    "rectangle": "fa6.square",
    "ellipse": "fa6.circle",
    "arrow": "fa6s.arrow-right",
    "text": "fa6s.font",
    "eraser": "fa6s.eraser",
}


# =========================================================
# UTILIDADES
# =========================================================

def icon(
    name,
    color=ICON_COLOR,
    prefix="fa6s"
):

    # qtawesome espera "prefijo.nombre"
    if "." not in name:

        name = f"{prefix}.{name}"

    return qta.icon(
        name,
        color=color
    )


def icon_pixmap(
    name,
    color=ICON_COLOR,
    size=ICON_SIZE
):

    return icon(
        name,
        color
    ).pixmap(
        size,
        size
    )


def set_icon(
    widget,
    name,
    color=ICON_COLOR,
    size=ICON_SIZE
):

    widget.setIcon(
        icon(name, color)
    )

    widget.setIconSize(
        QSize(size, size)
    )


def app_icon():

    if APP_ICON_PATH.exists():

        return QIcon(
            str(APP_ICON_PATH)
        )

    return QIcon()
