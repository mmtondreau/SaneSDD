#!/usr/bin/env bash
# Install sdd-util Python CLI dependencies.
# Run this once after installing the SDD plugin.
set -euo pipefail

# Navigate from plugins/sdd/scripts/ up to the repo root where pyproject.toml lives.
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

cd "$REPO_ROOT"

if command -v poetry &>/dev/null; then
    poetry install --no-interaction --quiet
    echo "sdd-util installed via poetry."
elif command -v pip &>/dev/null; then
    pip install -e "$PLUGIN_ROOT" --quiet
    echo "sdd-util installed via pip."
else
    echo "ERROR: Neither poetry nor pip found. Install Python 3.10+ and poetry first." >&2
    exit 1
fi
