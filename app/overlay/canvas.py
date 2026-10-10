import math

from PySide6.QtCore import Qt, QPoint, QRect

from app.config import SELECTION_COLOR
from PySide6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QPolygon,
    QFont,
)


class CanvasMixin:

    """Pintado de la pantalla: objetos y vista previa."""

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        for obj in self.objects:

            self.draw_object(
                painter,
                obj
            )

        # SELECCIÓN (MANO)
        if self.selected_object:

            rect = self.object_bbox(
                self.selected_object
            )

            painter.setPen(
                QPen(
                    QColor(SELECTION_COLOR),
                    2,
                    Qt.PenStyle.DashLine
                )
            )

            painter.setBrush(
                Qt.BrushStyle.NoBrush
            )

            painter.drawRect(
                rect.adjusted(
                    -5,
                    -5,
                    5,
                    5
                )
            )

        if not self.drawing:

            return

        # PREVISUALIZACIÓN LÁPIZ
        if (
            self.current_tool == "pencil"
            and len(self.current_path) > 1
        ):

            painter.setPen(
                self.create_pen(
                    self.pen_color,
                    self.pen_width
                )
            )

            painter.setBrush(
                Qt.BrushStyle.NoBrush
            )

            for i in range(
                1,
                len(self.current_path)
            ):

                painter.drawLine(
                    self.current_path[
                        i - 1
                    ],

                    self.current_path[
                        i
                    ]
                )

        elif self.current_tool == "rectangle":

            painter.setPen(
                self.create_pen(
                    self.pen_color,
                    self.pen_width
                )
            )

            painter.setBrush(
                QColor(self.pen_color)
                if self.fill_enabled
                else Qt.BrushStyle.NoBrush
            )

            painter.drawRect(
                QRect(
                    self.start_point,
                    self.current_point
                ).normalized()
            )

        elif self.current_tool == "ellipse":

            painter.setPen(
                self.create_pen(
                    self.pen_color,
                    self.pen_width
                )
            )

            painter.setBrush(
                QColor(self.pen_color)
                if self.fill_enabled
                else Qt.BrushStyle.NoBrush
            )

            painter.drawEllipse(
                QRect(
                    self.start_point,
                    self.current_point
                ).normalized()
            )

        elif self.current_tool == "arrow":

            self.draw_arrow(
                painter,
                self.start_point,
                self.current_point,
                self.pen_color,
                self.pen_width
            )

    # =========================================================
    # DIBUJAR OBJETOS
    # =========================================================


    def draw_object(
        self,
        painter,
        obj
    ):

        if obj["type"] == "text":

            painter.setPen(
                obj["color"]
            )

            font = QFont()

            font.setPointSize(
                obj["size"]
            )

            font.setBold(
                True
            )

            painter.setFont(
                font
            )

            painter.drawText(
                obj["position"],
                obj["text"]
            )

            return

        painter.setPen(
            self.create_pen(
                obj["color"],
                obj["width"]
            )
        )

        if obj["type"] == "pencil":

            points = obj[
                "points"
            ]

            for i in range(
                1,
                len(points)
            ):

                painter.drawLine(
                    points[i - 1],
                    points[i]
                )

        elif obj["type"] == "rectangle":

            # El relleno es una propiedad de cada forma
            # (lo decide el botón de relleno al dibujarla).
            painter.setBrush(
                QColor(obj["color"])
                if obj.get("filled", False)
                else Qt.BrushStyle.NoBrush
            )

            painter.drawRect(
                QRect(
                    obj["start"],
                    obj["end"]
                ).normalized()
            )

        elif obj["type"] == "ellipse":

            painter.setBrush(
                QColor(obj["color"])
                if obj.get("filled", False)
                else Qt.BrushStyle.NoBrush
            )

            painter.drawEllipse(
                QRect(
                    obj["start"],
                    obj["end"]
                ).normalized()
            )

        elif obj["type"] == "arrow":

            self.draw_arrow(
                painter,
                obj["start"],
                obj["end"],
                obj["color"],
                obj["width"]
            )

    # =========================================================
    # PEN
    # =========================================================


    def create_pen(
        self,
        color,
        width
    ):

        return QPen(
            QColor(color),
            width,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin
        )

    # =========================================================
    # FLECHA
    # =========================================================


    def draw_arrow(
        self,
        painter,
        start,
        end,
        color,
        width
    ):

        painter.setPen(
            self.create_pen(
                color,
                width
            )
        )

        painter.setBrush(
            QColor(color)
        )

        painter.drawLine(
            start,
            end
        )

        dx = (
            end.x()
            - start.x()
        )

        dy = (
            end.y()
            - start.y()
        )

        if dx == 0 and dy == 0:
            return

        angle = math.atan2(
            dy,
            dx
        )

        size = max(
            12,
            width * 4
        )

        p1 = QPoint(
            int(
                end.x()
                + size
                * math.cos(
                    angle
                    + math.radians(150)
                )
            ),

            int(
                end.y()
                + size
                * math.sin(
                    angle
                    + math.radians(150)
                )
            )
        )

        p2 = QPoint(
            int(
                end.x()
                + size
                * math.cos(
                    angle
                    - math.radians(150)
                )
            ),

            int(
                end.y()
                + size
                * math.sin(
                    angle
                    - math.radians(150)
                )
            )
        )

        painter.drawPolygon(
            QPolygon([
                end,
                p1,
                p2
            ])
        )

        # El relleno solo es para la punta: lo quitamos
        # para que las formas siguientes no se pinten
        # rellenadas.
        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

    # =========================================================
    # GOMA
    # =========================================================
