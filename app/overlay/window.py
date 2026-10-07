import shutil
import uuid
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QPoint,
    Signal,
    Slot,
    QStandardPaths,
    QThread,
    QEventLoop,
    QTimer,
    QUrl,
    QObject,
)
from PySide6.QtDBus import (
    QDBusConnection,
    QDBusInterface,
)
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QWidget, QApplication, QToolTip

from app import icons
from app.config import DEFAULT_PEN_COLOR
from app.overlay.objects import ObjectsMixin
from app.overlay.canvas import CanvasMixin
from app.overlay.panel import PanelMixin


class PortalScreenshotBridge(QObject):

    response = Signal(int, object)


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
    # CAPTURA DE PANTALLA
    # =========================================================


    def screenshots_directory(self):

        pictures = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        )

        if pictures:

            base = Path(pictures)

        else:

            base = Path.home() / "Pictures"

        candidates = [
            base / "Screenshots",
            base / "Capturas de pantalla",
        ]

        for directory in candidates:

            if directory.exists():

                return directory

        # En Ubuntu en español suele mostrarse como
        # "Capturas de pantalla". Si todavía no existe,
        # usamos ese nombre dentro de Imágenes.
        directory = (
            base / "Capturas de pantalla"
        )

        directory.mkdir(
            parents=True,
            exist_ok=True
        )

        return directory


    def capture_annotated_screenshot(self):

        # El paquete .deb ejecuta Qt mediante X11/XWayland.
        # Así QScreen puede capturar el escritorio compuesto
        # sin instalar otra aplicación y sin abrir el portal
        # de permisos de Wayland.

        if self.text_editor:

            self.confirm_text()

        directory = self.screenshots_directory()

        filename = (
            "Barra_Interactiva_"
            + datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )
            + ".png"
        )

        target = directory / filename

        previous_selection = self.selected_object

        # No queremos guardar ni la barra ni el recuadro
        # punteado de selección.
        self.selected_object = None

        self.toolbar.hide()

        self.update()

        QApplication.processEvents()

        # Damos un instante al compositor para repintar
        # la pantalla después de ocultar la barra.
        QThread.msleep(120)

        QApplication.processEvents()

        # En Wayland/XWayland QScreen.grabWindow(0) puede
        # devolver una imagen negra porque X11 no tiene acceso
        # al contenido de las ventanas Wayland. Primero usamos
        # el portal oficial del escritorio y dejamos Qt como
        # respaldo para sesiones X11 reales.
        success = self._capture_with_portal(
            target
        )

        if not success:

            success = self._capture_with_qt(
                target
            )

        self.selected_object = previous_selection

        self.toolbar.show()
        self.toolbar.raise_()

        self.update()

        if success and target.exists():

            image = QImage(
                str(target)
            )

            if not image.isNull():

                QApplication.clipboard().setImage(
                    image
                )

            QToolTip.showText(
                self.capture_button.mapToGlobal(
                    self.capture_button.rect().bottomLeft()
                ),
                "Captura guardada y copiada\n"
                + str(target),
                self.capture_button
            )

            return

        QToolTip.showText(
            self.capture_button.mapToGlobal(
                self.capture_button.rect().bottomLeft()
            ),
            "No se pudo realizar la captura. "
            "La sesión no ofrece captura X11/XWayland.",
            self.capture_button
        )


    def _capture_with_portal(
        self,
        target
    ):

        bus = QDBusConnection.sessionBus()

        if not bus.isConnected():

            return False

        token = (
            "barra_"
            + uuid.uuid4().hex
        )

        sender = (
            bus.baseService()
            .lstrip(":")
            .replace(".", "_")
        )

        response_path = (
            "/org/freedesktop/portal/desktop/request/"
            + sender
            + "/"
            + token
        )

        bridge = PortalScreenshotBridge(
            self
        )

        loop = QEventLoop(
            self
        )

        result = {
            "done": False,
            "ok": False,
            "uri": "",
        }

        @Slot(int, object)
        def handle_response(
            code,
            values
        ):

            result["done"] = True

            if code == 0:

                uri = values.get(
                    "uri",
                    ""
                )

                if hasattr(
                    uri,
                    "variant"
                ):

                    uri = uri.variant()

                result["uri"] = str(
                    uri
                )

                result["ok"] = bool(
                    result["uri"]
                )

            loop.quit()

        bridge.response.connect(
            handle_response
        )

        connected = bus.connect(
            "",
            response_path,
            "org.freedesktop.portal.Request",
            "Response",
            bridge,
            "response",
        )

        if not connected:

            return False

        interface = QDBusInterface(
            "org.freedesktop.portal.Desktop",
            "/org/freedesktop/portal/desktop",
            "org.freedesktop.portal.Screenshot",
            bus,
        )

        if not interface.isValid():

            bus.disconnect(
                "",
                response_path,
                "org.freedesktop.portal.Request",
                "Response",
                bridge,
                "response",
            )

            return False

        reply = interface.call(
            "Screenshot",
            "",
            {
                "interactive": False,
                "handle_token": token,
            },
        )

        if reply.errorName():

            bus.disconnect(
                "",
                response_path,
                "org.freedesktop.portal.Request",
                "Response",
                bridge,
                "response",
            )

            return False

        timeout = QTimer(
            self
        )

        timeout.setSingleShot(
            True
        )

        timeout.timeout.connect(
            loop.quit
        )

        timeout.start(
            15000
        )

        loop.exec()

        timeout.stop()

        bus.disconnect(
            "",
            response_path,
            "org.freedesktop.portal.Request",
            "Response",
            bridge,
            "response",
        )

        if (
            not result["done"]
            or not result["ok"]
        ):

            return False

        source = QUrl(
            result["uri"]
        ).toLocalFile()

        if not source:

            return False

        source_path = Path(
            source
        )

        if (
            not source_path.exists()
            or source_path.stat().st_size == 0
        ):

            return False

        try:

            shutil.copyfile(
                source_path,
                target
            )

        except OSError:

            return False

        return (
            target.exists()
            and target.stat().st_size > 0
        )


    def _capture_with_qt(
        self,
        target
    ):

        screen = QApplication.primaryScreen()

        if screen is None:

            return False

        pixmap = screen.grabWindow(0)

        if pixmap.isNull():

            return False

        return pixmap.save(
            str(target),
            "PNG"
        )

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
