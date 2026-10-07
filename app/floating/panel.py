from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
)

from app import icons
from app.config import QUICK_COLORS


class FloatingPanel(QWidget):

    """Botones y colores de la barra flotante.

    No decide nada: solo avisa de lo que pulsa
    el usuario mediante señales.
    """

    tool_selected = Signal(str)

    color_selected = Signal(str)

    custom_color_requested = Signal()

    close_requested = Signal()

    minimize_requested = Signal()

    expand_requested = Signal()

    def __init__(self):

        super().__init__()

        self.setObjectName(
            "container"
        )

        self.collapsed = False

        self.dragging = False

        self.drag_offset = QPoint()

        self.tool_buttons = []

        self.create_ui()

    def create_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            8, 8, 8, 8
        )

        layout.setSpacing(5)

        # MOVER
        self.drag = QLabel()

        self.drag.setPixmap(
            icons.icon_pixmap(
                icons.DRAG_ICON,
                color="#aaaaaa"
            )
        )

        self.drag.setObjectName("dragHandle")
        self.drag.setToolTip("Mover barra")
        self.drag.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.drag.setCursor(
            Qt.CursorShape.OpenHandCursor
        )

        self.drag.mousePressEvent = (
            self.start_system_drag
        )

        self.drag.mouseMoveEvent = (
            self.drag_move
        )

        self.drag.mouseReleaseEvent = (
            self.drag_release
        )

        layout.addWidget(self.drag)

        # HERRAMIENTAS
        self.add_tool(
            layout,
            "hand",
            "Seleccionar y mover"
        )

        self.add_tool(
            layout,
            "pencil",
            "Lápiz"
        )

        self.add_tool(
            layout,
            "rectangle",
            "Rectángulo"
        )

        self.add_tool(
            layout,
            "ellipse",
            "Círculo"
        )

        self.add_tool(
            layout,
            "arrow",
            "Flecha"
        )

        self.add_tool(
            layout,
            "text",
            "Texto"
        )

        self.add_tool(
            layout,
            "eraser",
            "Goma"
        )

        separator = QLabel("─")

        separator.setObjectName("separator")
        separator.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(separator)

        # COLORES RÁPIDOS
        for color, name in QUICK_COLORS:

            button = QPushButton("")

            button.setFixedSize(
                24,
                24
            )

            button.setToolTip(name)

            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {color};
                    border-radius: 12px;
                    border: 1px solid #666666;
                }}

                QPushButton:hover {{
                    border: 2px solid #ffffff;
                }}
                """
            )

            button.clicked.connect(
                lambda checked=False,
                c=color:
                    self.color_selected.emit(c)
            )

            layout.addWidget(
                button,
                0,
                Qt.AlignmentFlag.AlignHCenter
            )

        # COLOR PERSONALIZADO
        custom = QPushButton()

        icons.set_icon(
            custom,
            icons.CUSTOM_COLOR_ICON
        )

        custom.setToolTip(
            "Elegir cualquier color"
        )

        custom.clicked.connect(
            self.custom_color_requested.emit
        )

        layout.addWidget(
            custom
        )

        # MINIMIZAR
        self.minimize_button = QPushButton()

        icons.set_icon(
            self.minimize_button,
            icons.MINIMIZE_ICON
        )

        self.minimize_button.setObjectName(
            "minimizeButton"
        )

        self.minimize_button.setToolTip(
            "Minimizar barra"
        )

        self.minimize_button.clicked.connect(
            self.minimize_requested.emit
        )

        layout.addWidget(
            self.minimize_button
        )

        # RESTAURAR (solo con la barra minimizada)
        self.expand_button = QPushButton()

        icons.set_icon(
            self.expand_button,
            icons.EXPAND_ICON
        )

        self.expand_button.setObjectName(
            "expandButton"
        )

        self.expand_button.setToolTip(
            "Restaurar barra"
        )

        self.expand_button.clicked.connect(
            self.expand_requested.emit
        )

        self.expand_button.hide()

        layout.addWidget(
            self.expand_button
        )

        # CERRAR
        close_button = QPushButton()

        icons.set_icon(
            close_button,
            icons.CLOSE_ICON
        )

        close_button.setObjectName(
            "closeButton"
        )

        close_button.setToolTip(
            "Cerrar aplicación"
        )

        close_button.clicked.connect(
            self.close_requested.emit
        )

        layout.addWidget(
            close_button
        )

        self.setStyleSheet("""
            #container {
                background-color: #202124;
                border: 1px solid #444444;
                border-radius: 8px;
                min-width: 110px;
            }

            #dragHandle {
                color: #aaaaaa;
                font-size: 22px;
                padding-top: 6px;
                padding-bottom: 6px;
            }

            #dragHandle:hover {
                color: #ffffff;
            }

            #separator {
                color: #666666;
            }

            QPushButton {
                background-color: #333333;
                color: #ffffff;

                border: none;
                border-radius: 5px;

                min-width: 30px;
                min-height: 30px;

                padding: 4px 7px;

                font-size: 15px;
            }

            QPushButton:hover {
                background-color: #444444;
            }

            #closeButton:hover {
                background-color: #ea5b5d;
            }
        """)

        self.adjustSize()

    # =========================================================
    # HERRAMIENTAS
    # =========================================================

    def add_tool(
        self,
        layout,
        tool,
        tooltip
    ):

        button = QPushButton()

        icons.set_icon(
            button,
            icons.TOOL_ICONS[tool]
        )

        button.setToolTip(
            tooltip
        )

        button.clicked.connect(
            lambda checked=False,
            t=tool:
                self.tool_selected.emit(t)
        )

        self.tool_buttons.append(
            button
        )

        layout.addWidget(
            button
        )

    # =========================================================
    # MINIMIZAR
    # =========================================================

    def set_collapsed(
        self,
        collapsed
    ):

        if self.collapsed == collapsed:
            return

        self.collapsed = collapsed

        layout = self.layout()

        for i in range(
            layout.count()
        ):

            widget = (
                layout.itemAt(i).widget()
            )

            if widget is None:
                continue

            if widget is self.drag:
                continue

            if collapsed:

                widget.setVisible(
                    widget
                    is self.expand_button
                )

            else:

                widget.setVisible(
                    widget
                    is not self.expand_button
                )

        self.adjustSize()

    # =========================================================
    # MOVER VENTANA
    # =========================================================

    def start_system_drag(
        self,
        event
    ):

        if (
            event.button()
            != Qt.MouseButton.LeftButton
        ):
            return

        window = self.window()

        if window is None:
            return

        handle = window.windowHandle()

        if handle is None:
            handle = self.windowHandle()

        # El movimiento lo gestiona el sistema operativo.
        if (
            handle is not None
            and handle.startSystemMove()
        ):
            return

        # Respaldo: arrastre manual con el puntero.
        self.dragging = True

        self.drag_offset = (
            event.globalPosition().toPoint()
            - window.pos()
        )

        self.grabMouse()

        self.setCursor(
            Qt.CursorShape.ClosedHandCursor
        )

    def drag_move(
        self,
        event
    ):

        if not self.dragging:
            return

        window = self.window()

        if window is None:
            return

        target = (
            event.globalPosition().toPoint()
            - self.drag_offset
        )

        area = None

        if window.screen() is not None:

            area = (
                window.screen()
                .availableGeometry()
            )

        if area is not None:

            x = max(
                area.left(),

                min(
                    target.x(),
                    area.right()
                    - window.width()
                    + 1
                )
            )

            y = max(
                area.top(),

                min(
                    target.y(),
                    area.bottom()
                    - window.height()
                    + 1
                )
            )

            target.setX(x)
            target.setY(y)

        window.move(target)

    def drag_release(
        self,
        event
    ):

        if not self.dragging:
            return

        self.dragging = False

        self.releaseMouse()

        self.setCursor(
            Qt.CursorShape.OpenHandCursor
        )
