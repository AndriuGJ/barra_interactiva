# Barra Interactiva

Barra flotante + overlay de dibujo hecho con **PySide6**. Permite dibujar
encima de la pantalla (lápiz, rectángulos, círculos, flechas, texto),
cambiar colores y grosores, seleccionar y mover lo dibujado con la mano,
deshacer, limpiar y volver a la barra.

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
