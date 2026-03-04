#!/usr/bin/env bash
# Install ssdd-util Python CLI dependencies into a local venv.
# Run this once after installing the SaneSDD plugin.
set -euo pipefail

# PLUGIN_ROOT is one level up from scripts/
PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PLUGIN_ROOT/.venv"

echo "Setting up ssdd-util in $VENV_DIR ..." >&2

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --quiet click "pyyaml>=6.0" "python-frontmatter>=1.1"

echo "ssdd-util dependencies installed successfully." >&2
