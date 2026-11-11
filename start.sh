#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)" || exit 1
export NUMBA_CACHE_DIR="${NUMBA_CACHE_DIR:-${TMPDIR:-/tmp}/beat-grid-numba}"
if [ -n "${BEAT_GRID_PYTHON:-}" ]; then
    PYTHON="$BEAT_GRID_PYTHON"
elif [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
elif [ -x "$HOME/apps/ComfyUI/venv/bin/python" ]; then
    PYTHON="$HOME/apps/ComfyUI/venv/bin/python"
else
    PYTHON=python3
fi
exec "$PYTHON" "$SCRIPT_DIR/beat_grid.py" "$@"
