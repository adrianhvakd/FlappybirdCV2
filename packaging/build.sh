#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

APP="FlappyBirdVision"
VENV=".build-venv"
MAKE_APPIMAGE=0
[ "${1:-}" = "--appimage" ] && MAKE_APPIMAGE=1

echo "==> 1/4 Creando entorno de compilación ($VENV)"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip -q
"$VENV/bin/pip" install -q -r requirements.txt pyinstaller

echo "==> 2/4 Compilando con PyInstaller"
"$VENV/bin/pyinstaller" --clean --noconfirm packaging/flappybird.spec

echo "==> 3/4 Empaquetando dist/$APP"
VERSION="$(date +%Y.%m.%d)"
ARCH="$(uname -m)"
TARBALL="dist/${APP}-linux-${ARCH}-${VERSION}.tar.gz"
tar -C dist -czf "$TARBALL" "$APP"
echo "    -> $TARBALL"

cat > "dist/$APP.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Flappy Bird Visión
Comment=Flappy Bird controlado con gestos de la mano
Exec=$APP/$APP
Icon=$APP
Terminal=false
Categories=Game;ArcadeGame;
EOF

echo "==> 4/4 Listo"

if [ "$MAKE_APPIMAGE" -eq 1 ]; then
    echo "    Intentando crear AppImage..."
    TOOL="dist/appimagetool-${ARCH}.AppImage"
    if [ ! -x "$TOOL" ]; then
        URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage"
        curl -sL -o "$TOOL" "$URL" && chmod +x "$TOOL" || {
            echo "    [!] No se pudo descargar appimagetool; se omite el AppImage."
            TOOL=""
        }
    fi
    if [ -n "${TOOL:-}" ] && [ -x "$TOOL" ]; then
        APPDIR="dist/${APP}.AppDir"
        rm -rf "$APPDIR"
        cp -r "dist/$APP" "$APPDIR"
        cp "dist/$APP.desktop" "$APPDIR/$APP.desktop"
        [ -f assets/icon.png ] && cp assets/icon.png "$APPDIR/$APP.png"
        ARCH="$ARCH" "$TOOL" "$APPDIR" "dist/${APP}-${ARCH}.AppImage" 2>/dev/null \
            && echo "    -> dist/${APP}-${ARCH}.AppImage" \
            || echo "    [!] appimagetool falló; revisa la salida."
    fi
fi

echo
echo "Hecho. Copia dist/$APP/ a donde quieras y ejecuta ./$APP/$APP"
