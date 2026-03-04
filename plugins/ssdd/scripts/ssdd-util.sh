#!/usr/bin/env bash
# Wrapper to run ssdd-util using the plugin's local venv.
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PLUGIN_ROOT/.venv"

# Auto-install if venv is missing
if [ ! -d "$VENV_DIR" ]; then
    echo "ssdd-util dependencies not installed. Running setup..." >&2
    "$PLUGIN_ROOT/scripts/setup.sh"
fi

export PYTHONPATH="${PLUGIN_ROOT}/src:${PYTHONPATH:-}"
exec "$VENV_DIR/bin/python3" -m ssdd "$@"
