#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$DIR/venv/bin/python"

if [ ! -x "$PY" ]; then
    echo "[error] No se encuentra el entorno virtual en: $DIR/venv"
    echo "Créalo con:"
    echo "    python3 -m venv venv"
    echo "    venv/bin/pip install -r requirements.txt"
    exit 1
fi

exec "$PY" "$DIR/main.py" "$@"
