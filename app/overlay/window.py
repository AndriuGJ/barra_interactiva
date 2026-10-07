from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QApplication

from app import icons
from app.config import DEFAULT_PEN_COLOR
from app.overlay.objects import ObjectsMixin
from app.overlay.canvas import CanvasMixin
from app.overlay.panel import PanelMixin


class DrawingOverlay(ObjectsMixin, CanvasMixin, PanelMixin, QWidget):

    """Pantalla completa donde se dibuja.

    Gestiona el ciclo activar/desactivar, los eventos
    de ratón y teclado, y la comunicación con la
    barra interna (PanelMixin) y el lienzo (CanvasMixin).
    """

    stop_requested = Signal()

    def __init__(self):
        super().__init__()

        # =====================================================
        # CONFIGURACIÓN
        # =====================================================

        self.current_tool = "pencil"

        self.pen_color = QColor(
            DEFAULT_PEN_COLOR
        )

        self.pen_width = 4

        self.drawing = False

        self.start_point = QPoint()
        self.current_point = QPoint()

        self.current_path = []

        self.objects = []

        # =====================================================
        # TEXTO
        # =====================================================

        self.text_editor = None

        self.text_position = QPoint()

        self.selected_object = None

        self.moving_object = False

        self.move_offset = QPoint()

        # =====================================================
        # VENTANA
        # =====================================================

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

        self.setAttribute(
            Qt.WidgetAttribute.WA_NoSystemBackground,
            True
        )

        self.setMouseTracking(
            True
        )

        self.create_toolbar()

        self.hide()

    # =========================================================
    # TOOLBAR
    # =========================================================


    def set_tool(
        self,
        tool
    ):

        self.cancel_text_editor()

        self.current_tool = tool

        self.set_active_tool(tool)

        if tool != "hand":

            self.selected_object = None

        self.update()

    # =========================================================
    # ACTIVAR / DESACTIVAR
    # =========================================================


    def activate(
        self,
        toolbar_position=None
    ):

        screen = QApplication.primaryScreen()

        if screen is None:
            return

        # Mutter/GNOME redimensiona las ventanas que
        # tapen barras al área de trabajo, lo que
        # desplazaría nuestra barra. Usamos ese
        # área desde el principio para evitarlo.
        self.setGeometry(
            screen.availableGeometry()
        )

        self.show()
        self.raise_()

        self.toolbar.adjustSize()

        overlay_global = (
            self.mapToGlobal(
                QPoint(0, 0)
            )
        )

        area = screen.availableGeometry()

        if toolbar_position:

            x = toolbar_position.x()

        else:

            x = (
                area.right()
                - self.toolbar.width()
                + 1
            )

        y = (
            area.top()
            + max(
                0,
                (
                    area.height()
                    - self.toolbar.height()
                ) // 2
            )
        )

        x = max(
            area.left(),
            min(
                x,
                area.right()
                - self.toolbar.width()
                + 1
            )
        )

        y = max(
            area.top(),
            min(
                y,
                area.bottom()
                - self.toolbar.height()
                + 1
            )
        )

        self.toolbar.move(
            x - overlay_global.x(),
            y - overlay_global.y()
        )

        self.toolbar.show()
        self.toolbar.raise_()


    def deactivate(self):

        self.cancel_text_editor()

        self.selected_object = None

        self.moving_object = False

        self.hide()


    def mousePressEvent(
        self,
        event
    ):

        point = (
            event.position().toPoint()
        )

        if self.point_inside_toolbar(
            point
        ):
            return

        if (
            event.button()
            != Qt.MouseButton.LeftButton
        ):
            return

        # MANO
        if self.current_tool == "hand":

            obj = self.find_object_at(
                point
            )

            self.selected_object = obj

            if obj is not None:

                self.moving_object = True

                self.move_offset = (
                    point
                    - self.object_bbox(
                        obj
                    ).topLeft()
                )

            self.update()

            return

        # TEXTO
        if self.current_tool == "text":

            self.open_text_editor(
                point
            )

            return

        self.drawing = True

        self.start_point = QPoint(
            point
        )

        self.current_point = QPoint(
            point
        )

        if self.current_tool == "pencil":

            self.current_path = [
                QPoint(point)
            ]

        elif self.current_tool == "eraser":

            self.erase_at(
                point
            )

    # =========================================================
    # MOUSE MOVE
    # =========================================================


    def mouseMoveEvent(
        self,
        event
    ):

        point = (
            event.position().toPoint()
        )

        # MOVER OBJETO SELECCIONADO
        if (
            self.current_tool == "hand"
            and self.moving_object
            and self.selected_object
        ):

            bbox = self.object_bbox(
                self.selected_object
            )

            target = (
                point
                - self.move_offset
            )

            delta = target - bbox.topLeft()

            if delta.x() or delta.y():

                self.translate_object(
                    self.selected_object,
                    delta.x(),
                    delta.y()
                )

                self.update()

            return

        if not self.drawing:
            return

        self.current_point = QPoint(
            point
        )

        if self.current_tool == "pencil":

            self.current_path.append(
                QPoint(point)
            )

        elif self.current_tool == "eraser":

            self.erase_at(
                point
            )

        self.update()

    # =========================================================
    # MOUSE RELEASE
    # =========================================================


    def mouseReleaseEvent(
        self,
        event
    ):

        if (
            event.button()
            != Qt.MouseButton.LeftButton
        ):
            return

        if self.moving_object:

            self.moving_object = False
            return

        if not self.drawing:
            return

        self.drawing = False

        end = (
            event.position().toPoint()
        )

        if (
            self.current_tool == "pencil"
            and len(self.current_path) > 1
        ):

            self.objects.append({
                "type": "pencil",

                "points": [
                    QPoint(p)
                    for p in self.current_path
                ],

                "color": QColor(
                    self.pen_color
                ),

                "width": self.pen_width,
            })

        elif self.current_tool in [
            "rectangle",
            "ellipse",
            "arrow"
        ]:

            self.objects.append({
                "type": self.current_tool,

                "start": QPoint(
                    self.start_point
                ),

                "end": QPoint(
                    end
                ),

                "color": QColor(
                    self.pen_color
                ),

                "width": self.pen_width,
            })

        self.current_path = []

        self.update()

    # =========================================================
    # TEXTO
    # =========================================================


    def set_pen_color(
        self,
        color
    ):

        self.pen_color = QColor(
            color
        )

        # Si hay un objeto seleccionado con la mano,
        # también cambia el color de ese objeto.
        if self.selected_object:

            self.selected_object[
                "color"
            ] = QColor(
                color
            )

        self.update_color_selection()

        self.update()

    # =========================================================
    # COLOR PERSONALIZADO
    # =========================================================


    def set_pen_width(
        self,
        width
    ):

        self.pen_width = width

    # =========================================================
    # DESHACER
    # =========================================================


    def undo(self):

        self.cancel_text_editor()

        self.selected_object = None

        if self.objects:

            self.objects.pop()

        self.update()

    # =========================================================
    # LIMPIAR
    # =========================================================


    def clear(self):

        self.cancel_text_editor()

        self.objects.clear()

        self.selected_object = None

        self.current_path = []

        self.update()

    # =========================================================
    # TECLADO
    # =========================================================


    def keyPressEvent(
        self,
        event
    ):

        if (
            event.key()
            == Qt.Key.Key_Escape
        ):

            self.cancel_text_editor()

            self.selected_object = None

            self.moving_object = False

            self.update()

            return

        if (
            event.key()
            in (
                Qt.Key.Key_Delete,
                Qt.Key.Key_Backspace,
            )
            and self.selected_object
            and self.text_editor is None
        ):

            self.delete_selected()

            return

        if (
            event.modifiers()
            & Qt.KeyboardModifier.ControlModifier
            and
            event.key()
            == Qt.Key.Key_Z
        ):

            self.undo()

            return

        super().keyPressEvent(
            event
        )
