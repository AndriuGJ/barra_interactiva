import os
import sys
import signal

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.icons import app_icon
from app.floating import FloatingToolbar


def configure_qt_platform():
    """
    Selecciona el backend gráfico adecuado en Linux.

    - Wayland: usa Qt Wayland nativo.
    - X11: usa XCB.
    - Otros casos: deja que Qt decida automáticamente.

    Se respeta QT_QPA_PLATFORM si el usuario ya lo definió.
    """

    if os.environ.get("QT_QPA_PLATFORM"):
        return

    if not sys.platform.startswith("linux"):
        return

    session_type = (
        os.environ
        .get("XDG_SESSION_TYPE", "")
        .strip()
        .lower()
    )

    if session_type == "wayland":
        os.environ["QT_QPA_PLATFORM"] = "wayland"
        return

    if session_type == "x11":
        os.environ["QT_QPA_PLATFORM"] = "xcb"
        return


def main():
    configure_qt_platform()

    signal.signal(
        signal.SIGINT,
        lambda *_: QApplication.quit()
    )

    app = QApplication(sys.argv)

    app.setApplicationName(
        "Barra Interactiva"
    )

    app.setWindowIcon(
        app_icon()
    )

    app.setQuitOnLastWindowClosed(True)

    toolbar = FloatingToolbar()
    toolbar.show()

    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(200)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
