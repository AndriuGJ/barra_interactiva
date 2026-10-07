import math

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QColor, QFont, QFontMetrics
from PySide6.QtWidgets import QLineEdit

from app.config import SELECTION_COLOR


class ObjectsMixin:

    """Modelo de objetos: textos, goma y pruebas de contacto."""

    def open_text_editor(
        self,
        point
    ):

        self.cancel_text_editor()

        self.text_position = QPoint(
            point
        )

        self.text_editor = QLineEdit(
            self
        )

        self.text_editor.setPlaceholderText(
            "Escribe y presiona Enter"
        )

        self.text_editor.setGeometry(
            point.x(),
            point.y(),
            300,
            40
        )

        self.text_editor.setStyleSheet(f"""
            QLineEdit {{
                background-color:
                    rgba(32, 33, 36, 245);

                color: white;

                border:
                    2px solid {SELECTION_COLOR};

                border-radius: 5px;

                padding: 6px 10px;

                font-size: 16px;
            }}
        """)

        self.text_editor.returnPressed.connect(
            self.confirm_text
        )

        self.text_editor.show()
        self.text_editor.raise_()
        self.text_editor.setFocus()


    def confirm_text(self):

        if not self.text_editor:
            return

        text = (
            self.text_editor
            .text()
            .strip()
        )

        if text:

            obj = {
                "type": "text",

                "position": QPoint(
                    self.text_position
                ),

                "text": text,

                "color": QColor(
                    self.pen_color
                ),

                "size": 20,
            }

            self.objects.append(
                obj
            )

            self.selected_object = obj

        self.cancel_text_editor()

        self.hand_button.setChecked(
            True
        )

        self.current_tool = "hand"

        self.update()


    def cancel_text_editor(self):

        if self.text_editor:

            self.text_editor.hide()

            self.text_editor.deleteLater()

            self.text_editor = None

    # =========================================================
    # ENCONTRAR OBJETO (MANO)
    # =========================================================


    def find_object_at(
        self,
        point
    ):

        for obj in reversed(
            self.objects
        ):

            if self.object_hits(
                obj,
                point
            ):

                return obj

        return None


    def object_hits(
        self,
        obj,
        point
    ):

        if obj["type"] == "text":

            return (
                self.get_text_rect(obj)
                .adjusted(
                    -6,
                    -6,
                    6,
                    6
                )
                .contains(point)
            )

        if obj["type"] in [
            "rectangle",
            "ellipse"
        ]:

            return (
                self.object_bbox(obj)
                .adjusted(
                    -8,
                    -8,
                    8,
                    8
                )
                .contains(point)
            )

        if obj["type"] == "arrow":

            return self.point_near_line(
                point,
                obj["start"],
                obj["end"],
                10
            )

        if obj["type"] == "pencil":

            radius = 10

            for p in obj["points"]:

                if (
                    abs(
                        p.x()
                        - point.x()
                    )
                    < radius
                    and
                    abs(
                        p.y()
                        - point.y()
                    )
                    < radius
                ):

                    return True

        return False


    def object_bbox(
        self,
        obj
    ):

        if obj["type"] == "text":

            return self.get_text_rect(obj)

        if obj["type"] == "pencil":

            points = obj["points"]

            if not points:
                return QRect()

            xs = [p.x() for p in points]

            ys = [p.y() for p in points]

            stroke = obj.get("width", 4)

            return QRect(
                min(xs),
                min(ys),
                max(xs) - min(xs),
                max(ys) - min(ys)
            ).adjusted(
                -stroke,
                -stroke,
                stroke,
                stroke
            )

        return QRect(
            obj["start"],
            obj["end"]
        ).normalized()


    def translate_object(
        self,
        obj,
        dx,
        dy
    ):

        delta = QPoint(dx, dy)

        if obj["type"] == "text":

            obj["position"] = (
                obj["position"] + delta
            )

            return

        if obj["type"] == "pencil":

            obj["points"] = [
                p + delta
                for p in obj["points"]
            ]

            return

        obj["start"] = (
            obj["start"] + delta
        )

        obj["end"] = (
            obj["end"] + delta
        )


    def delete_selected(self):

        if not self.selected_object:
            return

        for i, obj in enumerate(
            self.objects
        ):

            if obj is self.selected_object:

                del self.objects[i]

                break

        self.selected_object = None

        self.update()


    def drop_selection_if(
        self,
        obj
    ):

        if self.selected_object is obj:

            self.selected_object = None


    def get_text_rect(
        self,
        obj
    ):

        font = QFont()

        font.setPointSize(
            obj["size"]
        )

        font.setBold(
            True
        )

        metrics = QFontMetrics(
            font
        )

        width = (
            metrics.horizontalAdvance(
                obj["text"]
            )
        )

        height = metrics.height()

        return QRect(
            obj["position"].x(),
            obj["position"].y()
            - height,

            width,
            height + 5
        )

    # =========================================================
    # TAMAÑO TEXTO
    # =========================================================


    def resize_selected_text(
        self,
        amount
    ):

        if not self.selected_object:
            return

        if (
            self.selected_object["type"]
            != "text"
        ):
            return

        size = (
            self.selected_object["size"]
            + amount
        )

        size = max(
            8,
            min(
                72,
                size
            )
        )

        self.selected_object[
            "size"
        ] = size

        self.update()

    # =========================================================
    # PAINT
    # =========================================================


    def erase_at(
        self,
        point
    ):

        radius = 18

        for i in range(
            len(self.objects) - 1,
            -1,
            -1
        ):

            obj = self.objects[i]

            if obj["type"] == "text":

                rect = (
                    self.get_text_rect(obj)
                    .adjusted(
                        -radius,
                        -radius,
                        radius,
                        radius
                    )
                )

                if rect.contains(point):

                    self.drop_selection_if(
                        obj
                    )

                    del self.objects[i]

                    self.update()

                    return

            elif obj["type"] == "pencil":

                for p in obj["points"]:

                    if (
                        abs(
                            p.x()
                            - point.x()
                        )
                        < radius
                        and
                        abs(
                            p.y()
                            - point.y()
                        )
                        < radius
                    ):

                        self.drop_selection_if(
                            obj
                        )

                        del self.objects[i]

                        self.update()

                        return

            elif obj["type"] in [
                "rectangle",
                "ellipse"
            ]:

                rect = QRect(
                    obj["start"],
                    obj["end"]
                ).normalized()

                if (
                    rect.adjusted(
                        -radius,
                        -radius,
                        radius,
                        radius
                    )
                    .contains(point)
                ):

                    self.drop_selection_if(
                        obj
                    )

                    del self.objects[i]

                    self.update()

                    return

            elif obj["type"] == "arrow":

                if self.point_near_line(
                    point,
                    obj["start"],
                    obj["end"],
                    radius
                ):

                    self.drop_selection_if(
                        obj
                    )

                    del self.objects[i]

                    self.update()

                    return

    # =========================================================
    # LINE HIT TEST
    # =========================================================


    def point_near_line(
        self,
        point,
        start,
        end,
        tolerance
    ):

        x = point.x()
        y = point.y()

        x1 = start.x()
        y1 = start.y()

        x2 = end.x()
        y2 = end.y()

        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:

            return (
                math.hypot(
                    x - x1,
                    y - y1
                )
                <= tolerance
            )

        t = (
            (
                (x - x1) * dx
                + (y - y1) * dy
            )
            /
            (
                dx * dx
                + dy * dy
            )
        )

        t = max(
            0,
            min(
                1,
                t
            )
        )

        nx = (
            x1
            + t * dx
        )

        ny = (
            y1
            + t * dy
        )

        return (
            math.hypot(
                x - nx,
                y - ny
            )
            <= tolerance
        )

    # =========================================================
    # COLOR
    # =========================================================
