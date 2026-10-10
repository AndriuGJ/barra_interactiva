# Barra Interactiva

Barra flotante + overlay de dibujo hecho con **PySide6**. Permite dibujar
encima de la pantalla (lápiz, rectángulos, círculos, flechas, texto),
cambiar colores y grosores, seleccionar y mover lo dibujado con la mano,
deshacer, limpiar, tomar capturas con las anotaciones y volver a la barra.

## Requisitos

- Python 3.10 o superior (probado con Python 3.14)
- Dependencias de `requirements.txt`:
  - `PySide6==6.11.2`
  - `qtawesome==1.4.2` (iconos Font Awesome)

## Inicializar el repositorio

```bash
git clone git@github.com:AndriuGJ/barra_interactiva.git
cd barra_interactiva

# 1. entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. dependencias
pip install -r requirements.txt
```

## Ejecutar

```bash
python app.py
```

- Al iniciar, la app abre **directamente la pantalla de dibujo** con la barra
  completa de opciones (la barra inicial ya no existe).
- **Mover la barra**: arrastra el tirador de puntos de la fila superior.
- **Minimizar / Cerrar**: en la misma fila superior están el botón `—`
  (la barra se pliega en una píldora arrastrable con `□` para restaurar)
  y la `X` para cerrar la aplicación.
- **Relleno**: el botón de gota (junto a los grosores) rellena los rectángulos
  y círculos que se dibujen a continuación; vuelve a pulsarlo para dibujar
  solo el contorno.
- **Zoom de pantalla**: el botón de la lupa (junto al relleno) enciende la
  lupa del escritorio: se amplía la **pantalla entera** en pasos definidos
  (110%, 120% ... hasta 200%, solo acerca). Con la lupa activa, el **clic
  izquierdo sube un nivel** (mantén pulsado y sigue subiendo) y el **clic
  derecho cancela** (vuelve al 100%). Requiere GNOME (lupa de accesibilidad).
- **Tecla del atajo (modo normal)**: al pulsar la tecla del atajo (por defecto
  `F`) la pantalla de dibujo se oculta del todo y puedes usar el equipo
  normal; al volver a pulsarla reaparece como estaba. Mientras la app está
  abierta, la tecla queda registrada como atajo global de GNOME (funciona
  desde cualquier programa) y la app lo retira al salir. **La tecla se
  cambia en Preferencias**: una sola tecla (`F`, `F5`) o una combinación de
  2 con `Ctrl`, `Alt`, `Shift` o `Super` (ej.: `Ctrl+Alt+F`); aplica al
  instante y también se recuerda para la próxima vez. Nota: al ser global,
  GNOME intercepta esa tecla en todas partes mientras la app corre.
- **Captura**: el botón de cámara guarda la pantalla con los dibujos y textos y la copia al portapapeles (una sola imagen, en la carpeta elegida).
- **Preferencias**: el botón de engranaje (debajo de la cámara) abre el
  diálogo de preferencias: la tecla del atajo y la carpeta donde se guardan
  las capturas (se recuerdan para la próxima vez).
- **Cerrar**: la `X` de la fila superior termina con la aplicación; para volver
  a dibujar se abre de nuevo.

## Atajos (en la pantalla de dibujo)

| Tecla | Acción |
| --- | --- |
| `F` (configurable en Preferencias) | Alternar modo normal (usar el equipo) <-> pantalla de dibujo |
| `Ctrl+Z` | Deshacer |
| `Escape` | Deseleccionar / cerrar editor de texto |
| `Supr` / `Retroceso` | Borrar el objeto seleccionado |
| `Ctrl+C` (terminal) | Salir de la aplicación |

## Estructura

```
app.py              Punto de entrada
app/config.py       Colores y grosores por defecto
app/icons.py        Iconos (qtawesome) e icono de la app
app/hotkey.py       Atajo global de GNOME + socket (tecla configurable)
app/preferences.py  Diálogo de preferencias (tecla del atajo y carpeta)
app/floating/       Barra flotante (window.py, panel.py)
app/overlay/        Pantalla de dibujo (window.py, panel.py, canvas.py, objects.py)
assets/icons/       Icono de la aplicación
```

## Trabajar con git

```bash
git add -A
git commit -m "Descripción del cambio"
git push
```


## Instalar el paquete .deb

Descarga la versión actual y ejecuta:

```bash
sudo apt install ./barra-interactiva_1.0.5_amd64.deb
```

La versión 1.0.5 usa las bibliotecas Qt/PySide6 del propio Ubuntu en lugar de
empaquetar una copia completa de Qt. Esto reduce mucho el tamaño del instalador
y evita incompatibilidades entre las bibliotecas gráficas empaquetadas y el
sistema.

## Actualizar desde una versión anterior

No es necesario desinstalar primero. APT reemplaza la versión anterior:

```bash
sudo apt install ./barra-interactiva_1.0.5_amd64.deb
```

Para comprobar la versión instalada:

```bash
apt list --installed 2>/dev/null | grep barra-interactiva
```

## Eliminar versiones anteriores

Para eliminar Barra Interactiva completamente:

```bash
sudo apt remove --purge barra-interactiva
sudo apt autoremove --purge
```

La versión 1.0.3 instalaba `gnome-screenshot` como dependencia. La versión
1.0.5 ya no usa ni necesita esa aplicación. Si quedó instalada y no la usas,
puedes quitarla con:

```bash
sudo apt remove --purge gnome-screenshot
sudo apt autoremove --purge
```

Después puedes instalar nuevamente Barra Interactiva con el comando de la
sección anterior.

## Capturas de pantalla

Al pulsar el botón de cámara:

1. La barra se oculta temporalmente.
2. Se captura la pantalla con los dibujos, formas y textos.
3. La imagen se guarda en la carpeta elegida con el botón de engranaje
   (por defecto `Imágenes/Capturas de pantalla`) y esa elección se recuerda.
4. La misma imagen se copia al portapapeles para poder pegarla con `Ctrl+V`.
5. El portal del escritorio crea por su cuenta una copia en `Imágenes`
   (`Screenshot.png`); la app la mueve a la carpeta elegida, así que
   **solo queda una imagen** y no se acumulan duplicados.

En Ubuntu la barra continúa usando XWayland/X11 cuando está disponible para
mantener su posición en el borde derecho. Para la captura se usa primero el
portal oficial del escritorio (XDG Desktop Portal), porque Wayland bloquea que
una aplicación X11 lea directamente el contenido de las ventanas Wayland. Esto
evita las capturas negras y no instala ninguna aplicación de capturas adicional.

Dependiendo de la política de seguridad de GNOME, el sistema puede mostrar una
confirmación de captura. Ese diálogo pertenece a Wayland/GNOME y no se puede
eliminar de forma segura desde la aplicación.

**Falta corrgir la desaparicion del puntero en hacer Zoom**



