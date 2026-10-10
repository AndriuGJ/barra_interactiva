import os
import sys
import signal

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.icons import app_icon
from app.floating import FloatingToolbar
from app.hotkey import HotkeyService


def configure_qt_platform():
    """
    Selecciona el backend gráfico adecuado en Linux.

    - Si XWayland/X11 está disponible (DISPLAY), usa XCB.
      Esto permite posicionar la barra y capturar la pantalla
      sin el diálogo de permisos del portal de Wayland.
    - Si no hay DISPLAY, usa Wayland nativo.

    Se respeta QT_QPA_PLATFORM si el usuario ya lo definió.
    """

    if os.environ.get("QT_QPA_PLATFORM"):
        return

    if not sys.platform.startswith("linux"):
        return

    if os.environ.get("DISPLAY"):
        os.environ["QT_QPA_PLATFORM"] = "xcb"
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

    # La barra inicial se omite: la aplicación arranca
    # directamente con la barra completa de dibujo.
    toolbar.overlay.activate()

    # Atajo global F (GNOME) + socket local: F alterna
    # entre "usar el equipo normal" y la barra. El
    # atajo se retira al salir.
    hotkey = HotkeyService()

    hotkey.toggle_requested.connect(
        toolbar.toggle_overlay
    )

    hotkey.start()

    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(200)

    try:

        sys.exit(app.exec())

    finally:

        hotkey.stop()


if __name__ == "__main__":
    main()
