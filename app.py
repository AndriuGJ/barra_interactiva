import os
import sys
import signal

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.icons import app_icon
from app.floating import FloatingToolbar


def main():

    # En Wayland el compositor decide dónde se
    # colocan las ventanas e ignora move().
    # Usamos XWayland para poder anclar la barra
    # al borde derecho de la pantalla.
    if (
        not os.environ.get("QT_QPA_PLATFORM")
        and os.environ.get("DISPLAY")
    ):

        os.environ["QT_QPA_PLATFORM"] = "xcb"

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