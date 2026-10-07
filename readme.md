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

- Al iniciar, la barra aparece pegada al **borde derecho** y centrada.
- **Mover la barra**: arrastra el tirador de puntos de arriba.
- **Minimizar**: botón `—` (la barra se pliega en una píldora arrastrable;
  el botón con recuadro la restaura).
- **Dibujar**: pulsa una herramienta y se abre la pantalla de dibujo.
- **Captura**: el botón de cámara guarda la pantalla con los dibujos y textos y la copia al portapapeles.
- **Volver**: botón `Interactuar` de la barra de dibujo.

## Atajos (en la pantalla de dibujo)

| Tecla | Acción |
| --- | --- |
| `Ctrl+Z` | Deshacer |
| `Escape` | Deseleccionar / cerrar editor de texto |
| `Supr` / `Retroceso` | Borrar el objeto seleccionado |
| `Ctrl+C` (terminal) | Salir de la aplicación |

## Estructura

```
app.py              Punto de entrada
app/config.py       Colores y grosores por defecto
app/icons.py        Iconos (qtawesome) e icono de la app
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
sudo apt install ./barra-interactiva_1.0.4_amd64.deb
```

La versión 1.0.4 usa las bibliotecas Qt/PySide6 del propio Ubuntu en lugar de
empaquetar una copia completa de Qt. Esto reduce mucho el tamaño del instalador
y evita incompatibilidades entre las bibliotecas gráficas empaquetadas y el
sistema.

## Actualizar desde una versión anterior

No es necesario desinstalar primero. APT reemplaza la versión anterior:

```bash
sudo apt install ./barra-interactiva_1.0.4_amd64.deb
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
1.0.4 ya no usa ni necesita esa aplicación. Si quedó instalada y no la usas,
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
3. La imagen se guarda en `Imágenes/Capturas de pantalla` (o la carpeta de
   capturas ya existente).
4. La misma imagen se copia al portapapeles para poder pegarla con `Ctrl+V`.

En Ubuntu la aplicación usa XWayland/X11 cuando está disponible. Esto permite
posicionar la barra en el borde derecho y hacer la captura desde Qt sin instalar
una aplicación de capturas adicional.
