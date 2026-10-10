"""Atajo global de GNOME para la aplicación.

Mientras la app está abierta registra una tecla (por
defecto F, configurable en Preferencias: 1 tecla o una
combinación con Ctrl/Alt/Shift/Super) como atajo del
sistema (media-keys de GNOME). Al activarse, el atajo
ejecuta un comando que avisa a la aplicación por un
socket local, y la app alterna entre la pantalla de
dibujo y el modo "usar el equipo normal". Al salir se
retira el atajo.

El socket también se sirve en el mismo proceso para que el
sistema no dependa de la ruta de instalación.
"""

import os
import re
import shutil
import socket
import subprocess
import sys

from PySide6.QtCore import (
    QObject,
    QSettings,
    QSocketNotifier,
    Signal,
)

SCHEMA_LIST = (
    "org.gnome.settings-daemon.plugins.media-keys"
)

SCHEMA_CUSTOM = (
    "org.gnome.settings-daemon.plugins.media-keys"
    ".custom-keybinding"
)

LIST_KEY = "custom-keybindings"

SHORTCUT_ID = "barra_interactiva"

REL_PATH = (
    "/org/gnome/settings-daemon/plugins/media-keys/"
    "custom-keybindings/barra_interactiva/"
)

FULL_SCHEMA = f"{SCHEMA_CUSTOM}:{REL_PATH}"

HOTKEY_DEFAULT = "F"

HOTKEY_ORGANIZATION = "BarraInteractiva"

HOTKEY_APPLICATION = "BarraInteractiva"

IS_LINUX = sys.platform.startswith("linux")

HAS_UNIX_SOCKET = (
    hasattr(socket, "AF_UNIX")
)

_GTK_MODIFIERS = {
    "ctrl": "<Control>",
    "control": "<Control>",
    "alt": "<Alt>",
    "shift": "<Shift>",
    "meta": "<Super>",
    "super": "<Super>",
}

_QT_MODIFIERS = {
    "control": "Ctrl",
    "ctrl": "Ctrl",
    "alt": "Alt",
    "shift": "Shift",
    "meta": "Super",
    "super": "Super",
}

_GTK_KEYS = {
    "space": "space",
    "esc": "escape",
    "escape": "escape",
    "return": "return",
    "enter": "kp_enter",
    "tab": "tab",
    "backspace": "backspace",
    "delete": "delete",
    "insert": "insert",
    "home": "home",
    "end": "end",
    "pageup": "page_up",
    "pagedown": "page_down",
    "left": "left",
    "right": "right",
    "up": "up",
    "down": "down",
}

_QT_KEYS = {
    value: key
    for key, value in (
        ("Space", "space"),
        ("Esc", "escape"),
        ("Return", "return"),
        ("Enter", "kp_enter"),
        ("Tab", "tab"),
        ("Backspace", "backspace"),
        ("Delete", "delete"),
        ("Insert", "insert"),
        ("Home", "home"),
        ("End", "end"),
        ("PageUp", "page_up"),
        ("PageDown", "page_down"),
        ("Left", "left"),
        ("Right", "right"),
        ("Up", "up"),
        ("Down", "down"),
    )
}


def hotkey_settings():

    return QSettings(
        HOTKEY_ORGANIZATION,
        HOTKEY_APPLICATION,
    )


def saved_hotkey():

    """Tecla del atajo en formato Qt (ej.: "F",
    "Ctrl+Alt+F")."""

    value = hotkey_settings().value(
        "hotkey",
        HOTKEY_DEFAULT,
    )

    return str(value) or HOTKEY_DEFAULT


def save_hotkey(qt_sequence):

    hotkey_settings().setValue(
        "hotkey",
        qt_sequence
    )

    hotkey_settings().sync()


def hotkey_is_plain_letter(qt_sequence):

    return (
        len(qt_sequence) == 1
        and qt_sequence.isalpha()
    )


def _gtk_key(key):

    if len(key) == 1:

        return key.lower() if key.isalpha() else key

    if key.lower() in _GTK_KEYS:

        return _GTK_KEYS[key.lower()]

    if re.fullmatch(r"[Ff]\d{1,2}", key):

        return "F" + key[1:]

    return None


