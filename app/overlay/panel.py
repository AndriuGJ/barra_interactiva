from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QButtonGroup,
    QColorDialog,
)

from app import icons
from app.config import QUICK_COLORS


class PanelMixin:

    """Barra interna de botones del overlay."""

    def create_toolbar(self):

        self.toolbar = QWidget(
            self
        )

        self.toolbar.setObjectName(
            "toolbar"
        )

        layout = QVBoxLayout(
            self.toolbar
        )

        layout.setContentsMargins(
            6, 6, 6, 6
        )

        layout.setSpacing(
            4
        )

        # -----------------------------------------------------
        # ARRASTRAR
        # -----------------------------------------------------

        self.drag_label = QLabel()

        self.drag_label.setPixmap(
            icons.icon_pixmap(
                icons.DRAG_ICON,
                color="#aaaaaa"
            )
        )

        self.drag_label.setObjectName(
            "dragHandle"
        )

        self.drag_label.setToolTip(
            "Mover barra"
        )

        self.drag_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.drag_label.setCursor(
            Qt.CursorShape.OpenHandCursor
        )

        self.drag_label.mousePressEvent = (
            self.toolbar_drag_press
        )

        self.drag_label.mouseMoveEvent = (
            self.toolbar_drag_move
        )

        self.drag_label.mouseReleaseEvent = (
            self.toolbar_drag_release
        )

        layout.addWidget(
            self.drag_label
        )

        # -----------------------------------------------------
        # HERRAMIENTAS
        # -----------------------------------------------------

        self.tool_group = QButtonGroup(
            self
        )

        self.tool_group.setExclusive(
            True
        )

        self.hand_button = QPushButton()

        self.prepare_tool_button(
            self.hand_button,
            "hand",
            "Seleccionar y mover"
        )

        layout.addWidget(
            self.hand_button
        )

        self.pencil_button = QPushButton()

        self.prepare_tool_button(
            self.pencil_button,
            "pencil",
            "Lápiz"
        )

        self.pencil_button.setChecked(
            True
        )

        layout.addWidget(
            self.pencil_button
        )

        self.rectangle_button = QPushButton()

        self.prepare_tool_button(
            self.rectangle_button,
            "rectangle",
            "Rectángulo"
        )

        layout.addWidget(
            self.rectangle_button
        )

        self.ellipse_button = QPushButton()

        self.prepare_tool_button(
            self.ellipse_button,
            "ellipse",
            "Círculo / Elipse"
        )

        layout.addWidget(
            self.ellipse_button
        )

        self.arrow_button = QPushButton()

        self.prepare_tool_button(
            self.arrow_button,
            "arrow",
            "Flecha"
        )

        layout.addWidget(
            self.arrow_button
        )

        self.text_button = QPushButton()

        self.prepare_tool_button(
            self.text_button,
            "text",
            "Texto"
        )

        layout.addWidget(
            self.text_button
        )

        self.eraser_button = QPushButton()

        self.prepare_tool_button(
            self.eraser_button,
            "eraser",
            "Goma"
        )

        layout.addWidget(
            self.eraser_button
        )

        self.add_separator(
            layout
        )

        # -----------------------------------------------------
        # TAMAÑO TEXTO
        # -----------------------------------------------------

        self.text_smaller_button = QPushButton(
            "A−"
        )

        self.text_smaller_button.setToolTip(
            "Reducir texto seleccionado"
        )

        self.text_smaller_button.clicked.connect(
            lambda: self.resize_selected_text(
                -2
            )
        )

        layout.addWidget(
            self.text_smaller_button
        )

        self.text_larger_button = QPushButton(
            "A+"
        )

        self.text_larger_button.setToolTip(
            "Aumentar texto seleccionado"
        )

        self.text_larger_button.clicked.connect(
            lambda: self.resize_selected_text(
                2
            )
        )

        layout.addWidget(
            self.text_larger_button
        )

        self.add_separator(
            layout
        )

        # -----------------------------------------------------
        # COLORES
        # -----------------------------------------------------

        self.color_buttons = {}

        for color, name in QUICK_COLORS:

            button = QPushButton(
                ""
            )

            button.setFixedSize(
                26,
                26
            )

            button.setToolTip(
                name
            )

            button.clicked.connect(
                lambda checked=False,
                c=color:
                    self.set_pen_color(c)
            )

            self.color_buttons[
                color
            ] = button

            layout.addWidget(
                button,
                0,
                Qt.AlignmentFlag.AlignHCenter
            )

        # -----------------------------------------------------
        # COLOR PERSONALIZADO
        # -----------------------------------------------------

        self.custom_color_button = QPushButton()

        icons.set_icon(
            self.custom_color_button,
            icons.CUSTOM_COLOR_ICON
        )

        self.custom_color_button.setToolTip(
            "Elegir cualquier color"
        )

        self.custom_color_button.clicked.connect(
            self.choose_custom_color
        )

        layout.addWidget(
            self.custom_color_button
        )

        self.add_separator(
            layout
        )

        # -----------------------------------------------------
        # GROSOR
        # -----------------------------------------------------

        self.thin_button = QPushButton(
            "━"
        )

        self.thin_button.setToolTip(
            "Trazo fino"
        )

        self.thin_button.clicked.connect(
            lambda: self.set_pen_width(2)
        )

        layout.addWidget(
            self.thin_button
        )

        self.medium_button = QPushButton(
            "━"
        )

        self.medium_button.setObjectName(
            "mediumWidth"
        )

        self.medium_button.setToolTip(
            "Trazo medio"
        )

        self.medium_button.clicked.connect(
            lambda: self.set_pen_width(5)
        )

        layout.addWidget(
            self.medium_button
        )

        self.thick_button = QPushButton(
            "━"
        )

        self.thick_button.setObjectName(
            "thickWidth"
        )

        self.thick_button.setToolTip(
            "Trazo grueso"
        )

        self.thick_button.clicked.connect(
            lambda: self.set_pen_width(9)
        )

        layout.addWidget(
            self.thick_button
        )

        self.add_separator(
            layout
        )

        # -----------------------------------------------------
        # DESHACER
        # -----------------------------------------------------

        self.undo_button = QPushButton()

        icons.set_icon(
            self.undo_button,
            icons.UNDO_ICON
        )

        self.undo_button.setToolTip(
            "Deshacer"
        )

        self.undo_button.clicked.connect(
            self.undo
        )

        layout.addWidget(
            self.undo_button
        )

        # -----------------------------------------------------
        # LIMPIAR
        # -----------------------------------------------------

        self.clear_button = QPushButton()

        icons.set_icon(
            self.clear_button,
            icons.CLEAR_ICON
        )

        self.clear_button.setToolTip(
            "Limpiar pantalla"
        )

        self.clear_button.clicked.connect(
            self.clear
        )

        layout.addWidget(
            self.clear_button
        )

        # -----------------------------------------------------
        # INTERACTUAR
        # -----------------------------------------------------

        self.stop_button = QPushButton(
            "Interactuar"
        )

        self.stop_button.setObjectName(
            "stopButton"
        )

        self.stop_button.setToolTip(
            "Volver a usar normalmente el escritorio"
        )

        self.stop_button.clicked.connect(
            self.stop_requested.emit
        )

        layout.addWidget(
            self.stop_button
        )

        self.toolbar.adjustSize()

        self.toolbar_dragging = False
        self.toolbar_drag_offset = QPoint()

        self.apply_base_styles()

        self.update_color_selection()

    # =========================================================
    # ESTILOS
    # =========================================================


    def apply_base_styles(self):

        self.toolbar.setStyleSheet("""
            #toolbar {
                background-color: #202124;
                border: 1px solid #444444;
                border-radius: 8px;
            }

            #dragHandle {
                color: #aaaaaa;
                font-size: 22px;
                padding-top: 4px;
                padding-bottom: 4px;
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

                border: 2px solid transparent;
                border-radius: 5px;

                min-width: 30px;
                min-height: 24px;

                padding: 3px 7px;

                font-size: 15px;
            }

            QPushButton:hover {
                background-color: #444444;
            }

            QPushButton:checked {
                background-color: #7460ee;
                border: 2px solid #a89aff;
            }

            #stopButton {
                background-color: #7460ee;
                min-width: 82px;
                font-size: 13px;
            }

            #stopButton:hover {
                background-color: #6652df;
            }

            #mediumWidth {
                font-size: 20px;
                font-weight: bold;
            }

            #thickWidth {
                font-size: 25px;
                font-weight: bold;
            }
        """)

    # =========================================================
    # SEPARADOR
    # =========================================================


    def add_separator(
        self,
        layout
    ):

        separator = QLabel(
            "─"
        )

        separator.setObjectName(
            "separator"
        )

        separator.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            separator
        )

    # =========================================================
    # HERRAMIENTAS
    # =========================================================


    def set_active_tool(
        self,
        tool
    ):

        buttons = {
            "hand": self.hand_button,
            "pencil": self.pencil_button,
            "rectangle": self.rectangle_button,
            "ellipse": self.ellipse_button,
            "arrow": self.arrow_button,
            "text": self.text_button,
            "eraser": self.eraser_button,
        }

        button = buttons.get(tool)

        if button:

            button.setChecked(True)

    def prepare_tool_button(
        self,
        button,
        tool_name,
        tooltip
    ):

        button.setCheckable(
            True
        )

        icons.set_icon(
            button,
            icons.TOOL_ICONS[tool_name]
        )

        button.setToolTip(
            tooltip
        )

        self.tool_group.addButton(
            button
        )

        button.clicked.connect(
            lambda checked=False,
            name=tool_name:
                self.set_tool(name)
        )


    def toolbar_size(self):

        return self.toolbar.size()

    def toolbar_global_position(self):

        return self.toolbar.mapToGlobal(
            QPoint(0, 0)
        )

    # =========================================================
    # MOVER TOOLBAR
    # =========================================================


    def toolbar_drag_press(
        self,
        event
    ):

        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):

            self.toolbar_dragging = True

            # Anclaje global: cursor menos la posición
            # de la barra, para no arrastrar un salto.
            self.toolbar_drag_offset = (
                event.globalPosition().toPoint()
                - self.mapToGlobal(
                    self.toolbar.pos()
                )
            )

            # El puntero se queda con la etiqueta
            # aunque salgas de ella.
            self.drag_label.grabMouse()

            self.drag_label.setCursor(
                Qt.CursorShape.ClosedHandCursor
            )


    def toolbar_drag_move(
        self,
        event
    ):

        if not self.toolbar_dragging:
            return

        target = (
            event.globalPosition().toPoint()
            - self.toolbar_drag_offset
        )

        position = self.mapFromGlobal(
            target
        )

        x = max(
            0,
            min(
                position.x(),
                self.width()
                - self.toolbar.width()
            )
        )

        y = max(
            0,
            min(
                position.y(),
                self.height()
                - self.toolbar.height()
            )
        )

        self.toolbar.move(
            x,
            y
        )


    def toolbar_drag_release(
        self,
        event
    ):

        self.toolbar_dragging = False

        self.drag_label.releaseMouse()

        self.drag_label.setCursor(
            Qt.CursorShape.OpenHandCursor
        )

    # =========================================================
    # HIT TEST
    # =========================================================


    def point_inside_toolbar(
        self,
        point
    ):

        return (
            self.toolbar
            .geometry()
            .contains(point)
        )

    # =========================================================
    # MOUSE PRESS
    # =========================================================


    def choose_custom_color(self):

        # Usamos un diálogo Qt NO NATIVO.
        # Es más fiable con nuestro overlay en Wayland.

        dialog = QColorDialog(
            self.pen_color,
            self.toolbar
        )

        dialog.setWindowTitle(
            "Seleccionar color"
        )

        dialog.setOption(
            QColorDialog.ColorDialogOption.DontUseNativeDialog,
            True
        )

        # Evitamos que sea hijo directo del overlay fullscreen.
        dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
        )

        result = dialog.exec()

        if not result:
            return

        color = (
            dialog.selectedColor()
        )

        if not color.isValid():
            return

        self.set_pen_color(
            color.name()
        )

    # =========================================================
    # COLOR SELECCIONADO
    # =========================================================


    def update_color_selection(self):

        current = (
            self.pen_color
            .name()
            .lower()
        )

        for color, button in (
            self.color_buttons.items()
        ):

            selected = (
                current
                == color.lower()
            )

            border = (
                "3px solid #ffffff"
                if selected
                else
                "2px solid #555555"
            )

            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {color};

                    border: {border};

                    border-radius: 13px;

                    min-width: 24px;
                    max-width: 24px;

                    min-height: 24px;
                    max-height: 24px;

                    padding: 0px;
                }}

                QPushButton:hover {{
                    border:
                        3px solid #a89aff;
                }}
                """
            )

        # Si el color actual no es uno
        # de los colores rápidos, mostramos
        # el color personalizado en ✿.

        predefined = [
            c.lower()
            for c in self.color_buttons.keys()
        ]

        if current not in predefined:

            self.custom_color_button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {current};

                    border:
                        3px solid #ffffff;

                    border-radius: 5px;
                }}
                """
            )

        else:

            self.custom_color_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #333333;

                    border:
                        2px solid transparent;

                    border-radius: 5px;
                }

                QPushButton:hover {
                    background-color: #444444;
                }
                """
            )

    # =========================================================
    # GROSOR
    # =========================================================
