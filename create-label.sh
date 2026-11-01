#!/usr/bin/env sh

# shell wrapper to create/activate venv environment and run create-label script

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
. "$VENV_DIR/bin/activate"

pip install -r "$SCRIPT_DIR/requirements.txt" >/dev/null

exec python "$SCRIPT_DIR/create-label.py" "$@"
