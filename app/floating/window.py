from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QColorDialog,
    QApplication,
)

from app import icons
from app.floating.panel import FloatingPanel
from app.overlay import DrawingOverlay


class FloatingToolbar(QWidget):

    """Barra flotante inicial de la aplicación.

    Anclada al borde derecho de la pantalla y centrada
    verticalmente. Al elegir una herramienta oculta esta
    ventana y activa el overlay de dibujo.
    """

    def __init__(self):

        super().__init__()

        self.first_show = True

        self.overlay = DrawingOverlay()

        self.overlay.stop_requested.connect(
            self.stop_overlay
        )

        self.setWindowTitle(
            "Barra Interactiva"
        )

        self.setWindowIcon(
            icons.app_icon()
        )

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True
        )

        self.create_interface()

    def create_interface(self):

        self.panel = FloatingPanel()

        self.panel.tool_selected.connect(
            self.start_overlay
        )

        self.panel.color_selected.connect(
            self.start_overlay
        )

        self.panel.custom_color_requested.connect(
            self.open_custom_color
        )

        self.panel.close_requested.connect(
            self.close_application
        )

        self.panel.minimize_requested.connect(
            self.collapse_bar
        )

        self.panel.expand_requested.connect(
            self.expand_bar
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0, 0, 0, 0
        )

        layout.addWidget(
            self.panel
        )

        self.adjustSize()

    # =========================================================
    # POSICIÓN
    # =========================================================

    def showEvent(self, event):

        super().showEvent(event)

        if self.first_show:

            self.first_show = False

            self.move_to_edge()

    def screen_area(self):

        screen = self.screen()

        if screen is None:

            screen = QApplication.primaryScreen()

        if screen is None:

            return None

        return screen.availableGeometry()

    def move_to_edge(self):

        area = self.screen_area()

        if area is None:

            return

        self.adjustSize()

        self.move(
            area.right() - self.width() + 1,

            area.top()
            + max(
                0,
                (
                    area.height()
                    - self.height()
                ) // 2
            )
        )

    def move_keeping_center(
        self,
        position,
        size
    ):

        area = self.screen_area()

        if area is None:

            self.move(position)
            return

        self.adjustSize()

        x = position.x()

        y = (
            position.y()
            + size.height() // 2
            - self.height() // 2
        )

        x = max(
            area.left(),
            min(
                x,
                area.right()
                - self.width()
                + 1
            )
        )

        y = max(
            area.top(),
            min(
                y,
                area.bottom()
                - self.height()
                + 1
            )
        )

        self.move(x, y)

    def clamp_position(
        self,
        position
    ):

        area = self.screen_area()

        if area is None:

            return position

        x = max(
            area.left(),

            min(
                position.x(),
                area.right()
                - self.width()
                + 1
            )
        )

        y = max(
            area.top(),

            min(
                position.y(),
                area.bottom()
                - self.height()
                + 1
            )
        )

        return QPoint(x, y)

    # =========================================================
    # MINIMIZAR
    # =========================================================

    def collapse_bar(self):

        top_left = self.pos()

        self.panel.set_collapsed(True)

        self.adjustSize()

        self.move(
            self.clamp_position(top_left)
        )

    def expand_bar(self):

        center = (
            self.frameGeometry().center()
        )

        self.panel.set_collapsed(False)

        self.adjustSize()

        self.move(
            self.clamp_position(
                QPoint(
                    center.x()
                    - self.width() // 2,

                    center.y()
                    - self.height() // 2
                )
            )
        )

    # =========================================================
    # OVERLAY DE DIBUJO
    # =========================================================

    def start_overlay(
        self,
        tool=None,
        color=None
    ):

        position = self.mapToGlobal(
            self.rect().topLeft()
        )

        if tool:

            self.overlay.set_tool(
                tool
            )

        if color:

            self.overlay.set_pen_color(
                color
            )

        self.hide()

        self.overlay.activate(
            position
        )

    def stop_overlay(self):

        position = (
            self.overlay.toolbar_global_position()
        )

        size = (
            self.overlay.toolbar_size()
        )

        self.overlay.deactivate()

        self.show()
        self.raise_()

        self.move_keeping_center(
            position,
            size
        )

    # =========================================================
    # COLOR PERSONALIZADO
    # =========================================================

    def open_custom_color(self):

        dialog = QColorDialog(
            self.overlay.pen_color,
            self
        )

        dialog.setWindowTitle(
            "Seleccionar color"
        )

        dialog.setOption(
            QColorDialog.ColorDialogOption.DontUseNativeDialog,
            True
        )

        if dialog.exec():

            color = dialog.selectedColor()

            if color.isValid():

                self.overlay.set_pen_color(
                    color.name()
                )

                self.start_overlay()

    # =========================================================
    # CERRAR
    # =========================================================

    def close_application(self):

        self.overlay.close()
        self.close()

        # Las ventanas usan Qt.Tool y Qt no emite
        # lastWindowClosed para ese tipo, así que
        # salimos del bucle de eventos a mano.
        QApplication.quit()
