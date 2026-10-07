#!/usr/bin/env bash
set -euo pipefail

PACKAGE_NAME="barra-interactiva"
VERSION="${VERSION:-1.0.4}"
ARCH="${ARCH:-amd64}"

rm -rf package *.deb

mkdir -p package/DEBIAN
mkdir -p package/opt/barra-interactiva
mkdir -p package/usr/bin
mkdir -p package/usr/share/applications
mkdir -p package/usr/share/icons/hicolor/512x512/apps

cp -a app.py package/opt/barra-interactiva/
cp -a app package/opt/barra-interactiva/
cp -a assets package/opt/barra-interactiva/

install -Dm644 assets/icons/Icono.png \
  package/usr/share/icons/hicolor/512x512/apps/barra-interactiva.png

cat > package/usr/bin/barra-interactiva <<'EOF'
#!/usr/bin/env bash
cd /opt/barra-interactiva
exec /usr/bin/python3 /opt/barra-interactiva/app.py "$@"
EOF

cat > package/DEBIAN/control <<EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: AndriuGJ
Depends: python3, python3-pyside6.qtwidgets, python3-qtawesome, qt6-qpa-plugins
Description: Barra flotante de anotacion para Linux
 Permite dibujar, escribir texto, crear figuras, tomar capturas
 anotadas y realizar anotaciones sobre la pantalla.
EOF

cat > package/usr/share/applications/barra-interactiva.desktop <<EOF
[Desktop Entry]
Name=Barra Interactiva
Comment=Dibuja y realiza anotaciones sobre tu pantalla
Exec=/usr/bin/barra-interactiva
Icon=barra-interactiva
Terminal=false
Type=Application
Categories=Utility;Education;
StartupNotify=false
EOF

chmod 755 package/DEBIAN
chmod 644 package/DEBIAN/control
chmod 755 package/usr/bin/barra-interactiva
chmod 644 package/usr/share/applications/barra-interactiva.desktop
chmod 644 package/usr/share/icons/hicolor/512x512/apps/barra-interactiva.png

dpkg-deb --build --root-owner-group \
  package "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

echo "Paquete creado: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