def qt_to_gtk(qt_sequence):

    """"Ctrl+Alt+F" -> "<Control><Alt>f".

    Devuelve None si la tecla no es compatible
    (más de una tecla final o tecla desconocida)."""

    parts = [
        part
        for part in (qt_sequence or "").split("+")
        if part
    ]

    if not parts:

        return None

    modifiers = []

    key = None

    for part in parts:

        lowered = part.lower()

        if lowered in _GTK_MODIFIERS:

            modifiers.append(_GTK_MODIFIERS[lowered])

        elif key is None:

            key = part

        else:

            return None

    if key is None:

        return None

    gtk_key = _gtk_key(key)

    if gtk_key is None:

        return None

    return "".join(modifiers) + gtk_key


def gtk_to_qt(gtk_binding):

    """"<Control><Alt>f" -> "Ctrl+Alt+F"."""

    modifiers = re.findall(
        r"<([^>]+)>",
        gtk_binding or "",
    )

    key = re.sub(
        r"<[^>]+>",
        "",
        gtk_binding or "",
    ).strip()

    parts = []

    for modifier in modifiers:

        lowered = modifier.lower()

        if lowered not in _QT_MODIFIERS:

            return None

        parts.append(_QT_MODIFIERS[lowered])

    if not key:

        return None

    if len(key) == 1:

        parts.append(key.upper() if key.isalpha() else key)

    elif key.lower() in _QT_KEYS:

        parts.append(_QT_KEYS[key.lower()])

    elif re.fullmatch(r"[Ff]\d{1,2}", key):

        parts.append("F" + key[1:])

    else:

        return None

    return "+".join(parts)


def set_shortcut_binding(qt_sequence):

    """Aplica la tecla al atajo de GNOME en caliente."""

    if not IS_LINUX:
        return False

    if not shutil.which("gsettings"):

        return False

    gtk = qt_to_gtk(qt_sequence)

    if gtk is None:

        return False

    try:

        _gsettings(
            [
                "set",
                FULL_SCHEMA,
                "binding",
                gtk,
            ]
        )

        return True

    except (
        RuntimeError,
        OSError,
        subprocess.SubprocessError,
    ):

        return False


def socket_path():

    base = (
        os.environ.get("XDG_RUNTIME_DIR")
        or os.path.join(
            os.path.expanduser("~"),
            ".cache",
        )
    )

    return os.path.join(
        base,
        "barra_interactiva.sock",
    )


def hotkey_script_path():

    return socket_path().replace(
        ".sock",
        "_hotkey.py",
    )


def write_hotkey_script(socket_file):

    """Genera el tiny script que ejecuta el atajo.

    Si la app no responde (crash, cierre forzado), el
    script retira F solo para no dejar la tecla
    bloqueada en el sistema."""

    path = hotkey_script_path()

    content = f'''import socket
import subprocess

SOCKET = {socket_file!r}
SCHEMA = (
    "org.gnome.settings-daemon.plugins.media-keys"
    ".custom-keybinding:"
    "{REL_PATH}"
)

try:
    client = socket.socket(socket.AF_UNIX)
    client.connect(SOCKET)
    client.sendall(b"t")
    client.close()
except Exception:
    subprocess.run(
        ["gsettings", "set", SCHEMA, "binding", "''"],
        capture_output=True,
    )
'''

    try:

        with open(path, "w", encoding="utf-8") as file:

            file.write(content)

        os.chmod(path, 0o700)

        return path

    except OSError:

        return None


def _gsettings(args, text=False):

    result = subprocess.run(
        ["gsettings", *args],
        capture_output=True,
        text=text,
        timeout=3,
    )

    if result.returncode != 0:

        raise RuntimeError(
            f"gsettings falló: {args}: "
            f"{result.stderr}"
        )

    return result


def _parse_list(raw):

    return re.findall(r"'([^']*)'", raw or "")


def _format_list(entries):

    if not entries:

        return "[]"

    return (
        "["
        + ", ".join(f"'{entry}'" for entry in entries)
        + "]"
    )


