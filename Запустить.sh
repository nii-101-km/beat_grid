#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)" || exit 1
exec "$SCRIPT_DIR/start.sh" "$@"
