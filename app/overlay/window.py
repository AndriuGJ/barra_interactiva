import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QPoint,
    Signal,
    Slot,
    SLOT,
    QSettings,
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
from PySide6.QtGui import QColor, QImage, QCursor, QKeySequence
from PySide6.QtWidgets import (
    QWidget,
    QApplication,
    QFileDialog,
    QToolTip,
    QDialog,
)

from app import icons
from app.config import DEFAULT_PEN_COLOR
from app.hotkey import saved_hotkey, hotkey_is_plain_letter
from app.overlay.objects import ObjectsMixin
from app.overlay.canvas import CanvasMixin
from app.overlay.panel import PanelMixin


def capture_settings():

    return QSettings(
        "BarraInteractiva",
        "BarraInteractiva"
    )


class PortalScreenshotBridge(QObject):

    response = Signal(int, object)

    # PySide6 solo enlaza la señal D-Bus si el slot se
    # declara con los tipos exactos de la señal
    # org.freedesktop.portal.Request.Response (u, a{sv})
    # y se referencia con la macro SLOT().
    @Slot("uint", "QVariantMap")
    def on_response(
        self,
        code,
        values
    ):

        self.response.emit(
            int(code),
            dict(values) if values else {}
        )


class DrawingOverlay(ObjectsMixin, CanvasMixin, PanelMixin, QWidget):

    """Pantalla completa donde se dibuja.

    Gestiona el ciclo activar/desactivar, los eventos
    de ratón y teclado, y la comunicación con la
    barra interna (PanelMixin) y el lienzo (CanvasMixin).
    """

    stop_requested = Signal()

    # F: alterna "modo normal" (usar el equipo) y
    # la pantalla de dibujo.
    toggle_requested = Signal()

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

        self.fill_enabled = False

        # =====================================================
        # ZOOM (lupa del escritorio)
        # =====================================================

        # Solo acerca: pasos definidos del 110% al 200%.
        self.zoom_levels = (
            1.1, 1.2, 1.3, 1.4, 1.5,
            1.6, 1.7, 1.8, 1.9, 2.0,
        )

        self.zoom_mode = False

        self.zooming = False

        self.zoom_index = -1

        self.original_mag_factor = None

        # Solo apagamos la lupa si la encendimos
        # nosotros; una lupa ajena (accesibilidad) se
        # queda como está.
        self.magnifier_on = False

        self.original_enabled = None

        self.restore_factor_timer = QTimer(self)

        self.restore_factor_timer.setSingleShot(
            True
        )

        self.restore_factor_timer.setInterval(
            1000
        )

        self.restore_factor_timer.timeout.connect(
            self.restore_mag_factor_now
        )

        self.zoom_timer = QTimer(self)

        self.zoom_timer.setInterval(
            500
        )

        self.zoom_timer.timeout.connect(
            self.zoom_in
        )

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

        # Cada sesión de dibujo empieza al 100%
        self.set_zoom_mode(
            False
        )

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

        self.set_zoom_mode(False)

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

        # Clic derecho con la lupa activa: cancelar
        # el zoom (volver al 100%)
        if (
            event.button()
            == Qt.MouseButton.RightButton
            and self.zoom_mode
        ):

            self.set_zoom_mode(False)

            return

        if (
            event.button()
            != Qt.MouseButton.LeftButton
        ):
            return

        # ZOOM: con la lupa activa el clic sube un
        # nivel (y sigue subiendo si se mantiene)
        if self.zoom_mode:

            if self.text_editor:

                self.confirm_text()

            self.zooming = True

            self.zoom_in()

            self.zoom_timer.start()

            self.update()

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

        if self.zooming:
            return

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

        # ZOOM: al soltar el clic se mantiene el
        # nivel hasta apagar la lupa
        if self.zooming:

            self.zooming = False

            self.zoom_timer.stop()

            self.update()

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

                # Solo rectángulos y círculos lo usan al
                # pintarse; las demás formas lo ignoran.
                "filled": self.fill_enabled,
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

        # Carpeta elegida por el usuario en Configuración.
        custom = capture_settings().value(
            "screenshots_directory",
            ""
        )

        if custom and Path(custom).is_dir():

            return Path(custom)

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


    def refresh_directory_tooltip(self):

        self.config_button.setToolTip(
            "Preferencias — atajo: "
            + saved_hotkey()
            + " | carpeta de capturas: "
            + str(self.screenshots_directory())
        )


    def open_preferences(self):

        from app.preferences import PreferencesDialog

        dialog = PreferencesDialog(
            screenshots_directory=str(
                self.screenshots_directory()
            ),
            parent=self,
        )

        dialog.settings_changed.connect(
            self.refresh_directory_tooltip
        )

        if (
            dialog.exec()
            == QDialog.DialogCode.Accepted
        ):

            self.refresh_directory_tooltip()


    def hotkey_matches(self, event):

        modifiers = event.modifiers()

        pressed = QKeySequence(
            int(
                getattr(
                    modifiers,
                    "value",
                    modifiers,
                )
            )
            | int(event.key())
        )

        return (
            pressed.toString().lower()
            == QKeySequence(saved_hotkey())
            .toString()
            .lower()
        )


    def choose_screenshots_directory(self):

        current = self.screenshots_directory()

        directory = QFileDialog.getExistingDirectory(
            self,
            "Carpeta donde guardar las capturas",
            str(current)
        )

        if not directory:

            return

        capture_settings().setValue(
            "screenshots_directory",
            directory
        )

        capture_settings().sync()

        self.refresh_directory_tooltip()

        QToolTip.showText(
            QCursor.pos(),
            "Carpeta de capturas:\n" + directory
        )


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
            "No se pudo capturar la pantalla. "
            "Revisa los permisos de captura del "
            "escritorio (portal de Wayland).",
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
            SLOT("on_response(uint,QVariantMap)"),
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
                SLOT("on_response(uint,QVariantMap)"),
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
                SLOT("on_response(uint,QVariantMap)"),
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
            SLOT("on_response(uint,QVariantMap)"),
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

        # El portal guarda su propia copia en Imágenes;
        # la movemos a nuestra carpeta para que solo
        # quede una imagen.
        try:

            if source_path != target:

                shutil.move(
                    str(source_path),
                    str(target)
                )

        except OSError:

            try:

                shutil.copyfile(
                    source_path,
                    target
                )

                source_path.unlink(
                    missing_ok=True
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

        # En Wayland/XWayland grabWindow devuelve una imagen
        # completamente negra en lugar de fallar. En ese caso
        # no guardamos basura y dejamos que se avise al usuario.
        image = pixmap.toImage()

        if image.isNull():

            return False

        black = True

        for x in range(
            10,
            image.width(),
            max(1, image.width() // 8)
        ):

            for y in range(
                10,
                image.height(),
                max(1, image.height() // 6)
            ):

                if image.pixelColor(
                    x,
                    y
                ).alpha() > 0 and image.pixelColor(
                    x,
                    y
                ).rgb() != 0xFF000000:

                    black = False

                    break

            if not black:
                break

        if black:

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
    # RELLENO
    # =========================================================


    def set_fill(
        self,
        enabled
    ):

        # Afecta a las formas que se dibujen a partir
        # de ahora; las ya dibujadas no cambian.
        self.fill_enabled = bool(
            enabled
        )

        button = getattr(
            self,
            "fill_button",
            None
        )

        if button and button.isChecked() != self.fill_enabled:

            button.setChecked(self.fill_enabled)

        self.update()

    # =========================================================
    # ZOOM
    # =========================================================


    def set_zoom_mode(
        self,
        enabled
    ):

        self.zoom_mode = bool(
            enabled
        )

        button = getattr(
            self,
            "zoom_button",
            None
        )

        if button and button.isChecked() != self.zoom_mode:

            button.setChecked(self.zoom_mode)

        if not self.zoom_mode:

            self.zoom_off()

        elif self.zoom_index < 0:

            # Encender la lupa arranca ya al primer
            # nivel (110%).
            self.zoom_in()

        self.update_zoom_tooltip()

        self.update()

    def zoom_in(self):

        if self.zoom_index >= (
            len(self.zoom_levels) - 1
        ):

            # Tope: 200%, solo acerca.
            self.zoom_timer.stop()

            return

        self.zoom_index += 1

        self.apply_magnifier(
            self.zoom_levels[self.zoom_index]
        )

        self.update_zoom_tooltip()

    def zoom_off(self):

        self.zoom_timer.stop()

        self.zooming = False

        self.zoom_index = -1

        self.apply_magnifier(
            None
        )

        self.update_zoom_tooltip()

    def apply_magnifier(
        self,
        factor
    ):

        # Zoom de toda la pantalla con la lupa del
        # escritorio de GNOME. Si no existe, no pasa
        # nada: la aplicación sigue funcionando.
        if not shutil.which("gsettings"):

            return

        schema_a11y = (
            "org.gnome.desktop.a11y.applications"
        )

        schema_mag = (
            "org.gnome.desktop.a11y.magnifier"
        )

        try:

            if factor is None:

                if not self.magnifier_on:

                    return

                self.magnifier_on = False

                if (
                    str(self.original_enabled)
                    .strip("'")
                    == "true"
                ):

                    # Lupa ajena: devolver su factor y
                    # dejarla encendida como estaba.
                    if self.original_mag_factor:

                        subprocess.run(
                            [
                                "gsettings",
                                "set",
                                schema_mag,
                                "mag-factor",
                                self.original_mag_factor,
                            ],
                            capture_output=True,
                            timeout=2,
                        )

                    self.clear_magnifier_state()

                    return

                # Lupa nuestra: con la lupa aún encendida
                # bajamos la amplificación a 1.0 y solo
                # después la apagamos. Apagar con el
                # factor alto dejaba el cursor real
                # desaparecido un rato (GNOME oculta el
                # cursor mientras amplía y tarda en
                # re-mostrarlo al cortar de golpe).
                subprocess.run(
                    [
                        "gsettings",
                        "set",
                        schema_mag,
                        "mag-factor",
                        "1.0",
                    ],
                    capture_output=True,
                    timeout=2,
                )

                subprocess.run(
                    [
                        "gsettings",
                        "set",
                        schema_a11y,
                        "screen-magnifier-enabled",
                        "false",
                    ],
                    capture_output=True,
                    timeout=2,
                )

                original = self.original_mag_factor

                self.original_enabled = None

                if (
                    original
                    and str(original)
                    .strip("'")
                    != "1.0"
                ):

                    # El factor original vuelve pasado un
                    # momento, con el cursor ya visible.
                    # Se conserva original_mag_factor
                    # para el temporizador.
                    self.restore_factor_timer.start()

                else:

                    self.clear_magnifier_state()

                return

            if not self.magnifier_on:

                if (
                    self.restore_factor_timer
                    .isActive()
                ):

                    # Terminar la restauración pendiente
                    # antes de guardar un estado nuevo.
                    self.restore_mag_factor_now()

                # Primer encendido: guardar el estado
                # previo del sistema.
                result = subprocess.run(
                    [
                        "gsettings",
                        "get",
                        schema_a11y,
                        "screen-magnifier-enabled",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )

                self.original_enabled = (
                    result.stdout.strip() or None
                )

                result = subprocess.run(
                    [
                        "gsettings",
                        "get",
                        schema_mag,
                        "mag-factor",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )

                self.original_mag_factor = (
                    result.stdout.strip() or None
                )

                subprocess.run(
                    [
                        "gsettings",
                        "set",
                        schema_mag,
                        "mag-factor",
                        str(factor),
                    ],
                    capture_output=True,
                    timeout=2,
                )

                subprocess.run(
                    [
                        "gsettings",
                        "set",
                        schema_a11y,
                        "screen-magnifier-enabled",
                        "true",
                    ],
                    capture_output=True,
                    timeout=2,
                )

                self.magnifier_on = True

                return

            # Subida de nivel: solo cambia el factor.
            subprocess.run(
                [
                    "gsettings",
                    "set",
                    schema_mag,
                    "mag-factor",
                    str(factor),
                ],
                capture_output=True,
                timeout=2,
            )

        except (
            OSError,
            subprocess.SubprocessError,
        ):

            pass

    def clear_magnifier_state(self):

        self.original_mag_factor = None

        self.original_enabled = None

    def restore_mag_factor_now(self):

        self.restore_factor_timer.stop()

        if self.magnifier_on:

            self.clear_magnifier_state()

            return

        original = self.original_mag_factor

        self.clear_magnifier_state()

        if not original:

            return

        if not shutil.which("gsettings"):

            return

        try:

            subprocess.run(
                [
                    "gsettings",
                    "set",
                    "org.gnome.desktop.a11y.magnifier",
                    "mag-factor",
                    str(original),
                ],
                capture_output=True,
                timeout=2,
            )

        except (
            OSError,
            subprocess.SubprocessError,
        ):

            pass

    def update_zoom_tooltip(self):

        button = getattr(
            self,
            "zoom_button",
            None
        )

        if button is None:

            return

        if self.zoom_index < 0:

            button.setToolTip(
                "Zoom de pantalla: apagado"
            )

        else:

            percent = int(
                self.zoom_levels[self.zoom_index]
                * 100
            )

            button.setToolTip(
                f"Zoom de pantalla: {percent}% — "
                "clic izq. sube un nivel, "
                "clic der. cancela"
            )

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

        # Atajo: alterna entre el modo "usar el equipo
        # normal" y la barra interactiva. Es el
        # respaldo del atajo global del sistema.
        # La tecla es configurable en Preferencias.
        if self.hotkey_matches(event) and (
            self.text_editor is None
            or not hotkey_is_plain_letter(
                saved_hotkey()
            )
        ):

            self.toggle_requested.emit()

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
