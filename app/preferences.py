"""Diálogo de preferencias: tecla del atajo y carpeta
de capturas."""

from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QKeySequenceEdit,
    QVBoxLayout,
)

from app.hotkey import (
    saved_hotkey,
    save_hotkey,
    qt_to_gtk,
    set_shortcut_binding,
)
from app.overlay.window import capture_settings


class PreferencesDialog(QDialog):

    settings_changed = Signal()

    def __init__(
        self,
        screenshots_directory="",
        parent=None,
    ):

        super().__init__(parent)

        self.setWindowTitle("Preferencias")

        self._initial_directory = str(
            screenshots_directory
        )

        self._directory = self._initial_directory

        self.hotkey_edit = QKeySequenceEdit(
            QKeySequence(saved_hotkey()),
            self,
        )

        self.hotkey_edit.setMaximumSequenceLength(1)

        hint = QLabel(
            "Una tecla o una combinación de 2, "
            "ej.: F, Ctrl+Alt+F, Shift+F5. "
            "Elige una tecla que no uses en "
            "otro programa.",
            self,
        )

        hint.setWordWrap(True)

        self.folder_value = QLabel(
            self._directory,
            self,
        )

        self.folder_value.setWordWrap(True)

        browse_button = QPushButton(
            "Examinar...",
            self,
        )

        browse_button.clicked.connect(
            self._choose_directory
        )

        folder_row = QHBoxLayout()

        folder_row.addWidget(self.folder_value)

        folder_row.addWidget(browse_button)

        form = QFormLayout()

        form.addRow(
            "Tecla del atajo:",
            self.hotkey_edit,
        )

        form.addRow("", hint)

        form.addRow(
            "Carpeta de capturas:",
            folder_row,
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            self,
        )

        buttons.accepted.connect(self.accept)

        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)

        layout.addLayout(form)

        layout.addWidget(buttons)

    def _choose_directory(self):

        directory = QFileDialog.getExistingDirectory(
            self,
            "Carpeta donde guardar las capturas",
            self._directory,
        )

        if not directory:

            return

        self._directory = directory

        self.folder_value.setText(directory)

    def apply(self):

        qt = (
            self.hotkey_edit.keySequence()
            .toString()
            .strip()
        )

        if not qt:

            QMessageBox.warning(
                self,
                "Preferencias",
                "Pulsa la tecla del atajo.",
            )

            return False

        if qt_to_gtk(qt) is None:

            QMessageBox.warning(
                self,
                "Preferencias",
                f"La tecla «{qt}» no es compatible. "
                "Usa una tecla simple o con Ctrl, "
                "Alt, Shift o Super.",
            )

            return False

        save_hotkey(qt)

        if not set_shortcut_binding(qt):

            QMessageBox.warning(
                self,
                "Preferencias",
                "No se pudo registrar el atajo "
                "del sistema; la tecla seguirá "
                "funcionando dentro de la "
                "pantalla de dibujo.",
            )

        if (
            self._directory
            and self._directory
            != self._initial_directory
        ):

            capture_settings().setValue(
                "screenshots_directory",
                self._directory,
            )

            capture_settings().sync()

            self.settings_changed.emit()

        return True

    def accept(self):

        if self.apply():

            super().accept()