def register_shortcut(socket_file):

    """Registra la tecla guardada como atajo global y
    devuelve True si se instaló. Preserva los atajos
    existentes."""

    if not IS_LINUX or not HAS_UNIX_SOCKET:
        return False

    if not shutil.which("gsettings"):

        return False

    try:

        script = write_hotkey_script(socket_file)

        if script is None:

            return False

        # python del sistema (sin espacios en la ruta);
        # el del venv puede vivir en carpetas con
        # espacios que gsd-media-keys parsea mal.
        python = "/usr/bin/python3"

        if not os.path.exists(python):

            python = (
                shutil.which("python3") or "python3"
            )

        command = f"{python} {script}"

        result = _gsettings(
            ["get", SCHEMA_LIST, LIST_KEY],
            text=True,
        )

        entries = _parse_list(result.stdout)

        if REL_PATH not in entries:

            entries.append(REL_PATH)

            _gsettings(
                [
                    "set",
                    SCHEMA_LIST,
                    LIST_KEY,
                    _format_list(entries),
                ]
            )

        _gsettings(
            [
                "set",
                FULL_SCHEMA,
                "name",
                "Barra Interactiva",
            ]
        )

        _gsettings(
            [
                "set",
                FULL_SCHEMA,
                "command",
                command,
            ]
        )

        _gsettings(
            [
                "set",
                FULL_SCHEMA,
                "binding",
                qt_to_gtk(saved_hotkey())
                or HOTKEY_DEFAULT,
            ]
        )

        return True

    except (
        RuntimeError,
        OSError,
        subprocess.SubprocessError,
    ):

        return False


def unregister_shortcut():

    """Retira el atajo dejando los demás como estaban."""

    if not IS_LINUX:
        return

    try:

        os.unlink(hotkey_script_path())

    except OSError:

        pass

    if not shutil.which("gsettings"):

        return

    try:

        result = _gsettings(
            ["get", SCHEMA_LIST, LIST_KEY],
            text=True,
        )

        entries = _parse_list(result.stdout)

        if REL_PATH not in entries:

            return

        entries.remove(REL_PATH)

        _gsettings(
            [
                "set",
                SCHEMA_LIST,
                LIST_KEY,
                _format_list(entries),
            ]
        )

    except (
        RuntimeError,
        OSError,
        subprocess.SubprocessError,
    ):

        pass


class HotkeyService(QObject):

    """Socket local + atajo global de GNOME (F)."""

    toggle_requested = Signal()

    def __init__(self, path=None):

        super().__init__()

        self._path = path or socket_path()

        self._server = None

        self._notifier = None

        self._registered = False

    def start(self, register=True):

        # AF_UNIX no está disponible en algunas instalaciones
        # de Python/Windows. El atajo global implementado aquí
        # es específico de GNOME/Linux, así que en Windows no
        # se crea socket ni se intenta registrar gsettings.
        if not IS_LINUX or not HAS_UNIX_SOCKET:
            return

        path = self._path

        try:

            directory = os.path.dirname(path)

            if os.path.isdir(directory):

                if os.path.exists(path):

                    os.unlink(path)

                self._server = socket.socket(
                    socket.AF_UNIX,
                    socket.SOCK_STREAM,
                )

                self._server.bind(path)

                self._server.listen(4)

                os.chmod(path, 0o600)

                self._notifier = QSocketNotifier(
                    self._server.fileno(),
                    QSocketNotifier.Type.Read,
                    self,
                )

                self._notifier.activated.connect(
                    self._on_ready
                )

        except OSError:

            self._server = None

        if register:

            self._registered = register_shortcut(
                self._path
            )

    def _on_ready(self):

        try:

            connection, _ = self._server.accept()

            data = connection.recv(16)

            connection.close()

        except OSError:

            return

        if data[:1] == b"t":

            self.toggle_requested.emit()

    def stop(self):

        if self._notifier is not None:

            self._notifier.setEnabled(False)

            self._notifier.deleteLater()

            self._notifier = None

        if self._server is not None:

            try:

                self._server.close()

            except OSError:

                pass

            self._server = None

            try:

                os.unlink(self._path)

            except OSError:

                pass

        if self._registered:

            unregister_shortcut()

            self._registered = False
