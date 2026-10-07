#!/usr/bin/env bash
set -euo pipefail

APP_NAME="BarraInteractiva"
PACKAGE_NAME="barra-interactiva"
VERSION="${VERSION:-1.0.3}"
ARCH="${ARCH:-amd64}"

rm -rf build dist package *.deb

python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --onedir \
  --name "${APP_NAME}" \
  --add-data "assets:assets" \
  app.py

mkdir -p package/DEBIAN
mkdir -p package/opt/barra-interactiva
mkdir -p package/usr/share/applications
mkdir -p package/usr/share/icons/hicolor/512x512/apps

cp -a "dist/${APP_NAME}/." package/opt/barra-interactiva/
install -Dm644 assets/icons/Icono.png \
  package/usr/share/icons/hicolor/512x512/apps/barra-interactiva.png

cat > package/DEBIAN/control <<EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: AndriuGJ
Depends: gnome-screenshot, libgl1, libglib2.0-bin, libxkbcommon0, libwayland-client0, libxcb-cursor0, libxkbcommon-x11-0
Description: Barra flotante de anotacion para Linux
 Permite dibujar, escribir texto, crear figuras y realizar
 anotaciones sobre la pantalla durante exposiciones o clases.
EOF

cat > package/usr/share/applications/barra-interactiva.desktop <<EOF
[Desktop Entry]
Name=Barra Interactiva
Comment=Dibuja y realiza anotaciones sobre tu pantalla
Exec=/opt/barra-interactiva/BarraInteractiva
Icon=barra-interactiva
Terminal=false
Type=Application
Categories=Utility;Education;
StartupNotify=false
EOF

chmod 755 package/DEBIAN
chmod 644 package/DEBIAN/control
chmod 755 package/opt/barra-interactiva/BarraInteractiva
chmod 644 package/usr/share/applications/barra-interactiva.desktop
chmod 644 package/usr/share/icons/hicolor/512x512/apps/barra-interactiva.png

dpkg-deb --build --root-owner-group \
  package "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

echo "Paquete creado: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
